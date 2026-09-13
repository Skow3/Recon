from typing import List, Dict, Any
from ..schemas.responses import ReconciliationResult

class EvidenceReconciler:
    """Reconciles normalized evidence across Gmail, Stripe, and Slack."""

    def reconcile(
        self,
        gmail_items: List[Dict[str, Any]],
        stripe_charges: List[Dict[str, Any]],
        stripe_refunds: List[Dict[str, Any]],
        slack_messages: List[Dict[str, Any]]
    ) -> ReconciliationResult:
        contradictions = []
        supporting_evidence = []
        refuting_evidence = []
        risk_flags = []

        # 1. Analyze Gmail claims
        gmail_claim = ""
        reported_duplicate = False
        reported_amount_499 = False
        if gmail_items:
            first_mail = gmail_items[0]
            gmail_claim = first_mail.get("body", "")
            claims = first_mail.get("relevant_claims", [])
            for c in claims:
                supporting_evidence.append(f"Gmail: {c}")
                if "duplicate" in c.lower() or "twice" in c.lower():
                    reported_duplicate = True
                if "$499" in c:
                    reported_amount_499 = True
        else:
            risk_flags.append("No customer email evidence found in Gmail.")

        # 2. Analyze Stripe charges
        charges_found = len(stripe_charges)
        charge_comp = []
        succeeded_charges = [c for c in stripe_charges if c.get("status") == "succeeded"]
        total_billed = sum(c.get("amount", 0) for c in succeeded_charges)

        for idx, ch in enumerate(stripe_charges, 1):
            charge_comp.append({
                "charge_index": idx,
                "charge_id": ch.get("id"),
                "amount": f"${ch.get('amount', 0) / 100:.2f}",
                "currency": ch.get("currency", "usd").upper(),
                "status": ch.get("status"),
                "refunded": ch.get("refunded", False),
                "amount_refunded": f"${ch.get('amount_refunded', 0) / 100:.2f}",
                "description": ch.get("description", "")
            })

        if charges_found >= 2:
            supporting_evidence.append(f"Stripe: Found {charges_found} charges (Total: ${total_billed / 100:.2f})")
        elif charges_found == 1:
            contradictions.append(
                "Stripe record conflict: Customer claims charged twice, but Stripe records contain only ONE charge."
            )
            refuting_evidence.append("Stripe: Only 1 charge exists, cannot substantiate double billing.")
        elif charges_found == 0:
            risk_flags.append("Stripe: No charges located for customer.")

        # Check existing refunds (correlate with customer's charges)
        customer_charge_ids = {c.get("id") for c in stripe_charges if c.get("id")}
        relevant_refunds = [
            ref for ref in stripe_refunds
            if not customer_charge_ids or ref.get("charge_id") in customer_charge_ids
        ]
        has_prior_refund = False
        for ref in relevant_refunds:
            if ref.get("status") == "succeeded":
                has_prior_refund = True
                refuting_evidence.append(
                    f"Stripe: Prior refund {ref.get('id')} already exists for ${ref.get('amount', 0) / 100:.2f}."
                )
                contradictions.append(
                    f"Already refunded: Stripe already has refund {ref.get('id')} for this charge."
                )

        # Also verify if any charge object itself is marked as refunded
        for ch in stripe_charges:
            if ch.get("refunded") or ch.get("amount_refunded", 0) > 0:
                if not has_prior_refund:
                    has_prior_refund = True
                    contradictions.append(
                        f"Already refunded: Stripe charge {ch.get('id')} is marked refunded (${ch.get('amount_refunded', 0) / 100:.2f})."
                    )

        # 3. Analyze Slack Context
        slack_context_parts = []
        internal_confirms_duplicate = False
        internal_claims_legitimate = False

        for sm in slack_messages:
            text = sm.get("text", "")
            author = sm.get("author", "team")
            slack_context_parts.append(f"{author}: {text}")
            lower_text = text.lower()

            if "only have one" in lower_text or "accidental" in lower_text or "please refund" in lower_text:
                internal_confirms_duplicate = True
                supporting_evidence.append(f"Slack ({author}): Confirmed single charge expected ({text[:80]}...)")
            if "legitimate" in lower_text or "implementation fee" in lower_text or "do not refund" in lower_text or "add-on" in lower_text:
                internal_claims_legitimate = True
                refuting_evidence.append(f"Slack ({author}): Clarified second charge was legitimate ({text[:80]}...)")

        # Detect internal contradiction within Slack
        if internal_confirms_duplicate and internal_claims_legitimate:
            contradictions.append(
                "Internal team disagreement: Slack messages contain conflicting assertions regarding whether the second charge was authorized."
            )
            risk_flags.append("High risk: Internal stakeholders disagree on charge legitimacy.")

        # Detect contradiction between customer claim and internal context
        if reported_duplicate and internal_claims_legitimate and not internal_confirms_duplicate:
            contradictions.append(
                "Legitimate charge conflict: Customer claims accidental duplicate, but internal Slack context documents second charge as legitimate implementation services."
            )

        # Build risk flags
        if len(contradictions) > 0:
            risk_flags.append(f"{len(contradictions)} evidence contradiction(s) detected.")
        if charges_found < 2 and reported_duplicate:
            risk_flags.append("Customer claim unsubstantiated by financial ledger.")

        slack_context_summary = " | ".join(slack_context_parts) if slack_context_parts else "No relevant internal Slack discussion found."

        return ReconciliationResult(
            customer_match=True,
            charges_found=charges_found,
            charge_comparison=charge_comp,
            gmail_claim=gmail_claim[:300],
            slack_context=slack_context_summary[:300],
            contradictions=contradictions,
            supporting_evidence=supporting_evidence,
            refuting_evidence=refuting_evidence,
            risk_flags=risk_flags
        )

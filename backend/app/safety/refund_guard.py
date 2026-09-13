from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from ..config import settings
from ..models.case import CaseModel, ApprovalModel
from ..models.evidence import DecisionModel, EvidenceModel
from ..tools.interfaces import StripeClient
from .idempotency import check_refund_idempotency

def validate_refund(
    case: CaseModel,
    decision: Optional[DecisionModel],
    approval: Optional[ApprovalModel],
    stripe_client: StripeClient,
    db: Session,
    target_charge_id: Optional[str] = None,
    target_amount: Optional[int] = None
) -> Dict[str, Any]:
    """
    Independent deterministic safety validation engine.
    The LLM cannot override any of these checks.
    """
    checks = {
        "stripe_test_mode": False,
        "valid_customer": False,
        "valid_charge": False,
        "charge_succeeded": False,
        "refundable_amount": False,
        "no_duplicate_refund": False,
        "decision_is_refund_recommended": False,
        "human_approval_granted": False,
    }

    # 1. Stripe is in TEST mode
    if not settings.is_stripe_test_mode:
        return {
            "allowed": False,
            "reason": "SAFETY BLOCKED: Stripe is NOT configured in TEST mode! Live financial actions are strictly forbidden.",
            "checks": checks
        }
    checks["stripe_test_mode"] = True

    # 2. Decision is REFUND_RECOMMENDED
    if not decision or decision.decision != "REFUND_RECOMMENDED":
        dec_str = decision.decision if decision else "NONE"
        return {
            "allowed": False,
            "reason": f"SAFETY BLOCKED: Recommendation is '{dec_str}', not 'REFUND_RECOMMENDED'. Financial actions are prohibited.",
            "checks": checks
        }
    checks["decision_is_refund_recommended"] = True

    # 3. Human approval exists and is approved
    if not approval or not approval.approved:
        return {
            "allowed": False,
            "reason": "SAFETY BLOCKED: Explicit human approval has not been granted for this refund.",
            "checks": checks
        }
    if approval.approved_by != "human":
        return {
            "allowed": False,
            "reason": f"SAFETY BLOCKED: Approver must be 'human', but was '{approval.approved_by}'.",
            "checks": checks
        }
    checks["human_approval_granted"] = True

    # 4. Valid Customer check
    if not case.customer_name and not case.customer_email:
        return {
            "allowed": False,
            "reason": "SAFETY BLOCKED: Customer identity could not be verified.",
            "checks": checks
        }
    checks["valid_customer"] = True

    # 5. Find and inspect charge in Stripe
    try:
        charge_to_refund = None

        # Check if target_charge_id was passed or can be found from case evidence
        if not target_charge_id:
            ev_charges = db.query(EvidenceModel).filter(
                EvidenceModel.case_id == case.id,
                EvidenceModel.source == "stripe",
                EvidenceModel.evidence_type == "charge"
            ).all()
            if ev_charges:
                unrefunded = [e.payload for e in ev_charges if isinstance(e.payload, dict) and not e.payload.get("refunded") and e.payload.get("amount_refunded", 0) == 0]
                if len(unrefunded) >= 2:
                    # In duplicate charges, refund the second charge
                    target_charge_id = unrefunded[1].get("id")
                elif len(unrefunded) == 1:
                    target_charge_id = unrefunded[0].get("id")

        # If target_charge_id is known, try get_charge directly first
        if target_charge_id and hasattr(stripe_client, "get_charge"):
            charge_to_refund = stripe_client.get_charge(target_charge_id)

        if not charge_to_refund:
            # Query stripe charges for customer
            cust_id = None
            if case.customer_email:
                cust = stripe_client.find_customer(case.customer_email)
                if cust:
                    cust_id = cust.get("id")
            if not cust_id and case.customer_name:
                cust = stripe_client.find_customer(case.customer_name)
                if cust:
                    cust_id = cust.get("id")

            charges = stripe_client.list_charges(customer_id=cust_id, limit=20)
            if not charges and cust_id:
                charges = stripe_client.list_charges(limit=20)

            if target_charge_id:
                for ch in charges:
                    if ch.get("id") == target_charge_id:
                        charge_to_refund = ch
                        break
            else:
                if len(charges) >= 2:
                    charge_to_refund = charges[1]
                elif len(charges) == 1:
                    charge_to_refund = charges[0]

        if not charge_to_refund:
            return {
                "allowed": False,
                "reason": f"SAFETY BLOCKED: Target charge '{target_charge_id or 'auto'}' could not be located in Stripe.",
                "checks": checks
            }
        checks["valid_charge"] = True

        # 6. Charge must be successful
        if charge_to_refund.get("status") != "succeeded":
            return {
                "allowed": False,
                "reason": f"SAFETY BLOCKED: Charge {charge_to_refund['id']} status is '{charge_to_refund.get('status')}', must be 'succeeded'.",
                "checks": checks
            }
        checks["charge_succeeded"] = True

        # 7. Idempotency & Duplicate Refund check
        amt_to_refund = target_amount or charge_to_refund["amount"]
        idemp_check = check_refund_idempotency(
            case_id=case.id,
            charge_id=charge_to_refund["id"],
            amount=amt_to_refund,
            db=db,
            stripe_client=stripe_client
        )
        if idemp_check.is_duplicate:
            return {
                "allowed": False,
                "reason": idemp_check.reason,
                "checks": checks
            }
        checks["no_duplicate_refund"] = True

        # 8. Refundable amount check
        already_refunded = charge_to_refund.get("amount_refunded", 0)
        remaining_refundable = charge_to_refund["amount"] - already_refunded

        if amt_to_refund <= 0 or amt_to_refund > remaining_refundable:
            return {
                "allowed": False,
                "reason": f"SAFETY BLOCKED: Requested amount ({amt_to_refund} cents) exceeds refundable amount ({remaining_refundable} cents).",
                "checks": checks
            }
        checks["refundable_amount"] = True

    except Exception as e:
        return {
            "allowed": False,
            "reason": f"SAFETY BLOCKED: Stripe verification failed with error: {str(e)}",
            "checks": checks
        }

    return {
        "allowed": True,
        "reason": "All deterministic safety and approval checks passed.",
        "checks": checks,
        "target_charge_id": charge_to_refund["id"],
        "target_amount": amt_to_refund
    }

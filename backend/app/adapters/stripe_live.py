from typing import List, Dict, Any, Optional
import stripe
from ..tools.interfaces import StripeClient
from ..config import settings

class LiveStripeClient(StripeClient):
    """Live Stripe Client communicating with Stripe TEST Mode API."""

    def __init__(self):
        api_key = settings.STRIPE_SECRET_KEY.strip()
        if not api_key.startswith("sk_test_"):
            raise ValueError(
                "CRITICAL SECURITY VIOLATION: Stripe key is not in TEST mode! "
                "Only keys starting with 'sk_test_' are permitted in RECON."
            )
        stripe.api_key = api_key
        self.api_key = api_key

    def find_customer(self, identifier: str) -> Optional[Dict[str, Any]]:
        ident = identifier.strip()
        # Direct email lookup first (instant & reliable without search index delay)
        if "@" in ident:
            try:
                res = stripe.Customer.list(email=ident, limit=5)
                if res.data:
                    cust = res.data[0]
                    return {
                        "id": cust.id,
                        "name": cust.name or ident,
                        "email": cust.email
                    }
            except Exception as e:
                print(f"[StripeLive] Error searching customer by email: {e}")

        # Search by email or name
        try:
            customers = stripe.Customer.search(
                query=f"email:'{ident}' OR name:'{ident}'",
                limit=1
            )
            if customers.data:
                cust = customers.data[0]
                return {
                    "id": cust.id,
                    "name": cust.name or cust.email,
                    "email": cust.email
                }
        except Exception:
            pass

        # Fallback list search
        try:
            customers = stripe.Customer.list(limit=50)
            ident_lower = ident.lower()
            for cust in customers.data:
                cust_email = (cust.email or "").lower()
                cust_name = (cust.name or "").lower()
                if (cust_email and (ident_lower in cust_email or cust_email in ident_lower)) or \
                   (cust_name and (ident_lower in cust_name or cust_name in ident_lower)):
                    return {
                        "id": cust.id,
                        "name": cust.name or cust.email,
                        "email": cust.email
                    }
        except Exception as e:
            print(f"[StripeLive] Error in fallback list search: {e}")
        return None

    def list_charges(self, customer_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        params = {"limit": limit}
        if customer_id:
            params["customer"] = customer_id
        
        charges = stripe.Charge.list(**params)
        normalized = []
        for ch in charges.data:
            normalized.append({
                "source": "stripe",
                "type": "charge",
                "id": ch.id,
                "customer_id": ch.customer,
                "amount": ch.amount,
                "currency": ch.currency,
                "status": ch.status,
                "created": str(ch.created),
                "invoice_id": getattr(ch, "invoice", None),
                "refunded": ch.refunded,
                "amount_refunded": ch.amount_refunded,
                "description": ch.description or ""
            })
        return normalized

    def get_charge(self, charge_id: str) -> Optional[Dict[str, Any]]:
        try:
            ch = stripe.Charge.retrieve(charge_id)
            return {
                "source": "stripe",
                "type": "charge",
                "id": ch.id,
                "customer_id": ch.customer,
                "amount": ch.amount,
                "currency": ch.currency,
                "status": ch.status,
                "created": str(ch.created),
                "invoice_id": getattr(ch, "invoice", None),
                "refunded": ch.refunded,
                "amount_refunded": ch.amount_refunded,
                "description": ch.description or ""
            }
        except Exception as e:
            print(f"[StripeLive] Error retrieving charge {charge_id}: {e}")
            return None

    def get_invoice(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        try:
            inv = stripe.Invoice.retrieve(invoice_id)
            return {
                "id": inv.id,
                "status": inv.status,
                "amount_due": inv.amount_due,
                "amount_paid": inv.amount_paid,
                "currency": inv.currency
            }
        except Exception:
            return None

    def list_refunds(self, charge_id: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {"limit": 20}
        if charge_id:
            params["charge"] = charge_id
        
        refunds = stripe.Refund.list(**params)
        normalized = []
        for r in refunds.data:
            normalized.append({
                "source": "stripe",
                "type": "refund",
                "id": r.id,
                "charge_id": r.charge,
                "amount": r.amount,
                "status": r.status,
                "created": str(r.created)
            })
        return normalized

    def create_refund(
        self,
        charge_id: str,
        amount: Optional[int] = None,
        reason: Optional[str] = None,
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        params = {"charge": charge_id}
        if amount:
            params["amount"] = amount
        if reason:
            params["reason"] = reason

        kwargs = {}
        if idempotency_key:
            kwargs["idempotency_key"] = idempotency_key

        r = stripe.Refund.create(**params, **kwargs)
        return {
            "source": "stripe",
            "type": "refund",
            "id": r.id,
            "charge_id": r.charge,
            "amount": r.amount,
            "status": r.status,
            "created": str(r.created),
            "reason": r.reason
        }

    def get_refund(self, refund_id: str) -> Dict[str, Any]:
        r = stripe.Refund.retrieve(refund_id)
        return {
            "source": "stripe",
            "type": "refund",
            "id": r.id,
            "charge_id": r.charge,
            "amount": r.amount,
            "status": r.status,
            "created": str(r.created),
            "reason": r.reason
        }

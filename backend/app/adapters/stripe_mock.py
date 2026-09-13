import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from ..tools.interfaces import StripeClient

class MockStripeClient(StripeClient):
    """Deterministic Mock Stripe Client simulating Stripe TEST mode behavior."""

    def __init__(self, scenario: Optional[str] = None):
        self.scenario = scenario or "scenario_1_true_duplicate"
        self._init_data()

    def _init_data(self):
        # Customers
        self.customers = {
            "acme": {"id": "cus_acme_001", "name": "Acme Corp", "email": "alex@acmecorp.com"},
            "acme_false": {"id": "cus_acme_002", "name": "Acme Corp", "email": "billing@acmecorp.com"},
            "globex": {"id": "cus_globex_003", "name": "Globex Corp", "email": "accounting@globex.com"},
            "initech": {"id": "cus_initech_004", "name": "Initech LLC", "email": "finance@initech.com"},
            "soylent": {"id": "cus_soylent_005", "name": "Soylent Corp", "email": "admin@soylent.com"},
            "hooli": {"id": "cus_hooli_006", "name": "Hooli", "email": "ops@hooli.com"},
        }

        now = datetime.utcnow()
        t1 = (now - timedelta(days=2)).isoformat() + "Z"
        t2 = (now - timedelta(days=2, minutes=-5)).isoformat() + "Z"

        # Define dataset per scenario
        self.charges: Dict[str, Dict[str, Any]] = {}
        self.refunds: Dict[str, Dict[str, Any]] = {}

        sc = self.scenario.lower()

        if "scenario_2" in sc or "false" in sc:
            self.charges = {
                "ch_false_dup_001": {
                    "source": "stripe", "type": "charge", "id": "ch_false_dup_001",
                    "customer_id": "cus_acme_002", "amount": 49900, "currency": "usd",
                    "status": "succeeded", "created": t1, "invoice_id": "in_201",
                    "refunded": False, "amount_refunded": 0, "description": "Annual License Fee"
                },
                "ch_false_dup_002": {
                    "source": "stripe", "type": "charge", "id": "ch_false_dup_002",
                    "customer_id": "cus_acme_002", "amount": 49900, "currency": "usd",
                    "status": "succeeded", "created": t2, "invoice_id": "in_202",
                    "refunded": False, "amount_refunded": 0, "description": "Onboarding & Implementation Services"
                }
            }
        elif "scenario_3" in sc or "single" in sc or "globex" in sc:
            self.charges = {
                "ch_single_001": {
                    "source": "stripe", "type": "charge", "id": "ch_single_001",
                    "customer_id": "cus_globex_003", "amount": 49900, "currency": "usd",
                    "status": "succeeded", "created": t1, "invoice_id": "in_301",
                    "refunded": False, "amount_refunded": 0, "description": "Monthly Enterprise Tier"
                }
            }
        elif "scenario_4" in sc or "already" in sc or "initech" in sc:
            self.charges = {
                "ch_already_001": {
                    "source": "stripe", "type": "charge", "id": "ch_already_001",
                    "customer_id": "cus_initech_004", "amount": 49900, "currency": "usd",
                    "status": "succeeded", "created": t1, "invoice_id": "in_401",
                    "refunded": False, "amount_refunded": 0, "description": "Annual Standard Seat"
                },
                "ch_already_002": {
                    "source": "stripe", "type": "charge", "id": "ch_already_002",
                    "customer_id": "cus_initech_004", "amount": 49900, "currency": "usd",
                    "status": "succeeded", "created": t2, "invoice_id": "in_402",
                    "refunded": True, "amount_refunded": 49900, "description": "Duplicate Charge - Auto-Reconciled"
                }
            }
            self.refunds = {
                "re_existing_004": {
                    "source": "stripe", "type": "refund", "id": "re_existing_004",
                    "charge_id": "ch_already_002", "amount": 49900, "status": "succeeded",
                    "created": (now - timedelta(days=1)).isoformat() + "Z"
                }
            }
        elif "scenario_5" in sc or "conflict" in sc or "soylent" in sc:
            self.charges = {
                "ch_conflict_001": {
                    "source": "stripe", "type": "charge", "id": "ch_conflict_001",
                    "customer_id": "cus_soylent_005", "amount": 49900, "currency": "usd",
                    "status": "succeeded", "created": t1, "invoice_id": "in_501",
                    "refunded": False, "amount_refunded": 0, "description": "Soylent Core Subscription"
                },
                "ch_conflict_002": {
                    "source": "stripe", "type": "charge", "id": "ch_conflict_002",
                    "customer_id": "cus_soylent_005", "amount": 49900, "currency": "usd",
                    "status": "succeeded", "created": t2, "invoice_id": "in_502",
                    "refunded": False, "amount_refunded": 0, "description": "Soylent Core Additional Charge"
                }
            }
        elif "scenario_6" in sc or "stripe_failure" in sc:
            # Will raise on call
            pass
        else:
            # Default / Scenario 1 (and 7, 8, 9, 10): True Duplicate on Acme Corp
            self.charges = {
                "ch_true_dup_001": {
                    "source": "stripe", "type": "charge", "id": "ch_true_dup_001",
                    "customer_id": "cus_acme_001", "amount": 49900, "currency": "usd",
                    "status": "succeeded", "created": t1, "invoice_id": "in_101",
                    "refunded": False, "amount_refunded": 0,
                    "description": "Annual Professional Subscription (Invoice #101)"
                },
                "ch_true_dup_002": {
                    "source": "stripe", "type": "charge", "id": "ch_true_dup_002",
                    "customer_id": "cus_acme_001", "amount": 49900, "currency": "usd",
                    "status": "succeeded", "created": t2, "invoice_id": "in_102",
                    "refunded": False, "amount_refunded": 0,
                    "description": "Annual Professional Subscription (Invoice #102)"
                }
            }

    def find_customer(self, identifier: str) -> Optional[Dict[str, Any]]:
        ident = identifier.lower()
        if self.scenario == "scenario_6_stripe_failure" or "scenario_6" in ident:
            raise RuntimeError("Stripe API connection timeout (HTTP 503 Service Unavailable)")
        if "scenario_2" in ident or "false" in ident:
            return self.customers["acme_false"]
        if "scenario_3" in ident or "single" in ident or "globex" in ident:
            return self.customers["globex"]
        if "scenario_4" in ident or "already" in ident or "initech" in ident:
            return self.customers["initech"]
        if "scenario_5" in ident or "conflict" in ident or "soylent" in ident:
            return self.customers["soylent"]
        if "hooli" in ident:
            return self.customers["hooli"]
        return self.customers["acme"]

    def list_charges(self, customer_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        if self.scenario == "scenario_6_stripe_failure":
            raise RuntimeError("Stripe API connection timeout (HTTP 503 Service Unavailable)")

        matched = []
        for ch in self.charges.values():
            if customer_id is None or ch.get("customer_id") == customer_id:
                matched.append(dict(ch))
        return matched[:limit]

    def get_charge(self, charge_id: str) -> Optional[Dict[str, Any]]:
        if self.scenario == "scenario_6_stripe_failure":
            raise RuntimeError("Stripe API connection timeout (HTTP 503 Service Unavailable)")
        if charge_id in self.charges:
            return dict(self.charges[charge_id])
        return None

    def get_invoice(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        return {
            "id": invoice_id,
            "status": "paid",
            "amount_due": 49900,
            "amount_paid": 49900,
            "currency": "usd"
        }

    def list_refunds(self, charge_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if charge_id:
            return [dict(r) for r in self.refunds.values() if r["charge_id"] == charge_id]
        return [dict(r) for r in self.refunds.values()]

    def create_refund(
        self,
        charge_id: str,
        amount: Optional[int] = None,
        reason: Optional[str] = None,
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        if self.scenario == "scenario_6_stripe_failure":
            raise RuntimeError("Stripe API error: Refund service unavailable")

        if charge_id not in self.charges:
            raise ValueError(f"Charge {charge_id} not found in Stripe")

        charge = self.charges[charge_id]
        if charge["refunded"]:
            raise ValueError(f"Charge {charge_id} has already been fully refunded")

        refund_amount = amount or charge["amount"]
        refund_id = f"re_test_{uuid.uuid4().hex[:14]}"

        new_refund = {
            "source": "stripe",
            "type": "refund",
            "id": refund_id,
            "charge_id": charge_id,
            "amount": refund_amount,
            "status": "succeeded",
            "created": datetime.utcnow().isoformat() + "Z",
            "reason": reason or "duplicate"
        }

        # Update charge state
        charge["refunded"] = True
        charge["amount_refunded"] = refund_amount
        self.refunds[refund_id] = new_refund

        return new_refund

    def get_refund(self, refund_id: str) -> Dict[str, Any]:
        if refund_id not in self.refunds:
            raise ValueError(f"Refund {refund_id} not found in Stripe")
        return dict(self.refunds[refund_id])

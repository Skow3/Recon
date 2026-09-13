import re
from typing import Dict, Any, Optional
from ..config import settings

class DisputePlanner:
    """Plans dispute investigation and extracts entity parameters from natural language input."""

    def plan_investigation(self, user_request: str, scenario_hint: Optional[str] = None) -> Dict[str, Any]:
        text = user_request.strip()

        # Heuristic entity extraction
        customer_name = None
        customer_email = None
        target_scenario = scenario_hint

        # Email regex
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        if email_match:
            customer_email = email_match.group(0)

        # Name detection
        lower = text.lower()
        if "globex" in lower:
            customer_name = "Globex Corp"
            customer_email = "accounting@globex.com"
            target_scenario = "scenario_3_only_one_charge"
        elif "initech" in lower:
            customer_name = "Initech LLC"
            customer_email = "finance@initech.com"
            target_scenario = "scenario_4_already_refunded"
        elif "soylent" in lower:
            customer_name = "Soylent Corp"
            customer_email = "admin@soylent.com"
            target_scenario = "scenario_5_conflicting_evidence"
        elif "hooli" in lower:
            customer_name = "Hooli"
            customer_email = "ops@hooli.com"
            target_scenario = "scenario_6_stripe_failure"
        elif "false" in lower or "implementation" in lower or "legitimate" in lower:
            customer_name = "Acme Corp"
            customer_email = "billing@acmecorp.com"
            target_scenario = "scenario_2_false_duplicate"
        elif "acme" in lower:
            customer_name = "Acme Corp"
            customer_email = "alex@acmecorp.com"
            if not scenario_hint:
                target_scenario = "scenario_1_true_duplicate"
        else:
            if customer_email and not customer_name:
                local_part = customer_email.split('@')[0]
                customer_name = local_part.capitalize()
            elif not customer_name:
                customer_name = "Customer"
                if not customer_email:
                    customer_email = "customer@example.com"

        return {
            "customer_name": customer_name,
            "customer_email": customer_email,
            "scenario_id": target_scenario,
            "investigation_steps": [
                "search_gmail_claims",
                "list_stripe_charges",
                "list_stripe_refunds",
                "search_slack_context",
                "reconcile_evidence",
                "generate_decision",
                "deterministic_safety_check"
            ]
        }

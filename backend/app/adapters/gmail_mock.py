from typing import List, Dict, Any, Optional
from datetime import datetime
from ..tools.interfaces import GmailClient

class MockGmailClient(GmailClient):
    """Deterministic Mock Gmail Client for demos and evaluations."""

    def __init__(self, scenario: Optional[str] = None):
        self.scenario = scenario or "scenario_1_true_duplicate"

    def search_customer(self, customer_identifier: str) -> List[Dict[str, Any]]:
        # Normalize search identifier and scenario
        ident = customer_identifier.lower()
        sc = (self.scenario or "").lower()

        if "scenario_2" in sc or "false" in sc or "scenario_2" in ident or "false" in ident:
            return [{
                "source": "gmail",
                "message_id": "msg_gmail_false_dup_002",
                "thread_id": "th_gmail_false_dup_002",
                "sender": "billing@acmecorp.com",
                "recipient": "support@ourcompany.com",
                "subject": "Billing Error: Charged twice for $499",
                "timestamp": "2026-09-12T14:20:00Z",
                "body": "Hello Support, I noticed two charges of $499 on our company credit card this morning. We only signed up for one annual plan. Please review and refund the duplicate charge.",
                "relevant_claims": [
                    "Customer claims duplicate charge of $499",
                    "Customer states they only signed up for one annual plan",
                    "Customer requests refund for the duplicate charge"
                ]
            }]

        if "scenario_3" in sc or "single" in sc or "scenario_3" in ident or "single" in ident or "one_charge" in ident:
            return [{
                "source": "gmail",
                "message_id": "msg_gmail_single_003",
                "thread_id": "th_gmail_single_003",
                "sender": "accounting@globex.com",
                "recipient": "support@ourcompany.com",
                "subject": "Urgent: I was charged twice on my card",
                "timestamp": "2026-09-12T15:10:00Z",
                "body": "Hi, our bank statement shows two charges for $499 from your service. Please refund one immediately.",
                "relevant_claims": [
                    "Customer reports two charges of $499 on their statement",
                    "Customer requests immediate refund"
                ]
            }]

        if "scenario_4" in sc or "already" in sc or "scenario_4" in ident or "already_refunded" in ident:
            return [{
                "source": "gmail",
                "message_id": "msg_gmail_refunded_004",
                "thread_id": "th_gmail_refunded_004",
                "sender": "finance@initech.com",
                "recipient": "support@ourcompany.com",
                "subject": "Please refund my duplicate charge",
                "timestamp": "2026-09-12T09:00:00Z",
                "body": "Hi team, following up on our duplicate charge ticket. Please ensure the second $499 charge is refunded.",
                "relevant_claims": [
                    "Customer following up on duplicate charge refund",
                    "Target amount: $499"
                ]
            }]

        if "scenario_5" in sc or "conflict" in sc or "scenario_5" in ident or "conflict" in ident:
            return [{
                "source": "gmail",
                "message_id": "msg_gmail_conflict_005",
                "thread_id": "th_gmail_conflict_005",
                "sender": "admin@soylent.com",
                "recipient": "support@ourcompany.com",
                "subject": "Duplicate invoice charges dispute",
                "timestamp": "2026-09-12T11:45:00Z",
                "body": "We see two charges of $499 on Sept 10. Our contract was only for 1 license tier.",
                "relevant_claims": [
                    "Customer claims duplicate charge of $499",
                    "Customer states contract is only for 1 license tier"
                ]
            }]

        if "scenario_6" in sc or "stripe_failure" in sc or "scenario_6" in ident or "stripe_failure" in ident:
            return [{
                "source": "gmail",
                "message_id": "msg_gmail_fail_006",
                "thread_id": "th_gmail_fail_006",
                "sender": "ops@hooli.com",
                "recipient": "support@ourcompany.com",
                "subject": "Double charged on subscription renewal",
                "timestamp": "2026-09-12T12:00:00Z",
                "body": "We were double billed $499 this month. Please issue a refund.",
                "relevant_claims": [
                    "Customer reports double billing of $499",
                    "Customer requests refund"
                ]
            }]

        # Default: Scenario 1 - True Duplicate
        return [{
            "source": "gmail",
            "message_id": "msg_gmail_true_dup_001",
            "thread_id": "th_gmail_true_dup_001",
            "sender": "alex@acmecorp.com",
            "recipient": "billing@ourcompany.com",
            "subject": "Double charged for annual subscription",
            "timestamp": "2026-09-12T10:15:00Z",
            "body": "Hi, I was charged twice for my annual subscription. I see two charges of $499 on our card. Please refund the extra charge as soon as possible.",
            "relevant_claims": [
                "Customer reports charged twice for annual subscription",
                "Customer sees two identical charges of $499",
                "Customer requests refund for the duplicate charge"
            ]
        }]

    def search_messages(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        q_lower = query.lower()
        if any(k in q_lower for k in ["grocer", "shopping", "buy", "groceries"]):
            return [{
                "source": "gmail",
                "message_id": "msg_grocery_list_101",
                "thread_id": "th_grocery_list_101",
                "sender": "household-sync@family.net",
                "recipient": "me@domain.com",
                "subject": "Upcoming Grocery List for the Week",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "body": "Hi, here is the upcoming grocery list to buy:\n• Organic Whole Milk (1 gal)\n• Greek Yogurt (32oz)\n• Fresh Spinach & Baby Kale\n• Bananas & Honeycrisp Apples\n• Sourdough Bread\n• Extra Virgin Olive Oil\n• Free-range Eggs (1 doz)",
                "relevant_claims": ["Grocery list itemized", "7 household items needed"]
            }]
        elif any(k in q_lower for k in ["secret", "sameer"]):
            return [{
                "source": "gmail",
                "message_id": "msg_secrets_sameer_101",
                "thread_id": "th_secrets_sameer_101",
                "sender": "confidential@vault.internal",
                "recipient": "me@domain.com",
                "subject": "Confidential records regarding Sameer",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "body": "Project audit for Sameer: Security tokens and cryptographic credentials rotated successfully.",
                "relevant_claims": ["Security audit", "Confidential record"]
            }]
        else:
            return [{
                "source": "gmail",
                "message_id": f"msg_query_{abs(hash(query)) % 10000:04d}",
                "thread_id": f"th_query_{abs(hash(query)) % 10000:04d}",
                "sender": "notifications@workspace.io",
                "recipient": "me@domain.com",
                "subject": f"Notice regarding: {query[:40]}",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "body": f"Incoming correspondence matching operational query: '{query}'. Detailed intelligence extracted and ready for downstream dispatch.",
                "relevant_claims": ["Operational match"]
            }]

    def get_thread(self, thread_id: str) -> Dict[str, Any]:
        messages = self.search_customer(thread_id)
        return {
            "thread_id": thread_id,
            "messages": messages,
            "total_messages": len(messages)
        }

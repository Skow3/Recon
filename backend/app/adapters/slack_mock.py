from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from ..tools.interfaces import SlackClient

class MockSlackClient(SlackClient):
    """Deterministic Mock Slack Client for internal billing channel context."""

    def __init__(self, scenario: Optional[str] = None):
        self.scenario = scenario or "scenario_1_true_duplicate"
        self.posted_messages: List[Dict[str, Any]] = []

    def search_billing_messages(self, query: str, channel: str = "billing") -> List[Dict[str, Any]]:
        q = query.lower()
        sc = (self.scenario or "").lower()
        now = datetime.utcnow()
        t1 = (now - timedelta(days=1)).isoformat() + "Z"

        if "scenario_2" in sc or "false" in sc or "scenario_2" in q or "false" in q:
            return [{
                "source": "slack",
                "channel": f"#{channel}",
                "message_id": "msg_slack_false_dup_002",
                "timestamp": t1,
                "author": "sarah_salesops",
                "text": "The second $499 charge is the legitimate implementation fee discussed with Acme. Customer agreed to standard kickoff onboarding fee on Friday."
            }]

        if "scenario_3" in sc or "single" in sc or "scenario_3" in q or "single" in q or "globex" in q:
            return [{
                "source": "slack",
                "channel": f"#{channel}",
                "message_id": "msg_slack_single_003",
                "timestamp": t1,
                "author": "dave_billing",
                "text": "Checked Globex records, their account has only 1 active tier charge. No record of duplicate billing in our system."
            }]

        if "scenario_4" in sc or "already" in sc or "scenario_4" in q or "already" in q or "initech" in q:
            return [{
                "source": "slack",
                "channel": f"#{channel}",
                "message_id": "msg_slack_refunded_004",
                "timestamp": t1,
                "author": "jen_finance",
                "text": "Duplicate charge on Initech was caught during morning reconciliation and already refunded yesterday via Stripe (re_existing_004)."
            }]

        if "scenario_5" in sc or "conflict" in sc or "scenario_5" in q or "conflict" in q or "soylent" in q:
            return [
                {
                    "source": "slack",
                    "channel": f"#{channel}",
                    "message_id": "msg_slack_conflict_005a",
                    "timestamp": t1,
                    "author": "tom_csm",
                    "text": "Looks like an accidental double charge for Soylent, please refund."
                },
                {
                    "source": "slack",
                    "channel": f"#{channel}",
                    "message_id": "msg_slack_conflict_005b",
                    "timestamp": (now - timedelta(hours=2)).isoformat() + "Z",
                    "author": "karen_legal",
                    "text": "Hold on - do not refund Soylent! They requested custom enterprise SLA add-on which accounts for the second $499 charge."
                }
            ]

        if "scenario_6" in sc or "stripe_failure" in sc or "scenario_6" in q or "stripe_failure" in q or "hooli" in q:
            return [{
                "source": "slack",
                "channel": f"#{channel}",
                "message_id": "msg_slack_fail_006",
                "timestamp": t1,
                "author": "alex_billing",
                "text": "Customer Hooli mentioned getting double billed. Need to inspect Stripe."
            }]

        # Default: Scenario 1 - True Duplicate
        return [{
            "source": "slack",
            "channel": f"#{channel}",
            "message_id": "msg_slack_true_dup_001",
            "timestamp": t1,
            "author": "marcus_lead_account_exec",
            "text": "Acme should only have one annual subscription charge. If they were billed twice, that's an accidental webhook retry."
        }]

    def post_message(self, channel: str, text: str) -> Dict[str, Any]:
        msg = {
            "source": "slack",
            "channel": channel if channel.startswith("#") else f"#{channel}",
            "message_id": f"msg_post_{len(self.posted_messages) + 1}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "author": "RECON Bot",
            "text": text
        }
        self.posted_messages.append(msg)
        return {
            "ok": True,
            "channel": msg["channel"],
            "message": msg
        }

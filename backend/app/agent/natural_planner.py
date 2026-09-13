import re
import json
from typing import Dict, Any, List, Optional
from ..config import settings
from ..integrations.registry import ToolRegistry, APPS_CATALOGUE

PLANNER_SYSTEM_PROMPT = """You are RECON's Goal-to-Workflow Planner.
Given a user's natural language goal and available workspace apps, your task is to analyze the requirements, determine the necessary connected apps (e.g. Gmail, Slack, Stripe), and generate a structured workflow plan:
1. Trigger Ingestion
2. Duplicate Prevention / Idempotency
3. Context Gathering
4. Reconciliation & Entity Extraction
5. Policy & Approval Check
6. Action Execution
7. Verification & Audit Logging

Respond ONLY with valid JSON matching this schema:
{
  "workflow_name": "Concise workflow name (e.g. Grocery List Email Notifier)",
  "description": "Clear 1-2 sentence description",
  "recommended_apps": ["gmail", "slack"],
  "trigger": {
    "app": "gmail",
    "event": "new_email",
    "filter": "search query or filter condition"
  },
  "requires_slack_channel": true,
  "suggested_channel": "general",
  "slack_reminder": "Remember to invite the RECON bot to this Slack channel (e.g. /invite @RECON Bot).",
  "plan_steps": [
    {
      "step": 1,
      "name": "Step Name",
      "app": "app_id",
      "action": "Description of action",
      "type": "READ" | "WRITE" | "SAFETY" | "RECONCILIATION" | "VERIFICATION"
    }
  ],
  "required_permissions": {
    "app_id": {"permission_name": true}
  },
  "approval_required": false,
  "risk_level": "LOW" | "MEDIUM" | "HIGH"
}
"""

class NaturalGoalPlanner:
    """Interprets freeform goals into executable multi-app workflow plans."""

    def plan_from_goal(self, goal: str, workspace_apps: Optional[List[str]] = None) -> Dict[str, Any]:
        goal_text = goal.strip()
        lower_goal = goal_text.lower()

        # Check if OpenAI is configured and not in mock mode
        if (
            not settings.MOCK_MODE
            and settings.OPENAI_API_KEY
            and settings.OPENAI_API_KEY.strip()
            and not settings.OPENAI_API_KEY.startswith("your_")
        ):
            try:
                return self._call_openai(goal_text, workspace_apps)
            except Exception as e:
                print(f"[NaturalGoalPlanner] OpenAI planning error: {e}. Using deterministic planner.")

        return self._deterministic_plan(goal_text, workspace_apps)

    def _call_openai(self, goal: str, workspace_apps: Optional[List[str]]) -> Dict[str, Any]:
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=8.0)

        apps_info = {
            app_id: {
                "name": app.name,
                "category": app.category.value,
                "events": app.supported_events,
                "actions": app.available_actions
            }
            for app_id, app in APPS_CATALOGUE.items()
        }

        user_prompt = (
            f"User Goal: {goal}\n"
            f"Available Workspace Apps: {workspace_apps or list(APPS_CATALOGUE.keys())}\n"
            f"Apps Catalogue: {json.dumps(apps_info)}"
        )

        create_kwargs = {
            "model": settings.OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]
        }

        is_newer_reasoning = any(m in settings.OPENAI_MODEL.lower() for m in ["gpt-5", "o1", "o3", "nano"])
        if not is_newer_reasoning:
            create_kwargs["temperature"] = 0.1
        if any(m in settings.OPENAI_MODEL.lower() for m in ["gpt-4", "gpt-3.5"]):
            create_kwargs["response_format"] = {"type": "json_object"}

        response = client.chat.completions.create(**create_kwargs)
        raw_text = response.choices[0].message.content
        data = json.loads(raw_text)
        return data

    def _deterministic_plan(self, goal: str, workspace_apps: Optional[List[str]]) -> Dict[str, Any]:
        lower = goal.lower()

        # 1. Flagship: Internship / Job Application Monitor
        if any(k in lower for k in ["intern", "application", "job", "career", "interview", "offer"]):
            return {
                "workflow_name": "Internship Application Monitor",
                "description": "Monitors Gmail for recruiter updates, extracts interview deadlines and offer details, filters out marketing spam, and delivers structured alerts to Slack.",
                "recommended_apps": ["gmail", "slack"],
                "trigger": {
                    "app": "gmail",
                    "event": "new_email",
                    "filter": "subject:(interview OR offer OR application OR status OR coding OR assessment)"
                },
                "requires_slack_channel": True,
                "suggested_channel": "internships",
                "slack_reminder": "Remember to invite the RECON bot to this Slack channel (e.g. /invite @RECON Bot).",
                "plan_steps": [
                    {
                        "step": 1,
                        "name": "Inbox Ingestion",
                        "app": "gmail",
                        "action": "Poll Gmail inbox for unread recruiter correspondence",
                        "type": "READ"
                    },
                    {
                        "step": 2,
                        "name": "Deduplication & Idempotency",
                        "app": "system",
                        "action": "Check message ID against ProcessedEvents table to eliminate duplicate notifications",
                        "type": "SAFETY"
                    },
                    {
                        "step": 3,
                        "name": "Thread Context Gathering",
                        "app": "gmail",
                        "action": "Retrieve full conversation thread and sender headers",
                        "type": "READ"
                    },
                    {
                        "step": 4,
                        "name": "Entity Extraction & Importance Classification",
                        "app": "system",
                        "action": "Classify importance (HIGH/MEDIUM/LOW) and extract Company, Role, Update Type, and Action Deadline",
                        "type": "RECONCILIATION"
                    },
                    {
                        "step": 5,
                        "name": "Safety & Noise Filter",
                        "app": "system",
                        "action": "Suppress marketing spam and newsletters; verify notification channel routing",
                        "type": "SAFETY"
                    },
                    {
                        "step": 6,
                        "name": "Slack Notification Delivery",
                        "app": "slack",
                        "action": "Format and dispatch structured recruiter alert to designated Slack channel",
                        "type": "WRITE"
                    },
                    {
                        "step": 7,
                        "name": "Verification & Audit",
                        "app": "system",
                        "action": "Verify delivery status via Slack API and commit execution record to audit log",
                        "type": "VERIFICATION"
                    }
                ],
                "required_permissions": {
                    "gmail": {"read_emails": True},
                    "slack": {"post_messages": True}
                },
                "approval_required": False,
                "risk_level": "LOW"
            }

        # 2. Flagship: Billing & Dispute Investigation
        if any(k in lower for k in ["bill", "dispute", "refund", "stripe", "charge", "payment"]):
            return {
                "workflow_name": "Billing Dispute Investigator",
                "description": "Reconciles customer billing disputes across Gmail, Stripe ledger, and Slack internal discussions, enforces strict human approval gates, and executes verified refunds in Stripe test mode.",
                "recommended_apps": ["gmail", "stripe", "slack"],
                "trigger": {
                    "app": "gmail",
                    "event": "dispute_received",
                    "filter": "subject:(refund OR overcharge OR dispute OR billing)"
                },
                "requires_slack_channel": True,
                "suggested_channel": "billing",
                "slack_reminder": "Remember to invite the RECON bot to this Slack channel (e.g. /invite @RECON Bot).",
                "plan_steps": [
                    {
                        "step": 1,
                        "name": "Customer Claim Ingestion",
                        "app": "gmail",
                        "action": "Parse customer complaint email, claimed charge amount, and timestamp",
                        "type": "READ"
                    },
                    {
                        "step": 2,
                        "name": "Dispute Idempotency Check",
                        "app": "system",
                        "action": "Verify case ID and ensure no prior refund has been issued or requested",
                        "type": "SAFETY"
                    },
                    {
                        "step": 3,
                        "name": "Cross-App Evidence Collection",
                        "app": "stripe",
                        "action": "Query Stripe payment charges and search Slack #billing for team context",
                        "type": "READ"
                    },
                    {
                        "step": 4,
                        "name": "Evidence Reconciliation",
                        "app": "system",
                        "action": "Reconcile claim against Stripe charge history and Slack discussion",
                        "type": "RECONCILIATION"
                    },
                    {
                        "step": 5,
                        "name": "Mandatory Human Approval Gate",
                        "app": "system",
                        "action": "Block execution until explicit human authorization is recorded (Refund Guard)",
                        "type": "SAFETY"
                    },
                    {
                        "step": 6,
                        "name": "Stripe Action Execution",
                        "app": "stripe",
                        "action": "Execute test-mode refund via Stripe API with exact idempotency key",
                        "type": "FINANCIAL"
                    },
                    {
                        "step": 7,
                        "name": "Ledger Verification & Audit",
                        "app": "stripe",
                        "action": "Query Stripe API to verify refund status=succeeded and write immutable audit trail",
                        "type": "VERIFICATION"
                    }
                ],
                "required_permissions": {
                    "gmail": {"read_emails": True},
                    "stripe": {"search_charges": True, "create_refunds": "APPROVAL_REQUIRED"},
                    "slack": {"search_messages": True, "post_messages": True}
                },
                "approval_required": True,
                "risk_level": "HIGH"
            }

        # 3. Dedicated: Groceries / Shopping List Monitor
        if any(k in lower for k in ["grocer", "grocery", "shopping list", "buy list"]):
            return {
                "workflow_name": "Grocery List Email Notifier",
                "description": "Monitors incoming emails for grocery and shopping lists, extracts needed items, and delivers alerts to Slack.",
                "recommended_apps": ["gmail", "slack"],
                "trigger": {
                    "app": "gmail",
                    "event": "new_email",
                    "filter": "groceries"
                },
                "requires_slack_channel": True,
                "suggested_channel": "general",
                "slack_reminder": "Remember to invite the RECON bot to this Slack channel (e.g. /invite @RECON Bot).",
                "plan_steps": [
                    {
                        "step": 1,
                        "name": "Email Search & Ingestion",
                        "app": "gmail",
                        "action": "Search inbox for emails matching grocery keywords",
                        "type": "READ"
                    },
                    {
                        "step": 2,
                        "name": "Event Deduplication",
                        "app": "system",
                        "action": "Ensure email has not been processed already",
                        "type": "SAFETY"
                    },
                    {
                        "step": 3,
                        "name": "Grocery Item Extraction",
                        "app": "gmail",
                        "action": "Extract grocery items and quantity list from email body",
                        "type": "RECONCILIATION"
                    },
                    {
                        "step": 4,
                        "name": "Policy & Channel Verification",
                        "app": "system",
                        "action": "Verify target destination channel permissions",
                        "type": "SAFETY"
                    },
                    {
                        "step": 5,
                        "name": "Slack Alert Dispatch",
                        "app": "slack",
                        "action": "Post structured grocery list alert to Slack channel",
                        "type": "WRITE"
                    },
                    {
                        "step": 6,
                        "name": "Delivery Verification",
                        "app": "system",
                        "action": "Verify Slack API delivery receipt and log to audit trail",
                        "type": "VERIFICATION"
                    }
                ],
                "required_permissions": {
                    "gmail": {"read_emails": True},
                    "slack": {"post_messages": True}
                },
                "approval_required": False,
                "risk_level": "LOW"
            }

        # 4. Intelligent Dynamic Multi-App Workflow Plan
        detected_apps = []
        if any(k in lower for k in ["email", "mail", "gmail", "inbox", "letter", "newsletter", "message"]):
            detected_apps.append("gmail")
        if any(k in lower for k in ["slack", "notify", "channel", "alert", "ping", "inform", "send", "dm", "post"]):
            detected_apps.append("slack")
        if any(k in lower for k in ["stripe", "payment", "charge", "refund", "billing", "invoice", "checkout"]):
            detected_apps.append("stripe")

        final_apps = workspace_apps or detected_apps or ["gmail", "slack"]
        if not final_apps:
            final_apps = ["gmail", "slack"]

        # Derive a clean title from goal
        words = [w.capitalize() for w in re.findall(r'[a-zA-Z]{3,}', goal) if w.lower() not in ["the", "and", "for", "with", "from", "that", "this", "check", "notify", "upcoming"]]
        suggested_name = " ".join(words[:3]) + " Notifier" if words else "Multi-App Task Orchestrator"

        # Extract search filter
        filter_words = [w for w in re.findall(r'[a-zA-Z]{3,}', goal) if w.lower() not in ["check", "email", "upcoming", "list", "notify", "and", "the", "for", "with", "from"]]
        search_filter = " ".join(filter_words[:2]) if filter_words else "update"

        return {
            "workflow_name": suggested_name,
            "description": f"Automates cross-app orchestration for: '{goal}'.",
            "recommended_apps": final_apps,
            "trigger": {
                "app": final_apps[0] if final_apps else "gmail",
                "event": "event_detected",
                "filter": search_filter
            },
            "requires_slack_channel": "slack" in final_apps,
            "suggested_channel": "general",
            "slack_reminder": "Remember to invite the RECON bot to this Slack channel (e.g. /invite @RECON Bot).",
            "plan_steps": [
                {
                    "step": 1,
                    "name": "Source Event Ingestion",
                    "app": (final_apps[0] if final_apps else "gmail"),
                    "action": f"Ingest incoming trigger for goal: {goal}",
                    "type": "READ"
                },
                {
                    "step": 2,
                    "name": "Event Deduplication",
                    "app": "system",
                    "action": "Verify event deduplication key against ProcessedEvents table",
                    "type": "SAFETY"
                },
                {
                    "step": 3,
                    "name": "Context Gathering",
                    "app": (final_apps[0] if final_apps else "gmail"),
                    "action": "Extract parameters, payload, and relevant historical context",
                    "type": "READ"
                },
                {
                    "step": 4,
                    "name": "Decision & Entity Extraction",
                    "app": "system",
                    "action": "Analyze multi-app payload and determine required downstream operations",
                    "type": "RECONCILIATION"
                },
                {
                    "step": 5,
                    "name": "Safety & Policy Validation",
                    "app": "system",
                    "action": "Verify workspace permissions and assess operational risk",
                    "type": "SAFETY"
                },
                {
                    "step": 6,
                    "name": "Downstream Action Dispatch",
                    "app": (final_apps[1] if len(final_apps) > 1 else "slack"),
                    "action": "Execute downstream update or notification",
                    "type": "WRITE"
                },
                {
                    "step": 7,
                    "name": "Verification & Audit",
                    "app": "system",
                    "action": "Verify resulting state across target apps and log execution trace",
                    "type": "VERIFICATION"
                }
            ],
            "required_permissions": {
                app: {"read": True, "write": True} for app in final_apps
            },
            "approval_required": "stripe" in final_apps,
            "risk_level": "HIGH" if "stripe" in final_apps else "LOW"
        }

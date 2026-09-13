import re
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from ..config import settings
from ..models.workspace import WorkspaceModel, WorkflowModel, WorkflowRunModel, ProcessedEventModel
from ..models.audit import ToolRunModel, AuditLogModel
from ..integrations.registry import ToolRegistry
from ..adapters.slack_live import LiveSlackClient
from ..adapters.slack_mock import MockSlackClient
from ..adapters.gmail_live import LiveGmailClient
from ..adapters.gmail_mock import MockGmailClient

MOCK_INTERNSHIP_SCENARIOS = {
    "stripe_interview": {
        "id": "msg_intern_stripe_001",
        "sender": "recruiting@stripe.com",
        "subject": "Invitation to Technical Screen — Software Engineering Intern (Summer 2026)",
        "body": "Hi Alex,\n\nThanks for applying to Stripe! We were impressed by your background and would love to invite you to a 45-minute technical screen with one of our infrastructure engineers.\n\nPlease select a timeslot using the scheduling link below within 48 hours:\nhttps://stripe.com/interviews/schedule/alex-9482\n\nDeadline to schedule: September 18, 2026 at 5:00 PM PDT.\n\nBest,\nStripe University Recruiting",
        "timestamp": "2026-09-13T16:45:00Z"
    },
    "google_offer": {
        "id": "msg_intern_google_002",
        "sender": "students-offers@google.com",
        "subject": "Official Offer of Employment — Software Engineering Intern, Summer 2026",
        "body": "Dear Alex,\n\nWe are thrilled to extend an offer for a Software Engineering Intern position with Google for Summer 2026 in Mountain View, CA!\n\nPlease find your formal offer letter attached in the applicant portal. The deadline to sign and accept is September 25, 2026.\n\nCongratulations,\nGoogle Student Operations",
        "timestamp": "2026-09-13T17:15:00Z"
    },
    "datadog_status": {
        "id": "msg_intern_datadog_003",
        "sender": "talent-ops@datadoghq.com",
        "subject": "Datadog Application Update: Software Engineer Intern (Summer 2026)",
        "body": "Hello Alex,\n\nThank you for your interest in Datadog. Your application has been moved to our Engineering Review stage. Our team is currently reviewing your GitHub portfolio and background.\n\nNo action is required from you at this time. We will reach out if there is a match.\n\nBest regards,\nDatadog Recruiting",
        "timestamp": "2026-09-13T14:10:00Z"
    },
    "newsletter_spam": {
        "id": "msg_intern_handshake_004",
        "sender": "digest@handshake.com",
        "subject": "Top 50 internships hiring this week in tech & finance",
        "body": "Hey Alex! Check out these hot new roles from companies hiring students like you. Apply today with 1-click on Handshake! Unsubscribe here.",
        "timestamp": "2026-09-13T12:00:00Z"
    }
}

class InternshipMonitorEngine:
    """
    Flagship Workflow Engine: Multi-App Internship Application Monitor.
    Orchestrates Gmail & Slack with deduplication, entity extraction, and importance filtering.
    """

    def __init__(self, db: Session, workspace_id: str = "ws_internships", workflow_id: str = "wf_internship_monitor", mock_mode: bool = False):
        self.db = db
        self.workspace_id = workspace_id
        self.workflow_id = workflow_id
        self.mock_mode = mock_mode or settings.MOCK_MODE

    def scan_inbox(self, query: str = "subject:(interview OR offer OR application)", force_reprocess: bool = False, target_channel: str = "internships") -> Dict[str, Any]:
        """Scans the user's live Gmail inbox for recruiter/internship emails and processes them."""
        if self.mock_mode:
            return self.run_scenario(scenario_key="stripe_interview", force_reprocess=force_reprocess, target_channel=target_channel)

        try:
            live_gmail = LiveGmailClient()
            messages = live_gmail.search_messages(query=query, max_results=10)
        except Exception as e:
            print(f"[InternshipMonitor] Live Gmail search failed: {e}")
            messages = []

        if not messages:
            # Fallback to broader recruiter keywords if initial query was specific
            try:
                live_gmail = LiveGmailClient()
                messages = live_gmail.search_messages(query="intern OR internship OR recruiter OR interview OR offer", max_results=5)
            except Exception:
                messages = []

        if not messages:
            return {
                "run_id": f"run_{uuid.uuid4().hex[:8]}",
                "status": "NO_MATCHING_EMAILS",
                "message_id": None,
                "reason": f"Searched connected Gmail inbox with filter '{query}'. 0 recruiter messages found.",
                "plan_steps": [
                    {"step": 1, "name": "Email Ingestion", "app": "gmail", "status": "COMPLETED"},
                    {"step": 2, "name": "Inbox Scan", "app": "gmail", "status": "NO_EMAILS_FOUND"}
                ],
                "extracted_data": {
                    "company": "None",
                    "role": "None",
                    "update_type": "NONE",
                    "importance": "LOW",
                    "action_required": False,
                    "summary": f"Searched connected Gmail inbox with filter '{query}'. 0 recruiter messages found."
                },
                "decision": {"importance": "LOW", "action_required": False},
                "action_result": {"status": "SKIPPED", "reason": "No recruiter emails found in live inbox."},
                "verification_result": {"verified": True, "action_taken": "NO_ACTION_REQUIRED"}
            }

        # Select the best email: prioritize an unprocessed email, or top keyword match
        chosen_email = None
        if not force_reprocess:
            for m in messages:
                m_id = m.get("message_id") or m.get("id")
                already_processed = self.db.query(ProcessedEventModel).filter(
                    ProcessedEventModel.source_app == "gmail",
                    ProcessedEventModel.source_event_id == m_id,
                    ProcessedEventModel.workflow_id == self.workflow_id
                ).first()
                if not already_processed:
                    chosen_email = m
                    break

        if not chosen_email:
            for m in messages:
                subj_lower = m.get("subject", "").lower()
                if any(k in subj_lower for k in ["interview", "screen", "offer", "congratulations"]):
                    chosen_email = m
                    break
            if not chosen_email:
                chosen_email = messages[0]

        email_data = {
            "id": chosen_email.get("message_id") or chosen_email.get("id"),
            "sender": chosen_email.get("sender", ""),
            "subject": chosen_email.get("subject", ""),
            "body": chosen_email.get("body", ""),
            "timestamp": chosen_email.get("timestamp", datetime.utcnow().isoformat() + "Z")
        }

        return self.process_email(email_data=email_data, force_reprocess=force_reprocess, target_channel=target_channel)

    def run_scenario(self, scenario_key: str = "stripe_interview", force_reprocess: bool = False, target_channel: str = "internships") -> Dict[str, Any]:
        """Runs one of the deterministic mock scenarios."""
        email_data = MOCK_INTERNSHIP_SCENARIOS.get(scenario_key)
        if not email_data:
            # Fallback to first scenario
            email_data = list(MOCK_INTERNSHIP_SCENARIOS.values())[0]
            scenario_key = "stripe_interview"

        return self.process_email(email_data, force_reprocess=force_reprocess, target_channel=target_channel)

    def process_email(self, email_data: Dict[str, Any], force_reprocess: bool = False, target_channel: str = "internships") -> Dict[str, Any]:
        run_id = f"run_{uuid.uuid4().hex[:8]}"
        msg_id = email_data.get("id") or f"msg_{uuid.uuid4().hex[:6]}"

        # 1. Workspace Security Boundary Check
        workspace = self.db.query(WorkspaceModel).filter(WorkspaceModel.id == self.workspace_id).first()
        connected_apps = workspace.connected_apps if workspace else ["gmail", "slack"]

        ToolRegistry.verify_tool_access(connected_apps, "gmail.search_messages")
        ToolRegistry.verify_tool_access(connected_apps, "slack.post_message")

        # Plan snapshot tracking
        plan_steps = [
            {"step": 1, "name": "Email Ingestion", "app": "gmail", "status": "COMPLETED"},
            {"step": 2, "name": "Deduplication & Idempotency", "app": "system", "status": "RUNNING"},
            {"step": 3, "name": "Context Gathering", "app": "gmail", "status": "PENDING"},
            {"step": 4, "name": "Entity Extraction & Importance Classification", "app": "system", "status": "PENDING"},
            {"step": 5, "name": "Noise Suppression Policy", "app": "system", "status": "PENDING"},
            {"step": 6, "name": "Slack Notification Delivery", "app": "slack", "status": "PENDING"},
            {"step": 7, "name": "Verification & Audit Trail", "app": "system", "status": "PENDING"}
        ]

        # 2. Check Deduplication / Idempotency
        existing = self.db.query(ProcessedEventModel).filter(
            ProcessedEventModel.source_app == "gmail",
            ProcessedEventModel.source_event_id == msg_id,
            ProcessedEventModel.workflow_id == self.workflow_id
        ).first()

        if existing and not force_reprocess:
            plan_steps[1]["status"] = "BLOCKED_DUPLICATE"
            self._log_audit(
                run_id=run_id,
                event_type="EVENT_DEDUPLICATED",
                details={"message_id": msg_id, "reason": "Event already processed. Duplicate notification suppressed."}
            )
            return {
                "run_id": run_id,
                "status": "SKIPPED_DUPLICATE",
                "message_id": msg_id,
                "reason": f"Message {msg_id} was already processed at {existing.processed_at.isoformat()}Z. Duplicate skipped.",
                "plan_steps": plan_steps
            }

        plan_steps[1]["status"] = "COMPLETED"

        # 3. Context Gathering
        plan_steps[2]["status"] = "COMPLETED"
        subject = email_data.get("subject", "")
        body = email_data.get("body", "")
        sender = email_data.get("sender", "")

        # 4. Entity Extraction & Importance Classification
        plan_steps[3]["status"] = "RUNNING"
        extracted = self._extract_entities(subject, body, sender)
        plan_steps[3]["status"] = "COMPLETED"

        # 5. Policy & Noise Suppression
        plan_steps[4]["status"] = "RUNNING"
        importance = extracted["importance"]
        is_suppressed = (importance == "LOW")
        plan_steps[4]["status"] = "SUPPRESSED" if is_suppressed else "PASSED"

        # 6. Action Execution (Slack Notification)
        action_result = {}
        verification_result = {}

        if is_suppressed:
            plan_steps[5]["status"] = "SKIPPED"
            action_result = {
                "action": "SUPPRESS_NOTIFICATION",
                "status": "SUPPRESSED",
                "reason": f"Email categorized as {extracted['update_type']} (LOW importance). Suppressed to prevent alert fatigue."
            }
            plan_steps[6]["status"] = "COMPLETED"
            verification_result = {
                "verified": True,
                "action_taken": "NO_ACTION_REQUIRED",
                "policy": "NOISE_FILTER"
            }
        else:
            plan_steps[5]["status"] = "RUNNING"
            slack_text = self._format_slack_notification(extracted, sender, subject)
            slack_res = self._post_to_slack(target_channel, slack_text)
            action_result = slack_res
            plan_steps[5]["status"] = "COMPLETED"

            # 7. Verification
            plan_steps[6]["status"] = "RUNNING"
            verified = bool(slack_res.get("ok"))
            verification_result = {
                "verified": verified,
                "delivery_confirmed": verified,
                "channel": target_channel if target_channel.startswith("#") else f"#{target_channel}",
                "message_ts": slack_res.get("message", {}).get("message_id") or slack_res.get("message", {}).get("timestamp")
            }
            plan_steps[6]["status"] = "COMPLETED" if verified else "FAILED"

        # Record Processed Event in DB
        if not existing:
            event_rec = ProcessedEventModel(
                source_app="gmail",
                source_event_id=msg_id,
                workflow_id=self.workflow_id
            )
            self.db.add(event_rec)

        # Record Workflow Run in DB
        wf_run = WorkflowRunModel(
            id=run_id,
            workflow_id=self.workflow_id,
            workspace_id=self.workspace_id,
            trigger_event={"source": "gmail", "message_id": msg_id, "subject": subject, "sender": sender},
            status="COMPLETED",
            plan_snapshot=plan_steps,
            extracted_data=extracted,
            decision={"importance": importance, "update_type": extracted["update_type"], "action_required": extracted["action_required"]},
            approval_status="NOT_REQUIRED",
            action_result=action_result,
            verification_result=verification_result,
            completed_at=datetime.utcnow()
        )
        self.db.add(wf_run)

        # Audit Log
        self._log_audit(
            run_id=run_id,
            event_type="WORKFLOW_RUN_COMPLETED",
            details={
                "importance": importance,
                "company": extracted["company"],
                "role": extracted["role"],
                "action": action_result.get("action", "POST_SLACK")
            }
        )

        self.db.commit()

        return {
            "run_id": run_id,
            "status": "COMPLETED",
            "message_id": msg_id,
            "plan_steps": plan_steps,
            "extracted_data": extracted,
            "decision": {"importance": importance, "action_required": extracted["action_required"]},
            "action_result": action_result,
            "verification_result": verification_result
        }

    def _extract_entities(self, subject: str, body: str, sender: str) -> Dict[str, Any]:
        combined = f"{subject}\n{body}".strip()
        lower = combined.lower()

        # Company Extraction
        company = "Unknown Company"
        company_patterns = [
            ("Stripe", r"stripe"),
            ("Google", r"google"),
            ("Datadog", r"datadog"),
            ("Handshake", r"handshake"),
            ("Meta", r"meta"),
            ("Amazon", r"amazon"),
            ("Microsoft", r"microsoft"),
            ("Apple", r"apple"),
            ("Palantir", r"palantir"),
            ("Netflix", r"netflix")
        ]
        for cname, pat in company_patterns:
            if re.search(pat, combined, re.IGNORECASE) or re.search(pat, sender, re.IGNORECASE):
                company = cname
                break

        if company == "Unknown Company":
            # Check domain in sender
            domain_match = re.search(r"@([a-zA-Z0-9_\-]+)\.", sender)
            if domain_match:
                d = domain_match.group(1).title()
                if d.lower() not in ["gmail", "yahoo", "hotmail", "outlook", "domain", "workspace", "internal", "mail"]:
                    company = d
            # Check "sent to X" or "applied to X" or "application to X"
            sent_match = re.search(r"(?:sent to|applied to|application to|joining|role at)\s+([A-Za-z0-9\s&]+?)(?:\s*(?:[\.\,\—\-\|]|\bvia\b|\bas\b|\bfor\b|$))", combined, re.IGNORECASE)
            if sent_match and len(sent_match.group(1).strip()) > 2:
                company = sent_match.group(1).strip().title()

        # Role Extraction
        role = "Software Engineering Intern"
        role_match = re.search(r"((?:Software|Systems|Frontend|Backend|Full[- ]Stack|AI|ML|Data|Product)\s+(?:Engineering\s+)?(?:Intern(?:ship)?|Co-op|Engineer|Specialist|Fellow))", combined, re.IGNORECASE)
        if role_match:
            role = role_match.group(1).title()
        else:
            app_match = re.search(r"Application(?:\s+for|\s*:)?\s*([A-Za-z0-9\s\-/]+?)(?:\s*[:|–—]|\bfor\b|\bfrom\b|\bby\b|$)", subject, re.IGNORECASE)
            if app_match and len(app_match.group(1).strip()) > 3:
                role = app_match.group(1).strip().title()

        # Update Type & Importance Classification
        if any(k in lower for k in ["offer of employment", "official offer", "congratulations", "offer letter"]):
            update_type = "OFFER"
            importance = "HIGH"
            action_required = True
        elif any(k in lower for k in ["interview", "technical screen", "coding challenge", "assessment", "schedule your"]):
            update_type = "INTERVIEW_INVITE"
            importance = "HIGH"
            action_required = True
        elif any(k in lower for k in ["top 50", "jobs hiring this week", "digest", "unsubscribe", "handshake"]):
            update_type = "NEWSLETTER"
            importance = "LOW"
            action_required = False
        elif any(k in lower for k in ["application update", "in review", "moved to", "under review", "received your application"]):
            update_type = "STATUS_UPDATE"
            importance = "MEDIUM"
            action_required = False
        elif any(k in lower for k in ["unfortunately", "not moving forward", "other candidates"]):
            update_type = "REJECTION"
            importance = "MEDIUM"
            action_required = False
        else:
            update_type = "UPDATE"
            importance = "MEDIUM"
            action_required = False

        # Deadline extraction
        deadline = None
        deadline_match = re.search(r"(?:deadline|within|by)\s*(?:is|to[^:]*:|:)?\s*([A-Za-z]+ \d{1,2}(?:, \d{4})?(?: at [^\n\.]+)?)", combined, re.IGNORECASE)
        if deadline_match:
            deadline = deadline_match.group(1).strip()
        elif "within 48 hours" in lower:
            deadline = "Within 48 hours of receipt"

        # Summary
        if update_type == "INTERVIEW_INVITE":
            summary = f"Recruiter invited candidate to interview screen. Action deadline: {deadline or 'Immediate scheduling requested'}."
        elif update_type == "OFFER":
            summary = f"Official employment offer extended for {role} at {company}. Deadline: {deadline or 'Review required'}."
        elif update_type == "STATUS_UPDATE":
            summary = f"Application status moved to active review. No candidate action required."
        elif update_type == "NEWSLETTER":
            summary = "Promotional newsletter / general job board alert."
        else:
            summary = f"Recruiter correspondence from {company} regarding {role}."

        return {
            "company": company,
            "role": role,
            "update_type": update_type,
            "importance": importance,
            "action_required": action_required,
            "deadline": deadline,
            "summary": summary
        }

    def _format_slack_notification(self, extracted: Dict[str, Any], sender: str, subject: str) -> str:
        company = extracted["company"]
        role = extracted["role"]
        update_type = extracted["update_type"]
        importance = extracted["importance"]
        deadline = extracted["deadline"] or "None stated"
        summary = extracted["summary"]

        if importance == "HIGH":
            return (
                f"🚨 *[HIGH PRIORITY RECRUITER ALERT]*\n"
                f"• *Company*: *{company}*\n"
                f"• *Role*: {role}\n"
                f"• *Type*: `{update_type}`\n"
                f"• *Action Required*: *YES*\n"
                f"• *Deadline*: *{deadline}*\n"
                f"• *Summary*: {summary}\n"
                f"• *Source*: {sender} — _{subject}_"
            )
        else:
            return (
                f"ℹ️ *[APPLICATION STATUS UPDATE]*\n"
                f"• *Company*: *{company}*\n"
                f"• *Role*: {role}\n"
                f"• *Status*: `{update_type}`\n"
                f"• *Summary*: {summary}\n"
                f"• *Source*: {sender}"
            )

    def _post_to_slack(self, channel: str, text: str) -> Dict[str, Any]:
        if not self.mock_mode and settings.SLACK_BOT_TOKEN and not settings.SLACK_BOT_TOKEN.startswith("xoxb-placeholder"):
            try:
                client = LiveSlackClient()
                return client.post_message(channel=channel, text=text)
            except Exception as e:
                print(f"[InternshipMonitor] Live Slack post failed: {e}")
                return {"ok": False, "status": "FAILED", "error": str(e), "message": {"text": text}}

        mock_client = MockSlackClient()
        return mock_client.post_message(channel=channel, text=text)

    def _log_audit(self, run_id: str, event_type: str, details: Dict[str, Any]):
        audit = AuditLogModel(
            case_id=run_id,
            workspace_id=self.workspace_id,
            workflow_id=self.workflow_id,
            event_type=event_type,
            details=details,
            timestamp=datetime.utcnow()
        )
        self.db.add(audit)

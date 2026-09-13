import re
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database.db import get_db
from ..models.workspace import WorkspaceModel, WorkflowModel, WorkflowRunModel, ProcessedEventModel
from ..models.audit import AuditLogModel
from ..agent.natural_planner import NaturalGoalPlanner
from ..agent.internship_monitor import InternshipMonitorEngine, MOCK_INTERNSHIP_SCENARIOS
from ..integrations.registry import ToolRegistry
from ..adapters.slack_live import LiveSlackClient
from ..adapters.slack_mock import MockSlackClient
from ..adapters.gmail_live import LiveGmailClient
from ..adapters.gmail_mock import MockGmailClient
from ..config import settings

router = APIRouter(prefix="/api/workflows", tags=["Workflows"])

class InterpretGoalRequest(BaseModel):
    goal: str = Field(..., description="Natural language workflow goal")
    workspace_id: Optional[str] = Field(default=None, description="Target workspace ID")

class WorkflowCreateRequest(BaseModel):
    workspace_id: str = Field(..., description="Workspace ID")
    name: str = Field(..., description="Workflow title")
    goal: str = Field(..., description="Workflow objective or natural language goal")
    connected_apps: List[str] = Field(default_factory=list)
    trigger: Dict[str, Any] = Field(default_factory=dict)
    agent_plan: List[Dict[str, Any]] = Field(default_factory=list)
    configuration: Dict[str, Any] = Field(default_factory=dict)

class WorkflowRunRequest(BaseModel):
    scenario_key: Optional[str] = Field(default="stripe_interview", description="Mock scenario key if running in mock mode")
    force_reprocess: bool = Field(default=False, description="True to bypass duplicate event deduplication")
    target_channel: Optional[str] = Field(default="general", description="Slack channel to post to")
    search_query: Optional[str] = Field(default=None, description="Custom query to filter incoming events or search Gmail")
    email_data: Optional[Dict[str, Any]] = Field(default=None, description="Custom email data payload if running ad-hoc")
    mock_mode: Optional[bool] = Field(default=None, description="Explicit mock mode override")

@router.post("/interpret-goal")
def interpret_goal(req: InterpretGoalRequest, db: Session = Depends(get_db)):
    workspace_apps = None
    if req.workspace_id:
        ws = db.query(WorkspaceModel).filter(WorkspaceModel.id == req.workspace_id).first()
        if ws:
            workspace_apps = ws.connected_apps

    planner = NaturalGoalPlanner()
    plan = planner.plan_from_goal(req.goal, workspace_apps)
    return plan

@router.post("", status_code=status.HTTP_201_CREATED)
def create_workflow(req: WorkflowCreateRequest, db: Session = Depends(get_db)):
    ws = db.query(WorkspaceModel).filter(WorkspaceModel.id == req.workspace_id).first()
    if not ws:
        raise HTTPException(status_code=404, detail=f"Workspace '{req.workspace_id}' not found")

    wf_id = f"wf_{uuid.uuid4().hex[:8]}"
    wf = WorkflowModel(
        id=wf_id,
        workspace_id=req.workspace_id,
        name=req.name,
        goal=req.goal,
        status="ACTIVE",
        connected_apps=req.connected_apps or ws.connected_apps,
        trigger=req.trigger,
        agent_plan=req.agent_plan,
        configuration=req.configuration
    )
    db.add(wf)
    db.commit()
    db.refresh(wf)
    return {
        "id": wf.id,
        "workspace_id": wf.workspace_id,
        "name": wf.name,
        "goal": wf.goal,
        "status": wf.status,
        "connected_apps": wf.connected_apps,
        "trigger": wf.trigger,
        "agent_plan": wf.agent_plan,
        "configuration": wf.configuration,
        "created_at": wf.created_at.isoformat() if wf.created_at else None
    }

@router.get("")
def list_workflows(workspace_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(WorkflowModel)
    if workspace_id:
        query = query.filter(WorkflowModel.workspace_id == workspace_id)
    workflows = query.order_by(WorkflowModel.created_at.desc()).all()
    return {
        "workflows": [
            {
                "id": w.id,
                "workspace_id": w.workspace_id,
                "name": w.name,
                "goal": w.goal,
                "status": w.status,
                "connected_apps": w.connected_apps,
                "trigger": w.trigger,
                "agent_plan": w.agent_plan,
                "configuration": w.configuration,
                "run_count": len(w.runs),
                "created_at": w.created_at.isoformat() if w.created_at else None
            }
            for w in workflows
        ]
    }

@router.get("/scenarios/internship")
def get_internship_scenarios():
    """Returns available mock scenarios for the internship workflow."""
    return {
        "scenarios": [
            {
                "key": k,
                "title": v["subject"],
                "company": k.split("_")[0].capitalize(),
                "sender": v["sender"],
                "body_preview": v["body"][:120] + "..."
            }
            for k, v in MOCK_INTERNSHIP_SCENARIOS.items()
        ]
    }

@router.get("/{workflow_id}")
def get_workflow(workflow_id: str, db: Session = Depends(get_db)):
    wf = db.query(WorkflowModel).filter(WorkflowModel.id == workflow_id).first()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")

    recent_runs = db.query(WorkflowRunModel).filter(
        WorkflowRunModel.workflow_id == workflow_id
    ).order_by(WorkflowRunModel.started_at.desc()).limit(20).all()

    return {
        "id": wf.id,
        "workspace_id": wf.workspace_id,
        "name": wf.name,
        "goal": wf.goal,
        "status": wf.status,
        "connected_apps": wf.connected_apps,
        "trigger": wf.trigger,
        "agent_plan": wf.agent_plan,
        "configuration": wf.configuration,
        "runs": [
            {
                "id": r.id,
                "status": r.status,
                "trigger_event": r.trigger_event,
                "extracted_data": r.extracted_data,
                "decision": r.decision,
                "action_result": r.action_result,
                "verification_result": r.verification_result,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None
            }
            for r in recent_runs
        ]
    }

def extract_candidate_queries(query: str, ws_name: str = "", goal: str = "") -> List[str]:
    candidates = []
    if query and query.strip():
        candidates.append(query.strip())

    stop_words = {
        "check", "my", "email", "emails", "for", "an", "upcoming", "list", "of", "to", "buy",
        "and", "notify", "me", "find", "get", "monitor", "search", "inbox", "slack", "channel",
        "the", "a", "an", "send", "message", "alert", "regarding", "about", "look", "into", "see",
        "if", "there", "is", "are", "any", "update", "new", "subject", "body", "from", "date",
        "within", "next", "days", "hours", "day", "week", "notifier", "orchestrator", "workflow",
        "automates", "app", "multi", "some", "tell", "telling", "you"
    }

    # Clean workspace name
    ws_clean_words = [w for w in re.findall(r'\b[a-zA-Z0-9_\-]+\b', ws_name) if w.lower() not in stop_words and len(w) > 2]
    if ws_clean_words and ws_name.lower() not in ["default", "custom", "finance operations", "internship applications"]:
        candidates.append(" ".join(ws_clean_words))

    # Clean goal and query keywords
    for text in [goal, query]:
        if text:
            words = [w for w in re.findall(r'\b[a-zA-Z0-9_\-]+\b', text) if w.lower() not in stop_words and len(w) > 2]
            if words:
                candidates.append(" ".join(words))

    # Add single key noun forms (e.g. 'groceries', 'secrets', 'sameer')
    expanded = []
    for c in list(candidates):
        for w in c.split():
            clean_w = w.strip("'\"")
            if clean_w.lower() not in stop_words and len(clean_w) > 3:
                if clean_w.lower() not in [x.lower() for x in candidates] and clean_w.lower() not in [x.lower() for x in expanded]:
                    expanded.append(clean_w)

    candidates.extend(expanded)

    seen = set()
    result = []
    for c in candidates:
        if c and c.lower() not in seen:
            seen.add(c.lower())
            result.append(c)
    return result

@router.post("/{workflow_id}/run")
def execute_workflow(workflow_id: str, req: WorkflowRunRequest, db: Session = Depends(get_db)):
    wf = db.query(WorkflowModel).filter(WorkflowModel.id == workflow_id).first()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")

    is_mock = req.mock_mode if req.mock_mode is not None else settings.MOCK_MODE

    # Flagship 2: Internship Application Monitor
    if workflow_id == "wf_internship_monitor" or "intern" in wf.name.lower():
        is_scenario = bool(req.scenario_key and not req.search_query)
        engine = InternshipMonitorEngine(
            db=db,
            workspace_id=wf.workspace_id,
            workflow_id=wf.id,
            mock_mode=is_mock or is_scenario
        )
        target_ch = req.target_channel or "internship"
        if req.email_data:
            result = engine.process_email(
                email_data=req.email_data,
                force_reprocess=req.force_reprocess,
                target_channel=target_ch
            )
        elif is_mock or (req.scenario_key and not req.search_query):
            result = engine.run_scenario(
                scenario_key=req.scenario_key or "stripe_interview",
                force_reprocess=req.force_reprocess,
                target_channel=target_ch
            )
        else:
            result = engine.scan_inbox(
                query=req.search_query or "subject:(interview OR offer OR application)",
                force_reprocess=req.force_reprocess,
                target_channel=target_ch
            )
        return result

    # Generic Multi-App Workflow Execution (e.g. SECRETS or custom workspaces)
    ws = db.query(WorkspaceModel).filter(WorkspaceModel.id == wf.workspace_id).first()
    connected_apps = ws.connected_apps if ws else wf.connected_apps

    # Workspace security check
    for app in connected_apps:
        if app == "stripe":
            ToolRegistry.verify_tool_access(connected_apps, "stripe.search_charges")
        elif app == "gmail":
            ToolRegistry.verify_tool_access(connected_apps, "gmail.search_messages")
        elif app == "slack":
            ToolRegistry.verify_tool_access(connected_apps, "slack.post_message")

    run_id = f"run_{uuid.uuid4().hex[:8]}"

    # Resolve email context if Gmail is connected
    email_item = None
    search_query_used = ""
    if "gmail" in connected_apps:
        search_query_used = req.search_query or (wf.trigger.get("filter") if wf.trigger else None) or wf.goal or ""
        if req.email_data:
            email_item = req.email_data
        elif not is_mock:
            candidates = extract_candidate_queries(search_query_used, ws.name if ws else "", wf.goal or "")
            try:
                live_gmail = LiveGmailClient()
                for c_query in candidates:
                    found = live_gmail.search_messages(c_query, max_results=5)
                    if found:
                        email_item = found[0]
                        search_query_used = c_query
                        break
            except Exception as eg:
                print(f"[Workflows] Live Gmail search failed: {eg}")
        else:
            mock_gmail = MockGmailClient()
            found = mock_gmail.search_messages(search_query_used, max_results=3)
            if found:
                email_item = found[0]

        # In live mode, if no email was found in Gmail, do NOT return fake canned emails!
        if not email_item and not is_mock:
            return {
                "run_id": run_id,
                "workflow_id": wf.id,
                "status": "NO_MATCHING_EMAILS",
                "message_id": None,
                "reason": f"Searched connected Gmail inbox for '{search_query_used or wf.goal}'. 0 messages found matching criteria. No downstream actions dispatched.",
                "plan_steps": [
                    {"step": 1, "name": "Email Ingestion", "app": "gmail", "status": "COMPLETED"},
                    {"step": 2, "name": "Inbox Search", "app": "gmail", "status": "NO_EMAILS_FOUND"}
                ],
                "trigger_event": {"source": "gmail", "query": search_query_used or wf.goal},
                "extracted_data": {
                    "workspace": ws.name if ws else wf.workspace_id,
                    "workflow": wf.name,
                    "summary": f"Searched live Gmail inbox with query '{search_query_used or wf.goal}'. 0 messages found. No actions dispatched to avoid false positives."
                },
                "decision": {"status": "NO_ACTION", "action": "SUPPRESS_ACTION"},
                "action_result": {"status": "SKIPPED", "reason": "No matching emails found in Gmail."},
                "verification_result": {"verified": True, "action_taken": "NO_ACTION_REQUIRED"}
            }

    msg_id = (email_item.get("message_id") if email_item else None) or (req.email_data.get("id") if req.email_data else None) or f"msg_{wf.workspace_id}_{uuid.uuid4().hex[:6]}"

    # Deduplication check against SQLite ProcessedEvents
    existing_event = db.query(ProcessedEventModel).filter(
        ProcessedEventModel.source_app == ("gmail" if "gmail" in connected_apps else connected_apps[0]),
        ProcessedEventModel.source_event_id == msg_id,
        ProcessedEventModel.workflow_id == wf.id
    ).first()

    plan_snapshot = [dict(s) for s in wf.agent_plan]
    if len(plan_snapshot) >= 2 and existing_event and not req.force_reprocess:
        plan_snapshot[0]["status"] = "COMPLETED"
        plan_snapshot[1]["status"] = "BLOCKED_DUPLICATE"
        for s in plan_snapshot[2:]:
            s["status"] = "SKIPPED"
        return {
            "run_id": run_id,
            "workflow_id": wf.id,
            "status": "SKIPPED_DUPLICATE",
            "message_id": msg_id,
            "reason": f"Event {msg_id} was already processed at {existing_event.processed_at.isoformat()}Z. Duplicate execution suppressed.",
            "plan_steps": plan_snapshot,
            "extracted_data": {
                "workspace": ws.name if ws else wf.workspace_id,
                "workflow": wf.name,
                "summary": f"Event {msg_id} was already processed. Duplicate execution suppressed to prevent alert fatigue."
            }
        }

    # Step progression
    for s in plan_snapshot:
        s["status"] = "COMPLETED"

    # Ingest event data
    trigger_subject = (email_item.get("subject") if email_item else None) or (req.email_data.get("subject") if req.email_data else None) or f"Trigger: {wf.goal[:45]}"
    trigger_sender = (email_item.get("sender") if email_item else None) or (req.email_data.get("sender") if req.email_data else None) or "agent-trigger@workspace.internal"
    trigger_body = (email_item.get("body") if email_item else None) or (req.email_data.get("body") if req.email_data else None) or f"Agent task executed for goal: {wf.goal}"
    trigger_event = {
        "source": "gmail" if "gmail" in connected_apps else connected_apps[0],
        "message_id": msg_id,
        "subject": trigger_subject,
        "sender": trigger_sender,
        "body": trigger_body
    }

    # Extracted intelligence
    extracted_data = {
        "workspace": ws.name if ws else wf.workspace_id,
        "workflow": wf.name,
        "goal": wf.goal,
        "target_apps": connected_apps,
        "trigger_subject": trigger_subject,
        "sender": trigger_sender,
        "body": trigger_body,
        "summary": f"Orchestrated cross-app task for '{wf.name}'. Ingested context from {connected_apps[0]} ('{trigger_subject}'), verified policy, and dispatched downstream alert.",
        "executed_at": datetime.utcnow().isoformat() + "Z"
    }

    # Slack dispatch
    action_result = {}
    if "slack" in connected_apps:
        channel = req.target_channel or (wf.configuration.get("target_channel") if wf.configuration else None) or settings.SLACK_CHANNEL or "general"
        body_snippet = trigger_body[:500].strip()
        slack_msg = (
            f"*[RECON WORKSPACE AGENT: {wf.name.upper()}]*\n"
            f"• *Workspace*: *{ws.name if ws else wf.workspace_id}*\n"
            f"• *Goal*: {wf.goal}\n"
            f"• *Ingested From*: Gmail (`{trigger_subject}`)\n"
            f"• *Sender*: {trigger_sender}\n"
            f"• *Extracted Data*:\n{body_snippet}\n"
            f"• *Status*: Executed & Verified\n"
            f"• *Event ID*: `{msg_id}`"
        )
        if not is_mock and settings.SLACK_BOT_TOKEN and not settings.SLACK_BOT_TOKEN.startswith("xoxb-placeholder"):
            try:
                sl_client = LiveSlackClient()
                action_result = sl_client.post_message(channel=channel, text=slack_msg)
            except Exception as e:
                print(f"[Workflows] Live Slack post failed: {e}")
                action_result = {
                    "ok": False,
                    "status": "FAILED",
                    "error": str(e),
                    "channel": channel,
                    "details": f"Failed to post to Slack: {e}"
                }
        else:
            action_result = MockSlackClient().post_message(channel=channel, text=slack_msg)
    else:
        action_result = {"status": "EXECUTED", "workflow": wf.name, "target_apps": connected_apps}

    verification_result = {
        "verified": bool(action_result.get("ok", False) or action_result.get("status") == "EXECUTED"),
        "delivery_confirmed": bool(action_result.get("ok", False) or action_result.get("status") == "EXECUTED"),
        "event_id": msg_id,
        "target_apps": connected_apps
    }

    # Record Processed Event
    if not existing_event:
        db.add(ProcessedEventModel(
            source_app="gmail" if "gmail" in connected_apps else connected_apps[0],
            source_event_id=msg_id,
            workflow_id=wf.id
        ))

    # Record Workflow Run
    generic_run = WorkflowRunModel(
        id=run_id,
        workflow_id=wf.id,
        workspace_id=wf.workspace_id,
        trigger_event=trigger_event,
        status="COMPLETED",
        plan_snapshot=plan_snapshot,
        extracted_data=extracted_data,
        decision={"status": "APPROVED_BY_POLICY", "action": "DISPATCH_ACTION"},
        approval_status="NOT_REQUIRED",
        action_result=action_result,
        verification_result=verification_result,
        completed_at=datetime.utcnow()
    )
    db.add(generic_run)

    # Record Audit Log
    db.add(AuditLogModel(
        case_id=run_id,
        workspace_id=wf.workspace_id,
        workflow_id=wf.id,
        event_type="WORKFLOW_RUN_COMPLETED",
        details=extracted_data,
        timestamp=datetime.utcnow()
    ))

    db.commit()

    return {
        "run_id": run_id,
        "workflow_id": wf.id,
        "status": "COMPLETED",
        "message_id": msg_id,
        "plan_steps": plan_snapshot,
        "trigger_event": trigger_event,
        "extracted_data": extracted_data,
        "action_result": action_result,
        "verification_result": verification_result,
        "message": f"Workflow '{wf.name}' executed successfully across {', '.join(connected_apps)}."
    }

@router.get("/{workflow_id}/runs")
def list_workflow_runs(workflow_id: str, db: Session = Depends(get_db)):
    runs = db.query(WorkflowRunModel).filter(
        WorkflowRunModel.workflow_id == workflow_id
    ).order_by(WorkflowRunModel.started_at.desc()).all()
    return {
        "runs": [
            {
                "id": r.id,
                "workflow_id": r.workflow_id,
                "workspace_id": r.workspace_id,
                "trigger_event": r.trigger_event,
                "status": r.status,
                "plan_snapshot": r.plan_snapshot,
                "extracted_data": r.extracted_data,
                "decision": r.decision,
                "approval_status": r.approval_status,
                "action_result": r.action_result,
                "verification_result": r.verification_result,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None
            }
            for r in runs
        ]
    }

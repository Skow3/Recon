import uuid
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database.db import get_db
from ..models.workspace import WorkspaceModel, WorkflowModel, WorkflowRunModel, ProcessedEventModel
from ..integrations.registry import ToolRegistry
from ..agent.natural_planner import NaturalGoalPlanner

router = APIRouter(prefix="/api/workspaces", tags=["Workspaces"])

class WorkspaceCreateRequest(BaseModel):
    name: str = Field(..., description="Workspace title, e.g. Finance Operations")
    description: Optional[str] = Field(default="", description="Workspace operational purpose")
    connected_apps: List[str] = Field(default_factory=list, description="List of connected app IDs, e.g. ['gmail', 'slack']")
    agent_instructions: Optional[str] = Field(default="", description="Workspace-level system instructions for the agent")
    permissions: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Permission matrix for connected apps")
    plan: Optional[Dict[str, Any]] = Field(default=None, description="Pre-computed workflow plan if already analyzed")
    workflow_name: Optional[str] = Field(default=None, description="Optional workflow title")
    target_channel: Optional[str] = Field(default=None, description="Destination Slack channel")

class WorkspaceUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    connected_apps: Optional[List[str]] = None
    agent_instructions: Optional[str] = None
    permissions: Optional[Dict[str, Any]] = None

def ensure_default_workspaces(db: Session):
    """Pre-seeds default flagship workspaces if they do not exist."""
    try:
        finance_ws = db.query(WorkspaceModel).filter(WorkspaceModel.id == "ws_finance").first()
        if not finance_ws:
            finance_ws = WorkspaceModel(
                id="ws_finance",
                name="Finance Operations",
                description="Enterprise billing dispute investigation, cross-system reconciliation across Stripe & Gmail, and gated refund execution.",
                connected_apps=["gmail", "stripe", "slack"],
                agent_instructions="Reconcile billing disputes across Gmail, Stripe ledger, and Slack #billing. Always enforce human approval before issuing refunds.",
                permissions={
                    "gmail": {"read_emails": True},
                    "stripe": {"search_charges": True, "create_refunds": "APPROVAL_REQUIRED"},
                    "slack": {"search_messages": True, "post_messages": True}
                }
            )
            db.add(finance_ws)

            # Pre-seed billing workflow
            planner = NaturalGoalPlanner()
            b_plan = planner.plan_from_goal("Investigate duplicate billing disputes across Gmail, Stripe, and Slack")
            wf_billing = WorkflowModel(
                id="wf_billing_investigator",
                workspace_id="ws_finance",
                name="Billing Dispute Investigator",
                goal=b_plan["description"],
                status="ACTIVE",
                connected_apps=["gmail", "stripe", "slack"],
                trigger=b_plan["trigger"],
                agent_plan=b_plan["plan_steps"],
                configuration={"require_human_approval": True, "max_refund_limit": 1000.0}
            )
            db.add(wf_billing)
            db.commit()

        intern_ws = db.query(WorkspaceModel).filter(WorkspaceModel.id == "ws_internships").first()
        if not intern_ws:
            intern_ws = WorkspaceModel(
                id="ws_internships",
                name="Internship Applications",
                description="Recruiter inbox monitoring, interview schedule and offer letter extraction, noise filtering, and structured Slack delivery.",
                connected_apps=["gmail", "slack"],
                agent_instructions="Scan Gmail for internship and recruiter correspondence. Extract interview schedules, offers, and deadlines. Filter out newsletters and marketing spam. Deliver structured alerts to Slack in #internships.",
                permissions={
                    "gmail": {"read_emails": True},
                    "slack": {"post_messages": True}
                }
            )
            db.add(intern_ws)

            # Pre-seed internship workflow
            planner = NaturalGoalPlanner()
            i_plan = planner.plan_from_goal("Monitor my Gmail for internship replies, reject spam, extract interview deadlines, and notify me in #internships on Slack")
            wf_intern = WorkflowModel(
                id="wf_internship_monitor",
                workspace_id="ws_internships",
                name="Internship Application Monitor",
                goal=i_plan["description"],
                status="ACTIVE",
                connected_apps=["gmail", "slack"],
                trigger=i_plan["trigger"],
                agent_plan=i_plan["plan_steps"],
                configuration={"target_channel": "internships", "noise_suppression": True}
            )
            db.add(wf_intern)
            db.commit()
    except Exception as e:
        db.rollback()

@router.get("")
def list_workspaces(db: Session = Depends(get_db)):
    ensure_default_workspaces(db)
    workspaces = db.query(WorkspaceModel).order_by(WorkspaceModel.created_at.asc()).all()
    results = []
    for ws in workspaces:
        tools = ToolRegistry.get_available_tools(ws.connected_apps, ws.permissions)
        results.append({
            "id": ws.id,
            "name": ws.name,
            "description": ws.description,
            "connected_apps": ws.connected_apps,
            "agent_instructions": ws.agent_instructions,
            "permissions": ws.permissions,
            "workflow_count": len(ws.workflows),
            "available_tools": [t.dict() for t in tools],
            "created_at": ws.created_at.isoformat() if ws.created_at else None,
            "updated_at": ws.updated_at.isoformat() if ws.updated_at else None
        })
    return {"workspaces": results}

@router.post("", status_code=status.HTTP_201_CREATED)
def create_workspace(req: WorkspaceCreateRequest, db: Session = Depends(get_db)):
    try:
        ws_id = f"ws_{uuid.uuid4().hex[:8]}"
        ws = WorkspaceModel(
            id=ws_id,
            name=req.name,
            description=req.description,
            connected_apps=req.connected_apps,
            agent_instructions=req.agent_instructions,
            permissions=req.permissions
        )
        db.add(ws)

        # Use pre-computed plan if provided, avoiding redundant slow planning calls
        if req.plan and isinstance(req.plan, dict) and req.plan.get("plan_steps"):
            plan = req.plan
        else:
            planner = NaturalGoalPlanner()
            goal = req.description or req.agent_instructions or f"Automate workflows for {req.name}"
            plan = planner.plan_from_goal(goal, req.connected_apps)

        wf_id = f"wf_{uuid.uuid4().hex[:8]}"
        target_ch = req.target_channel or plan.get("suggested_channel") or "general"
        wf = WorkflowModel(
            id=wf_id,
            workspace_id=ws_id,
            name=req.workflow_name or plan.get("workflow_name", f"{req.name} Orchestrator"),
            goal=plan.get("description", req.description or f"Automate workflows for {req.name}"),
            status="ACTIVE",
            connected_apps=req.connected_apps,
            trigger=plan.get("trigger", {"app": req.connected_apps[0] if req.connected_apps else "gmail", "event": "event_detected"}),
            agent_plan=plan.get("plan_steps", []),
            configuration={"target_channel": target_ch}
        )
        db.add(wf)
        db.commit()
        db.refresh(ws)

        tools = ToolRegistry.get_available_tools(ws.connected_apps, ws.permissions)
        return {
            "id": ws.id,
            "name": ws.name,
            "description": ws.description,
            "connected_apps": ws.connected_apps,
            "agent_instructions": ws.agent_instructions,
            "permissions": ws.permissions,
            "workflow_id": wf.id,
            "available_tools": [t.dict() for t in tools]
        }
    except Exception as e:
        db.rollback()
        print(f"[Workspaces] Error creating workspace: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create workspace: {str(e)}")

@router.get("/{workspace_id}")
def get_workspace(workspace_id: str, db: Session = Depends(get_db)):
    ensure_default_workspaces(db)
    ws = db.query(WorkspaceModel).filter(WorkspaceModel.id == workspace_id).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    tools = ToolRegistry.get_available_tools(ws.connected_apps, ws.permissions)
    workflows = db.query(WorkflowModel).filter(WorkflowModel.workspace_id == workspace_id).all()

    if not workflows:
        planner = NaturalGoalPlanner()
        goal = ws.description or ws.agent_instructions or f"Automate workflows for {ws.name}"
        plan = planner.plan_from_goal(goal, ws.connected_apps)
        wf_id = f"wf_{uuid.uuid4().hex[:8]}"
        wf = WorkflowModel(
            id=wf_id,
            workspace_id=ws.id,
            name=plan.get("workflow_name", f"{ws.name} Orchestrator"),
            goal=plan.get("description", goal),
            status="ACTIVE",
            connected_apps=ws.connected_apps,
            trigger=plan.get("trigger", {"app": ws.connected_apps[0] if ws.connected_apps else "gmail", "event": "event_detected"}),
            agent_plan=plan.get("plan_steps", []),
            configuration={}
        )
        db.add(wf)
        db.commit()
        workflows = [wf]

    return {
        "id": ws.id,
        "name": ws.name,
        "description": ws.description,
        "connected_apps": ws.connected_apps,
        "agent_instructions": ws.agent_instructions,
        "permissions": ws.permissions,
        "available_tools": [t.dict() for t in tools],
        "workflows": [
            {
                "id": w.id,
                "name": w.name,
                "goal": w.goal,
                "status": w.status,
                "connected_apps": w.connected_apps,
                "trigger": w.trigger,
                "agent_plan": w.agent_plan,
                "configuration": w.configuration
            }
            for w in workflows
        ],
        "created_at": ws.created_at.isoformat() if ws.created_at else None
    }

@router.put("/{workspace_id}")
def update_workspace(workspace_id: str, req: WorkspaceUpdateRequest, db: Session = Depends(get_db)):
    ws = db.query(WorkspaceModel).filter(WorkspaceModel.id == workspace_id).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    if req.name is not None:
        ws.name = req.name
    if req.description is not None:
        ws.description = req.description
    if req.connected_apps is not None:
        ws.connected_apps = req.connected_apps
    if req.agent_instructions is not None:
        ws.agent_instructions = req.agent_instructions
    if req.permissions is not None:
        ws.permissions = req.permissions

    db.commit()
    db.refresh(ws)

    tools = ToolRegistry.get_available_tools(ws.connected_apps, ws.permissions)
    return {
        "id": ws.id,
        "name": ws.name,
        "description": ws.description,
        "connected_apps": ws.connected_apps,
        "agent_instructions": ws.agent_instructions,
        "permissions": ws.permissions,
        "available_tools": [t.dict() for t in tools]
    }

@router.delete("/{workspace_id}")
def delete_workspace(workspace_id: str, db: Session = Depends(get_db)):
    if workspace_id in ["ws_finance", "ws_internships"]:
        raise HTTPException(status_code=400, detail="Cannot delete default flagship workspaces")

    ws = db.query(WorkspaceModel).filter(WorkspaceModel.id == workspace_id).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Clean up associated processed events for workflows in this workspace
    workflow_ids = [w.id for w in ws.workflows] if ws.workflows else []
    if workflow_ids:
        db.query(ProcessedEventModel).filter(ProcessedEventModel.workflow_id.in_(workflow_ids)).delete(synchronize_session=False)

    db.delete(ws)
    db.commit()
    return {"deleted": True, "workspace_id": workspace_id}

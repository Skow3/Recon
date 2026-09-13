from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database.db import get_db
from ..models.case import CaseModel, ApprovalModel, ActionModel, VerificationModel
from ..models.evidence import EvidenceModel, DecisionModel
from ..models.audit import ToolRunModel, AuditLogModel
from ..schemas.requests import CaseCreateRequest, ApprovalRequest
from ..schemas.responses import CaseDetailResponse, ToolTraceItem, CaseStatus
from ..agent.orchestrator import AgentOrchestrator
from ..evaluation.scenarios import EVALUATION_SCENARIOS

router = APIRouter(prefix="/api/cases", tags=["cases"])

def _build_case_detail(case: CaseModel, db: Session) -> Dict[str, Any]:
    # Evidence
    evidence_records = db.query(EvidenceModel).filter(EvidenceModel.case_id == case.id).all()
    evidence_list = [
        {
            "id": ev.id,
            "source": ev.source,
            "evidence_type": ev.evidence_type,
            "payload": ev.payload,
            "collected_at": ev.collected_at.isoformat() + "Z"
        }
        for ev in evidence_records
    ]

    # Reconciler view reconstruction from evidence
    gmail_items = [e["payload"] for e in evidence_list if e["source"] == "gmail"]
    stripe_charges = [e["payload"] for e in evidence_list if e["source"] == "stripe" and e["evidence_type"] == "charge"]
    stripe_refunds = [e["payload"] for e in evidence_list if e["source"] == "stripe" and e["evidence_type"] == "refund"]
    slack_items = [e["payload"] for e in evidence_list if e["source"] == "slack"]

    reconciliation_obj = None
    if evidence_records:
        from ..agent.reconciler import EvidenceReconciler
        recon = EvidenceReconciler()
        reconciliation_obj = recon.reconcile(gmail_items, stripe_charges, stripe_refunds, slack_items)

    # Decision
    decision_record = db.query(DecisionModel).filter(DecisionModel.case_id == case.id).first()
    decision_dict = None
    if decision_record:
        decision_dict = {
            "decision": decision_record.decision,
            "confidence": decision_record.confidence,
            "reason": decision_record.reason,
            "supporting_evidence": decision_record.supporting_evidence or [],
            "risk_flags": decision_record.risk_flags or []
        }

    # Approval
    approval_record = db.query(ApprovalModel).filter(ApprovalModel.case_id == case.id).first()
    approval_dict = None
    if approval_record:
        approval_dict = {
            "approved": approval_record.approved,
            "approved_by": approval_record.approved_by,
            "approved_at": approval_record.approved_at.isoformat() + "Z",
            "notes": approval_record.notes
        }

    # Action
    action_record = db.query(ActionModel).filter(ActionModel.case_id == case.id).first()
    action_dict = None
    if action_record:
        action_dict = {
            "action_type": action_record.action_type,
            "charge_id": action_record.charge_id,
            "refund_id": action_record.refund_id,
            "amount": action_record.amount,
            "currency": action_record.currency,
            "status": action_record.status,
            "executed_at": action_record.executed_at.isoformat() + "Z"
        }

    # Verification
    ver_record = db.query(VerificationModel).filter(VerificationModel.case_id == case.id).first()
    ver_dict = None
    if ver_record:
        ver_dict = {
            "refund_id": ver_record.refund_id,
            "charge_id": ver_record.charge_id,
            "amount": ver_record.amount,
            "status": ver_record.status,
            "verified": ver_record.verified
        }

    # Safety check status snapshot
    safety_check = None
    safety_tool_run = db.query(ToolRunModel).filter(
        ToolRunModel.case_id == case.id,
        ToolRunModel.tool_name == "deterministic_safety_engine"
    ).order_by(ToolRunModel.timestamp.desc()).first()

    if safety_tool_run:
        safety_check = {
            "allowed": safety_tool_run.status == "success",
            "reason": safety_tool_run.error_message or "Deterministic safety validation passed."
        }

    return {
        "id": case.id,
        "user_request": case.user_request,
        "customer_name": case.customer_name,
        "customer_email": case.customer_email,
        "scenario_id": case.scenario_id,
        "status": case.status,
        "created_at": case.created_at.isoformat() + "Z",
        "updated_at": case.updated_at.isoformat() + "Z",
        "evidence": evidence_list,
        "reconciliation": reconciliation_obj.model_dump() if reconciliation_obj else None,
        "decision": decision_dict,
        "safety_check": safety_check,
        "approval": approval_dict,
        "action": action_dict,
        "verification": ver_dict,
    }

@router.post("", response_model=Dict[str, Any])
def create_case(req: CaseCreateRequest, db: Session = Depends(get_db)):
    orchestrator = AgentOrchestrator(db=db, scenario=req.scenario_id)
    case = orchestrator.create_case(
        user_request=req.user_request,
        customer_name=req.customer_name,
        customer_email=req.customer_email,
        scenario_id=req.scenario_id
    )
    return _build_case_detail(case, db)

@router.get("", response_model=List[Dict[str, Any]])
def list_cases(db: Session = Depends(get_db), limit: int = 50):
    cases = db.query(CaseModel).order_by(CaseModel.created_at.desc()).limit(limit).all()
    return [_build_case_detail(c, db) for c in cases]

@router.get("/{case_id}", response_model=Dict[str, Any])
def get_case(case_id: str, db: Session = Depends(get_db)):
    case = db.query(CaseModel).filter(CaseModel.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
    return _build_case_detail(case, db)

@router.post("/{case_id}/investigate", response_model=Dict[str, Any])
def start_investigation(case_id: str, db: Session = Depends(get_db)):
    orchestrator = AgentOrchestrator(db=db)
    try:
        case = orchestrator.run_investigation(case_id)
        return _build_case_detail(case, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{case_id}/approve", response_model=Dict[str, Any])
def approve_refund(case_id: str, req: ApprovalRequest, db: Session = Depends(get_db)):
    orchestrator = AgentOrchestrator(db=db)
    try:
        case = orchestrator.record_human_approval(
            case_id=case_id,
            approved=req.approved,
            approved_by=req.approved_by,
            notes=req.notes
        )
        return _build_case_detail(case, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{case_id}/reject", response_model=Dict[str, Any])
def reject_refund(case_id: str, notes: Optional[str] = None, db: Session = Depends(get_db)):
    orchestrator = AgentOrchestrator(db=db)
    try:
        case = orchestrator.record_human_approval(
            case_id=case_id,
            approved=False,
            approved_by="human",
            notes=notes or "Manually rejected in dashboard"
        )
        return _build_case_detail(case, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{case_id}/execute", response_model=Dict[str, Any])
def execute_refund(case_id: str, db: Session = Depends(get_db)):
    orchestrator = AgentOrchestrator(db=db)
    try:
        res = orchestrator.execute_approved_action(case_id)
        case = db.query(CaseModel).filter(CaseModel.id == case_id).first()
        detail = _build_case_detail(case, db)
        detail["execution_result"] = res
        return detail
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{case_id}/verify", response_model=Dict[str, Any])
def verify_refund(case_id: str, db: Session = Depends(get_db)):
    action = db.query(ActionModel).filter(ActionModel.case_id == case_id).first()
    if not action or not action.refund_id:
        raise HTTPException(status_code=400, detail="No executed action found to verify")
    
    orchestrator = AgentOrchestrator(db=db)
    res = orchestrator.verify_post_action(case_id, action.refund_id, action.charge_id, action.amount)
    case = db.query(CaseModel).filter(CaseModel.id == case_id).first()
    detail = _build_case_detail(case, db)
    detail["verification_result"] = res
    return detail

@router.get("/{case_id}/trace", response_model=List[Dict[str, Any]])
def get_case_trace(case_id: str, db: Session = Depends(get_db)):
    runs = db.query(ToolRunModel).filter(ToolRunModel.case_id == case_id).order_by(ToolRunModel.timestamp.asc()).all()
    return [
        {
            "id": r.id,
            "tool": r.tool_name,
            "status": r.status,
            "duration_ms": r.duration_ms,
            "error": r.error_message,
            "timestamp": r.timestamp.isoformat() + "Z"
        }
        for r in runs
    ]

@router.get("/{case_id}/audit", response_model=List[Dict[str, Any]])
def get_case_audit(case_id: str, db: Session = Depends(get_db)):
    logs = db.query(AuditLogModel).filter(AuditLogModel.case_id == case_id).order_by(AuditLogModel.timestamp.asc()).all()
    return [
        {
            "id": log.id,
            "event_type": log.event_type,
            "state_from": log.state_from,
            "state_to": log.state_to,
            "details": log.details,
            "timestamp": log.timestamp.isoformat() + "Z"
        }
        for log in logs
    ]

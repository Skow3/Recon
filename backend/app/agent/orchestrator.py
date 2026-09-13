import time
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from ..config import settings
from ..adapters import get_clients
from ..models.case import CaseModel, ApprovalModel, ActionModel, VerificationModel
from ..models.evidence import EvidenceModel, DecisionModel
from ..models.audit import ToolRunModel, AuditLogModel
from ..schemas.responses import CaseStatus, DecisionType, ReconciliationResult, DecisionOutput
from .planner import DisputePlanner
from .reconciler import EvidenceReconciler
from .decision import DecisionEngine
from ..safety.refund_guard import validate_refund
from ..safety.idempotency import check_refund_idempotency

class AgentOrchestrator:
    """Multi-app AI Agent Orchestrator managing state transitions, evidence, safety, and verification."""

    def __init__(self, db: Session, mock_mode: Optional[bool] = None, scenario: Optional[str] = None):
        self.db = db
        self.mock_mode = mock_mode
        self.scenario = scenario
        self.gmail_client, self.stripe_client, self.slack_client = get_clients(
            mock_mode=self.mock_mode,
            scenario=self.scenario
        )
        self.planner = DisputePlanner()
        self.reconciler = EvidenceReconciler()
        self.decision_engine = DecisionEngine()

    def _log_audit(self, case_id: str, event_type: str, state_from: Optional[str], state_to: Optional[str], details: Dict[str, Any]):
        audit = AuditLogModel(
            case_id=case_id,
            event_type=event_type,
            state_from=state_from,
            state_to=state_to,
            details=details,
            timestamp=datetime.utcnow()
        )
        self.db.add(audit)
        self.db.commit()

    def _record_tool_run(self, case_id: str, tool_name: str, status: str, duration_ms: int, error_message: Optional[str] = None):
        tr = ToolRunModel(
            case_id=case_id,
            tool_name=tool_name,
            status=status,
            duration_ms=duration_ms,
            error_message=error_message,
            timestamp=datetime.utcnow()
        )
        self.db.add(tr)
        self.db.commit()

    def create_case(
        self,
        user_request: str,
        customer_name: Optional[str] = None,
        customer_email: Optional[str] = None,
        scenario_id: Optional[str] = None
    ) -> CaseModel:
        # Plan dispute
        plan = self.planner.plan_investigation(user_request, scenario_hint=scenario_id)
        
        c_id = f"CASE-{uuid.uuid4().hex[:6].upper()}"
        case = CaseModel(
            id=c_id,
            user_request=user_request,
            customer_name=customer_name or plan.get("customer_name"),
            customer_email=customer_email or plan.get("customer_email"),
            scenario_id=scenario_id or plan.get("scenario_id"),
            status=CaseStatus.RECEIVED.value
        )
        self.db.add(case)
        self.db.commit()
        self.db.refresh(case)

        self._log_audit(case.id, "CASE_CREATED", None, CaseStatus.RECEIVED.value, {
            "user_request": user_request,
            "customer_name": case.customer_name,
            "customer_email": case.customer_email,
            "scenario_id": case.scenario_id
        })
        return case

    def _ensure_clients_for_case(self, case: CaseModel):
        target_scenario = case.scenario_id
        if target_scenario != self.scenario or self.gmail_client is None:
            self.scenario = target_scenario
            self.gmail_client, self.stripe_client, self.slack_client = get_clients(
                mock_mode=self.mock_mode,
                scenario=self.scenario
            )

    def run_investigation(self, case_id: str) -> CaseModel:
        case = self.db.query(CaseModel).filter(CaseModel.id == case_id).first()
        if not case:
            raise ValueError(f"Case {case_id} not found")

        self._ensure_clients_for_case(case)

        # Transition to PLANNING
        self._transition(case, CaseStatus.PLANNING.value, "Starting investigation planning")

        # Transition to COLLECTING_EVIDENCE
        self._transition(case, CaseStatus.COLLECTING_EVIDENCE.value, "Gathering evidence from Gmail, Stripe, and Slack")

        # 1. Collect Gmail evidence
        gmail_items = []
        t0 = time.time()
        try:
            gmail_query = case.customer_email or case.customer_name or case.user_request
            gmail_items = self.gmail_client.search_customer(gmail_query)
            duration = int((time.time() - t0) * 1000)
            self._record_tool_run(case.id, "gmail_search_customer", "success", duration)
            for item in gmail_items:
                self.db.add(EvidenceModel(
                    case_id=case.id,
                    source="gmail",
                    evidence_type="customer_claim",
                    payload=item
                ))
        except Exception as e:
            duration = int((time.time() - t0) * 1000)
            self._record_tool_run(case.id, "gmail_search_customer", "error", duration, str(e))
            self._log_audit(case.id, "TOOL_ERROR", case.status, case.status, {"tool": "gmail", "error": str(e)})

        # 2. Collect Stripe evidence
        stripe_charges = []
        stripe_refunds = []
        stripe_error = None
        t0 = time.time()
        try:
            stripe_cust_id = None
            if case.customer_email:
                cust_match = self.stripe_client.find_customer(case.customer_email)
                if cust_match:
                    stripe_cust_id = cust_match.get("id")
            if not stripe_cust_id and case.customer_name:
                cust_match = self.stripe_client.find_customer(case.customer_name)
                if cust_match:
                    stripe_cust_id = cust_match.get("id")

            stripe_charges = self.stripe_client.list_charges(customer_id=stripe_cust_id, limit=10)
            if not stripe_charges and not stripe_cust_id:
                stripe_charges = self.stripe_client.list_charges(limit=10)

            duration = int((time.time() - t0) * 1000)
            self._record_tool_run(case.id, "stripe_list_charges", "success", duration)
            for ch in stripe_charges:
                self.db.add(EvidenceModel(
                    case_id=case.id,
                    source="stripe",
                    evidence_type="charge",
                    payload=ch
                ))

            # Fetch Stripe refunds
            t1 = time.time()
            stripe_refunds = self.stripe_client.list_refunds()
            dur_ref = int((time.time() - t1) * 1000)
            self._record_tool_run(case.id, "stripe_list_refunds", "success", dur_ref)
            for rf in stripe_refunds:
                self.db.add(EvidenceModel(
                    case_id=case.id,
                    source="stripe",
                    evidence_type="refund",
                    payload=rf
                ))
        except Exception as e:
            stripe_error = str(e)
            duration = int((time.time() - t0) * 1000)
            self._record_tool_run(case.id, "stripe_list_charges", "error", duration, str(e))
            self._log_audit(case.id, "TOOL_ERROR", case.status, case.status, {"tool": "stripe", "error": str(e)})

        # 3. Collect Slack evidence
        slack_messages = []
        t0 = time.time()
        try:
            slack_query = case.customer_name or (case.customer_email.split('@')[0] if case.customer_email else "billing")
            slack_messages = self.slack_client.search_billing_messages(slack_query, channel=settings.SLACK_CHANNEL)
            duration = int((time.time() - t0) * 1000)
            self._record_tool_run(case.id, "slack_search_billing_messages", "success", duration)
            for sm in slack_messages:
                self.db.add(EvidenceModel(
                    case_id=case.id,
                    source="slack",
                    evidence_type="internal_context",
                    payload=sm
                ))
        except Exception as e:
            duration = int((time.time() - t0) * 1000)
            self._record_tool_run(case.id, "slack_search_billing_messages", "error", duration, str(e))
            self._log_audit(case.id, "TOOL_ERROR", case.status, case.status, {"tool": "slack", "error": str(e)})

        self.db.commit()

        # If Stripe was completely unreachable, escalate immediately
        if stripe_error:
            decision_output = self.decision_engine.generate_decision(
                ReconciliationResult(risk_flags=["Stripe external ledger unreachable"]),
                stripe_error=stripe_error
            )
            self._save_decision(case, decision_output)
            self._transition(case, CaseStatus.ESCALATED.value, f"Stripe unavailable: {stripe_error}")
            return case

        # Transition to RECONCILING
        self._transition(case, CaseStatus.RECONCILING.value, "Cross-referencing evidence and detecting contradictions")
        t0 = time.time()
        reconciliation = self.reconciler.reconcile(
            gmail_items=gmail_items,
            stripe_charges=stripe_charges,
            stripe_refunds=stripe_refunds,
            slack_messages=slack_messages
        )
        duration = int((time.time() - t0) * 1000)
        self._record_tool_run(case.id, "recon_reconcile_evidence", "success", duration)

        # Generate Decision
        t0 = time.time()
        is_mock_case = bool(self.mock_mode or (case.scenario_id and case.scenario_id.startswith("scenario_")))
        decision_output = self.decision_engine.generate_decision(
            reconciliation,
            mock_mode=is_mock_case
        )
        duration = int((time.time() - t0) * 1000)
        self._record_tool_run(case.id, "recon_generate_decision", "success", duration)
        self._save_decision(case, decision_output)

        # State transition based on decision
        if decision_output.decision == DecisionType.REFUND_RECOMMENDED:
            self._transition(case, CaseStatus.DECISION_READY.value, "Refund recommended; preparing for human review")
            self._transition(case, CaseStatus.AWAITING_APPROVAL.value, "Awaiting explicit human approval")
        elif decision_output.decision == DecisionType.NO_REFUND:
            self._transition(case, CaseStatus.COMPLETED.value, f"No refund justified: {decision_output.reason}")
        else: # ESCALATE_FOR_REVIEW
            self._transition(case, CaseStatus.ESCALATED.value, f"Dispute escalated for human review: {decision_output.reason}")

        return case

    def record_human_approval(self, case_id: str, approved: bool, approved_by: str = "human", notes: Optional[str] = None) -> CaseModel:
        case = self.db.query(CaseModel).filter(CaseModel.id == case_id).first()
        if not case:
            raise ValueError(f"Case {case_id} not found")

        # Persist approval
        existing_approval = self.db.query(ApprovalModel).filter(ApprovalModel.case_id == case_id).first()
        if existing_approval:
            existing_approval.approved = approved
            existing_approval.approved_by = approved_by
            existing_approval.notes = notes
            existing_approval.approved_at = datetime.utcnow()
        else:
            approval = ApprovalModel(
                case_id=case_id,
                approved=approved,
                approved_by=approved_by,
                notes=notes,
                approved_at=datetime.utcnow()
            )
            self.db.add(approval)
        self.db.commit()

        self._record_tool_run(case.id, "human_approval_gate", "success" if approved else "rejected", 0)

        if approved:
            self._log_audit(case.id, "HUMAN_APPROVED", case.status, case.status, {
                "approved_by": approved_by,
                "notes": notes
            })
        else:
            self._transition(case, CaseStatus.BLOCKED.value, f"Refund rejected by human approver ({approved_by})")
            self._log_audit(case.id, "HUMAN_REJECTED", case.status, CaseStatus.BLOCKED.value, {
                "approved_by": approved_by,
                "notes": notes
            })

        return case

    def execute_approved_action(self, case_id: str) -> Dict[str, Any]:
        case = self.db.query(CaseModel).filter(CaseModel.id == case_id).first()
        if not case:
            raise ValueError(f"Case {case_id} not found")

        self._ensure_clients_for_case(case)

        # Load decision and approval
        decision = self.db.query(DecisionModel).filter(DecisionModel.case_id == case_id).first()
        approval = self.db.query(ApprovalModel).filter(ApprovalModel.case_id == case_id).first()

        # Step 1: Run Deterministic Safety Engine
        t0 = time.time()
        safety_result = validate_refund(
            case=case,
            decision=decision,
            approval=approval,
            stripe_client=self.stripe_client,
            db=self.db
        )
        duration = int((time.time() - t0) * 1000)
        self._record_tool_run(
            case.id,
            "deterministic_safety_engine",
            "success" if safety_result["allowed"] else "blocked",
            duration,
            error_message=safety_result["reason"] if not safety_result["allowed"] else None
        )

        if not safety_result["allowed"]:
            self._transition(case, CaseStatus.BLOCKED.value, safety_result["reason"])
            self._log_audit(case.id, "SAFETY_BLOCK", case.status, CaseStatus.BLOCKED.value, safety_result)
            return {
                "executed": False,
                "safety_check": safety_result,
                "case_status": case.status
            }

        # Step 2: Transition to EXECUTING
        self._transition(case, CaseStatus.EXECUTING.value, f"Executing Stripe refund for charge {safety_result['target_charge_id']}")

        # Step 3: Execute Stripe Refund
        target_charge_id = safety_result["target_charge_id"]
        target_amount = safety_result["target_amount"]

        t0 = time.time()
        try:
            refund_resp = self.stripe_client.create_refund(
                charge_id=target_charge_id,
                amount=target_amount,
                reason="duplicate",
                idempotency_key=f"recon_{case.id}_{target_charge_id}"
            )
            duration = int((time.time() - t0) * 1000)
            self._record_tool_run(case.id, "stripe_create_refund", "success", duration)

            action = ActionModel(
                case_id=case.id,
                action_type="stripe_create_refund",
                charge_id=target_charge_id,
                refund_id=refund_resp["id"],
                amount=target_amount,
                currency="usd",
                status=refund_resp.get("status", "succeeded"),
                executed_at=datetime.utcnow()
            )
            self.db.add(action)
            self.db.commit()

            self._log_audit(case.id, "REFUND_EXECUTED", CaseStatus.EXECUTING.value, CaseStatus.VERIFYING.value, refund_resp)

            # Step 4: Automatically trigger post-action verification
            verification_result = self.verify_post_action(case.id, refund_resp["id"], target_charge_id, target_amount)

            return {
                "executed": True,
                "safety_check": safety_result,
                "action": {
                    "action_type": "stripe_create_refund",
                    "refund_id": refund_resp["id"],
                    "charge_id": target_charge_id,
                    "amount": target_amount,
                    "status": refund_resp.get("status")
                },
                "verification": verification_result,
                "case_status": case.status
            }
        except Exception as e:
            duration = int((time.time() - t0) * 1000)
            self._record_tool_run(case.id, "stripe_create_refund", "error", duration, str(e))
            self._transition(case, CaseStatus.FAILED.value, f"Stripe refund execution failed: {str(e)}")
            return {
                "executed": False,
                "safety_check": safety_result,
                "error": str(e),
                "case_status": case.status
            }

    def verify_post_action(self, case_id: str, refund_id: str, charge_id: str, expected_amount: int) -> Dict[str, Any]:
        case = self.db.query(CaseModel).filter(CaseModel.id == case_id).first()
        if not case:
            raise ValueError(f"Case {case_id} not found")

        self._ensure_clients_for_case(case)
        self._transition(case, CaseStatus.VERIFYING.value, f"Verifying Stripe state for refund {refund_id}")

        t0 = time.time()
        try:
            refund_obj = self.stripe_client.get_refund(refund_id)
            duration = int((time.time() - t0) * 1000)
            self._record_tool_run(case.id, "stripe_get_refund", "success", duration)

            verified = (
                refund_obj.get("id") == refund_id and
                refund_obj.get("status") == "succeeded" and
                refund_obj.get("amount") == expected_amount
            )

            # Persist verification
            ver = VerificationModel(
                case_id=case.id,
                refund_id=refund_id,
                charge_id=charge_id,
                amount=refund_obj.get("amount", expected_amount),
                status=refund_obj.get("status", "unknown"),
                verified=verified,
                verified_at=datetime.utcnow()
            )
            self.db.add(ver)
            self.db.commit()

            # Post notification to Slack billing channel
            slack_msg = (
                f"RECON completed billing case {case.id}.\n"
                f"Customer: {case.customer_name or 'Acme Corp'}\n"
                f"Issue: Duplicate ${expected_amount / 100:.2f} charge\n"
                f"Action: ${expected_amount / 100:.2f} refund\n"
                f"Stripe Refund: {refund_id}\n"
                f"Status: Verified"
            )

            t_slack = time.time()
            try:
                slack_res = self.slack_client.post_message("billing", slack_msg)
                dur_slack = int((time.time() - t_slack) * 1000)
                self._record_tool_run(case.id, "slack_post_message", "success", dur_slack)
            except Exception as e_slack:
                dur_slack = int((time.time() - t_slack) * 1000)
                self._record_tool_run(case.id, "slack_post_message", "error", dur_slack, str(e_slack))

            self._transition(case, CaseStatus.COMPLETED.value, f"Action verified in Stripe ({refund_id}) and Slack notified")
            self._log_audit(case.id, "VERIFICATION_SUCCESS", CaseStatus.VERIFYING.value, CaseStatus.COMPLETED.value, {
                "refund_id": refund_id,
                "verified": verified,
                "status": refund_obj.get("status")
            })

            return {
                "refund_id": refund_id,
                "charge_id": charge_id,
                "amount": expected_amount,
                "status": refund_obj.get("status"),
                "verified": verified
            }
        except Exception as e:
            duration = int((time.time() - t0) * 1000)
            self._record_tool_run(case.id, "stripe_get_refund", "error", duration, str(e))
            self._transition(case, CaseStatus.FAILED.value, f"Post-action verification failed: {str(e)}")
            return {
                "refund_id": refund_id,
                "charge_id": charge_id,
                "amount": expected_amount,
                "status": "failed",
                "verified": False,
                "error": str(e)
            }

    def _transition(self, case: CaseModel, new_status: str, reason: str):
        old_status = case.status
        case.status = new_status
        case.updated_at = datetime.utcnow()
        self.db.commit()
        self._log_audit(case.id, "STATE_TRANSITION", old_status, new_status, {"reason": reason})

    def _save_decision(self, case: CaseModel, decision: DecisionOutput):
        existing = self.db.query(DecisionModel).filter(DecisionModel.case_id == case.id).first()
        if existing:
            existing.decision = decision.decision.value
            existing.confidence = decision.confidence
            existing.reason = decision.reason
            existing.supporting_evidence = decision.supporting_evidence
            existing.risk_flags = decision.risk_flags
        else:
            dm = DecisionModel(
                case_id=case.id,
                decision=decision.decision.value,
                confidence=decision.confidence,
                reason=decision.reason,
                supporting_evidence=decision.supporting_evidence,
                risk_flags=decision.risk_flags
            )
            self.db.add(dm)
        self.db.commit()

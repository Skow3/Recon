from typing import List, Optional, Any, Dict
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

class DecisionType(str, Enum):
    REFUND_RECOMMENDED = "REFUND_RECOMMENDED"
    NO_REFUND = "NO_REFUND"
    ESCALATE_FOR_REVIEW = "ESCALATE_FOR_REVIEW"

class CaseStatus(str, Enum):
    RECEIVED = "RECEIVED"
    PLANNING = "PLANNING"
    COLLECTING_EVIDENCE = "COLLECTING_EVIDENCE"
    RECONCILING = "RECONCILING"
    DECISION_READY = "DECISION_READY"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    EXECUTING = "EXECUTING"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    ESCALATED = "ESCALATED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"

class GmailEvidence(BaseModel):
    source: str = "gmail"
    message_id: str
    thread_id: str
    sender: str
    recipient: str
    subject: str
    timestamp: str
    body: str
    relevant_claims: List[str] = Field(default_factory=list)

class StripeChargeEvidence(BaseModel):
    source: str = "stripe"
    type: str = "charge"
    id: str
    amount: int # in cents
    currency: str
    status: str
    created: Optional[str] = None
    customer_id: Optional[str] = None
    invoice_id: Optional[str] = None
    refunded: bool = False
    amount_refunded: int = 0

class StripeRefundEvidence(BaseModel):
    source: str = "stripe"
    type: str = "refund"
    id: str
    charge_id: str
    amount: int
    status: str
    created: Optional[str] = None

class SlackEvidence(BaseModel):
    source: str = "slack"
    channel: str
    message_id: str
    timestamp: str
    author: str
    text: str

class ReconciliationResult(BaseModel):
    customer_match: bool = True
    charges_found: int = 0
    charge_comparison: List[Dict[str, Any]] = Field(default_factory=list)
    gmail_claim: str = ""
    slack_context: str = ""
    contradictions: List[str] = Field(default_factory=list)
    supporting_evidence: List[str] = Field(default_factory=list)
    refuting_evidence: List[str] = Field(default_factory=list)
    risk_flags: List[str] = Field(default_factory=list)

class DecisionOutput(BaseModel):
    decision: DecisionType
    confidence: float
    reason: str
    supporting_evidence: List[str] = Field(default_factory=list)
    risk_flags: List[str] = Field(default_factory=list)

class SafetyCheckResult(BaseModel):
    allowed: bool
    reason: str
    details: Dict[str, Any] = Field(default_factory=dict)

class VerificationOutput(BaseModel):
    refund_id: str
    charge_id: str
    amount: int
    status: str
    verified: bool

class ToolTraceItem(BaseModel):
    id: Optional[int] = None
    tool: str
    status: str
    duration_ms: int
    timestamp: str
    error: Optional[str] = None

class CaseDetailResponse(BaseModel):
    id: str
    user_request: str
    customer_name: Optional[str]
    customer_email: Optional[str]
    scenario_id: Optional[str]
    status: CaseStatus
    created_at: str
    updated_at: str
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    reconciliation: Optional[ReconciliationResult] = None
    decision: Optional[DecisionOutput] = None
    safety_check: Optional[SafetyCheckResult] = None
    approval: Optional[Dict[str, Any]] = None
    action: Optional[Dict[str, Any]] = None
    verification: Optional[VerificationOutput] = None
    slack_notification: Optional[Dict[str, Any]] = None

class EvaluationCaseResult(BaseModel):
    case_name: str
    scenario_id: str
    expected_decision: str
    actual_decision: str
    expected_refund_allowed: bool = False
    decision_correct: bool
    refund_attempted: bool
    refund_succeeded: bool
    unsafe_action: bool
    duplicate_action: bool
    verification_succeeded: bool
    failure_handled_correctly: bool
    final_state: str
    notes: str

class EvaluationReport(BaseModel):
    total_cases: int
    decision_accuracy_pct: float
    false_refund_rate_pct: float
    unsafe_action_count: int
    duplicate_refund_count: int
    verification_success_rate_pct: float
    failure_handling_rate_pct: float
    results: List[EvaluationCaseResult]

from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from ..database.db import Base

class CaseModel(Base):
    __tablename__ = "cases"

    id = Column(String, primary_key=True, index=True) # e.g. CASE-001
    workspace_id = Column(String, default="ws_finance", nullable=True, index=True)
    workflow_id = Column(String, default="wf_billing_investigator", nullable=True, index=True)
    user_request = Column(Text, nullable=False)
    customer_name = Column(String, nullable=True)
    customer_email = Column(String, nullable=True)
    scenario_id = Column(String, nullable=True)
    status = Column(String, default="RECEIVED", nullable=False) # RECEIVED, PLANNING, COLLECTING_EVIDENCE, RECONCILING, DECISION_READY, AWAITING_APPROVAL, EXECUTING, VERIFYING, COMPLETED, ESCALATED, BLOCKED, FAILED
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    evidence_items = relationship("EvidenceModel", back_populates="case", cascade="all, delete-orphan")
    decision = relationship("DecisionModel", back_populates="case", uselist=False, cascade="all, delete-orphan")
    approval = relationship("ApprovalModel", back_populates="case", uselist=False, cascade="all, delete-orphan")
    action = relationship("ActionModel", back_populates="case", uselist=False, cascade="all, delete-orphan")
    verification = relationship("VerificationModel", back_populates="case", uselist=False, cascade="all, delete-orphan")
    tool_runs = relationship("ToolRunModel", back_populates="case", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLogModel", back_populates="case", cascade="all, delete-orphan")

class ApprovalModel(Base):
    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String, ForeignKey("cases.id"), nullable=False, unique=True)
    approved = Column(Boolean, nullable=False)
    approved_by = Column(String, default="human", nullable=False)
    approved_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)

    case = relationship("CaseModel", back_populates="approval")

class ActionModel(Base):
    __tablename__ = "actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String, ForeignKey("cases.id"), nullable=False, unique=True)
    action_type = Column(String, default="stripe_create_refund", nullable=False)
    charge_id = Column(String, nullable=False)
    refund_id = Column(String, nullable=True)
    amount = Column(Integer, nullable=False) # In cents
    currency = Column(String, default="usd", nullable=False)
    status = Column(String, default="pending", nullable=False)
    executed_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("CaseModel", back_populates="action")

class VerificationModel(Base):
    __tablename__ = "verifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String, ForeignKey("cases.id"), nullable=False, unique=True)
    refund_id = Column(String, nullable=False)
    charge_id = Column(String, nullable=False)
    amount = Column(Integer, nullable=False)
    status = Column(String, nullable=False) # e.g. succeeded
    verified = Column(Boolean, default=False, nullable=False)
    verified_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("CaseModel", back_populates="verification")

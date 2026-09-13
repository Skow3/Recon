from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from ..database.db import Base

class WorkspaceModel(Base):
    __tablename__ = "workspaces"

    id = Column(String, primary_key=True, index=True) # e.g. ws_finance, ws_internships
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    connected_apps = Column(JSON, default=list, nullable=False) # e.g. ["gmail", "stripe", "slack"]
    agent_instructions = Column(Text, nullable=True)
    permissions = Column(JSON, default=dict, nullable=False) # e.g. {"gmail": {"read_emails": True}, "stripe": {"create_refunds": "APPROVAL_REQUIRED"}}
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    workflows = relationship("WorkflowModel", back_populates="workspace", cascade="all, delete-orphan")
    runs = relationship("WorkflowRunModel", back_populates="workspace", cascade="all, delete-orphan")


class WorkflowModel(Base):
    __tablename__ = "workflows"

    id = Column(String, primary_key=True, index=True) # e.g. wf_billing_investigator, wf_internship_monitor
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    goal = Column(Text, nullable=False)
    status = Column(String, default="ACTIVE", nullable=False) # DRAFT, ACTIVE, PAUSED, RUNNING, COMPLETED, FAILED, BLOCKED
    connected_apps = Column(JSON, default=list, nullable=False)
    trigger = Column(JSON, default=dict, nullable=False) # e.g. {"app": "gmail", "event": "new_email"}
    agent_plan = Column(JSON, default=list, nullable=False) # List of plan steps
    configuration = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    workspace = relationship("WorkspaceModel", back_populates="workflows")
    runs = relationship("WorkflowRunModel", back_populates="workflow", cascade="all, delete-orphan")


class WorkflowRunModel(Base):
    __tablename__ = "workflow_runs"

    id = Column(String, primary_key=True, index=True) # e.g. run_xxx
    workflow_id = Column(String, ForeignKey("workflows.id"), nullable=False, index=True)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False, index=True)
    trigger_event = Column(JSON, default=dict, nullable=False)
    status = Column(String, default="RUNNING", nullable=False) # RUNNING, WAITING_FOR_APPROVAL, COMPLETED, FAILED, BLOCKED
    plan_snapshot = Column(JSON, default=list, nullable=False)
    extracted_data = Column(JSON, default=dict, nullable=False)
    decision = Column(JSON, default=dict, nullable=False)
    approval_status = Column(String, default="NOT_REQUIRED", nullable=False) # NOT_REQUIRED, PENDING, APPROVED, REJECTED
    action_result = Column(JSON, default=dict, nullable=False)
    verification_result = Column(JSON, default=dict, nullable=False)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    workspace = relationship("WorkspaceModel", back_populates="runs")
    workflow = relationship("WorkflowModel", back_populates="runs")


class ProcessedEventModel(Base):
    __tablename__ = "processed_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_app = Column(String, nullable=False, index=True) # e.g. "gmail", "stripe"
    source_event_id = Column(String, nullable=False, index=True) # e.g. message_id
    workflow_id = Column(String, nullable=False, index=True)
    processed_at = Column(DateTime, default=datetime.utcnow)

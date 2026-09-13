from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from ..database.db import Base

class ToolRunModel(Base):
    __tablename__ = "tool_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String, ForeignKey("cases.id"), nullable=True, index=True)
    workspace_id = Column(String, nullable=True, index=True)
    workflow_id = Column(String, nullable=True, index=True)
    tool_name = Column(String, nullable=False)
    status = Column(String, nullable=False) # 'success', 'error'
    duration_ms = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    case = relationship("CaseModel", back_populates="tool_runs")

class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String, ForeignKey("cases.id"), nullable=True, index=True)
    workspace_id = Column(String, nullable=True, index=True)
    workflow_id = Column(String, nullable=True, index=True)
    event_type = Column(String, nullable=False)
    state_from = Column(String, nullable=True)
    state_to = Column(String, nullable=True)
    details = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=datetime.utcnow)

    case = relationship("CaseModel", back_populates="audit_logs")

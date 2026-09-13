from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from ..database.db import Base

class EvidenceModel(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String, ForeignKey("cases.id"), nullable=False, index=True)
    source = Column(String, nullable=False) # 'gmail', 'stripe', 'slack'
    evidence_type = Column(String, nullable=False) # 'customer_claim', 'charge', 'invoice', 'refund', 'internal_context'
    payload = Column(JSON, nullable=False)
    collected_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("CaseModel", back_populates="evidence_items")

class DecisionModel(Base):
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String, ForeignKey("cases.id"), nullable=False, unique=True)
    decision = Column(String, nullable=False) # 'REFUND_RECOMMENDED', 'NO_REFUND', 'ESCALATE_FOR_REVIEW'
    confidence = Column(Float, nullable=False)
    reason = Column(Text, nullable=False)
    supporting_evidence = Column(JSON, default=list)
    refuting_evidence = Column(JSON, default=list)
    risk_flags = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("CaseModel", back_populates="decision")

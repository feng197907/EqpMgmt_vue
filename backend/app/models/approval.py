from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from backend.app.db.session import Base


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"
    id = Column(Integer, primary_key=True, index=True)
    doc_id = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    created_by = Column(String(255), nullable=False)
    current_step = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.current_timestamp())


class ApprovalStep(Base):
    __tablename__ = "approval_steps"
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("approval_requests.id"), nullable=False)
    step_order = Column(Integer, nullable=False)
    approver_role = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    decided_by = Column(String(255), nullable=True)
    decided_at = Column(DateTime, nullable=True)
    comment = Column(String(1000), nullable=True)
    signature_id = Column(Integer, nullable=True)

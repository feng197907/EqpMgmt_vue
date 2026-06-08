"""Approval Pydantic schemas.

Provides request/response schemas for the approval workflow API.
"""

from typing import Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ApprovalCreate(BaseModel):
    """Schema for submitting a document for approval."""
    doc_id: int


class ApprovalRequestOut(BaseModel):
    """Schema for an approval request response."""
    id: int
    doc_id: int
    doc_name: Optional[str] = None
    status: str
    created_by: Optional[str] = None
    current_step: Optional[int] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ApprovalStepOut(BaseModel):
    """Schema for an approval step response."""
    id: int
    request_id: int
    step_order: int
    approver_role: str
    status: str
    decided_by: Optional[str] = None
    decided_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ApprovalDecision(BaseModel):
    """Schema for approving or rejecting an approval request."""
    comment: Optional[str] = None

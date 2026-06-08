"""Device status-change Pydantic schemas.

Provides request/response schemas for the device status-change API.
"""

from typing import Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DeviceChangeCreate(BaseModel):
    """Schema for creating a device status-change request."""
    device_id: int
    new_status: str
    reason: Optional[str] = None


class DeviceChangeOut(BaseModel):
    """Schema for a device status-change response."""
    id: int
    device_id: int
    new_status: str
    reason: Optional[str] = None
    requested_by: Optional[str] = None
    created_at: Optional[datetime] = None
    status: str = "pending"
    decided_by: Optional[str] = None
    decided_at: Optional[datetime] = None
    comment: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DeviceChangeDecision(BaseModel):
    """Schema for approving or rejecting a device status-change request."""
    action: str = "approve"   # "approve" or "reject"
    comment: Optional[str] = None

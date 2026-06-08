"""Electronic-signature Pydantic schemas.

Provides request/response schemas for the e-signature API.
"""

from typing import Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ESignCreate(BaseModel):
    """Schema for creating an electronic signature."""
    record_type: str                           # e.g. maintenance_plan, document, device_change
    record_id: int
    sign_meaning: str                          # approved / reviewed / executed / released
    sign_meaning_label: str                    # Chinese label
    remark: Optional[str] = None


class ESignatureOut(BaseModel):
    """Schema for an electronic-signature response."""
    id: int
    record_type: str
    record_id: int
    signed_by: str
    signed_by_display: Optional[str] = None
    sign_meaning: str
    sign_meaning_label: Optional[str] = None
    signed_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    remark: Optional[str] = None
    is_deleted: bool = False

    model_config = ConfigDict(from_attributes=True)

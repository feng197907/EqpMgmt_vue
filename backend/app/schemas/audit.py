from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class AuditLogOut(BaseModel):
    id: int
    user: Optional[str] = None
    action: Optional[str] = None
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    details: Optional[str] = None
    before_value: Optional[str] = None
    after_value: Optional[str] = None
    reason: Optional[str] = None
    ip_address: Optional[str] = None
    log_time: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SettingOut(BaseModel):
    id: int
    setting_key: str
    setting_value: Optional[str] = None
    description: Optional[str] = None
    updated_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SettingUpdate(BaseModel):
    setting_value: str

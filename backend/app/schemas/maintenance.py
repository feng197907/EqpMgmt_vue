from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class MaintenancePlanBase(BaseModel):
    device_id: int
    maintenance_type: str
    interval_days: int
    next_due_date: str


class MaintenancePlanCreate(MaintenancePlanBase):
    pass


class MaintenancePlanUpdate(BaseModel):
    maintenance_type: Optional[str] = None
    interval_days: Optional[int] = None
    next_due_date: Optional[str] = None
    is_active: Optional[bool] = None


class MaintenancePlanOut(MaintenancePlanBase):
    id: int
    is_active: bool
    is_closed: bool
    closed_at: Optional[datetime] = None
    closed_by: Optional[str] = None
    close_reason: Optional[str] = None
    created_by: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    urgency: Optional[str] = None
    overdue_days: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class MaintenanceRecordCreate(BaseModel):
    content: str
    result: str
    parts_used: Optional[str] = None


class MaintenanceRecordOut(BaseModel):
    id: int
    plan_id: int
    device_id: int
    maintenance_type: str
    content: str
    result: str
    performed_by: str
    performed_at: Optional[str] = None
    next_due_date: Optional[str] = None
    parts_used: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class RepairRecordCreate(BaseModel):
    content: str
    result: str
    parts_used: Optional[str] = None


class RepairRecordOut(BaseModel):
    id: int
    device_id: int
    content: str
    result: str
    performed_by: str
    performed_at: Optional[str] = None
    parts_used: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

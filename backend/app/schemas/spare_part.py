from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class SparePartCreate(BaseModel):
    name: str
    category: str = "other"
    specification: Optional[str] = None
    unit: str = "个"
    brand: Optional[str] = None
    safety_stock_min: int = 0
    safety_stock_max: int = 9999
    supplier_name: Optional[str] = None
    supplier_contact: Optional[str] = None
    supplier_phone: Optional[str] = None
    remark: Optional[str] = None


class SparePartUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    specification: Optional[str] = None
    unit: Optional[str] = None
    brand: Optional[str] = None
    safety_stock_min: Optional[int] = None
    safety_stock_max: Optional[int] = None
    supplier_name: Optional[str] = None
    supplier_contact: Optional[str] = None
    supplier_phone: Optional[str] = None
    remark: Optional[str] = None
    is_active: Optional[bool] = None


class SparePartOut(BaseModel):
    id: int
    code: str
    name: str
    category: str
    specification: Optional[str] = None
    unit: Optional[str] = None
    brand: Optional[str] = None
    safety_stock_min: int
    safety_stock_max: int
    current_stock: int
    weighted_avg_price: float
    supplier_name: Optional[str] = None
    supplier_contact: Optional[str] = None
    supplier_phone: Optional[str] = None
    supplier_doc_path: Optional[str] = None
    remark: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class InboundCreate(BaseModel):
    spare_part_id: int
    quantity: int
    unit_price: float = 0
    batch_no: Optional[str] = None
    inbound_date: Optional[str] = None
    remark: Optional[str] = None


class InboundOut(BaseModel):
    id: int
    spare_part_id: int
    quantity: int
    unit_price: float
    batch_no: Optional[str] = None
    inbound_date: Optional[datetime] = None
    remark: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ConsumptionCreate(BaseModel):
    spare_part_id: int
    quantity: int
    maintenance_record_id: Optional[int] = None
    batch_no: Optional[str] = None
    remark: Optional[str] = None


class ConsumptionOut(BaseModel):
    id: int
    spare_part_id: int
    maintenance_record_id: Optional[int] = None
    quantity: int
    unit_price: float
    batch_no: Optional[str] = None
    consumed_by: Optional[str] = None
    consumed_at: Optional[datetime] = None
    remark: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AlertOut(BaseModel):
    id: int
    spare_part_id: int
    alert_type: str
    current_stock: int
    threshold: int
    is_resolved: bool
    resolved_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

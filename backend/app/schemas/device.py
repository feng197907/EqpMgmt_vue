from pydantic import BaseModel
from typing import Optional


class DeviceBase(BaseModel):
    device_code: str
    device_name: Optional[str] = None
    model: Optional[str] = None
    location: Optional[str] = None


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(BaseModel):
    device_code: Optional[str] = None
    device_name: Optional[str] = None
    model: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None


class DeviceOut(DeviceBase):
    id: int
    status: Optional[str] = None
    is_deleted: Optional[bool] = False

    class Config:
        orm_mode = True

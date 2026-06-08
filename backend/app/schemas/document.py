from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date


class DocumentBase(BaseModel):
    device_id: int
    doc_type: str
    doc_name: str
    version: str
    remarks: Optional[str] = None
    calibration_due_date: Optional[date] = None


class DocumentCreate(DocumentBase):
    pass


class DocumentOut(DocumentBase):
    id: int
    file_path: str
    uploaded_by: str
    upload_time: Optional[datetime] = None
    status: str
    download_count: int
    is_deleted: bool

    class Config:
        orm_mode = True

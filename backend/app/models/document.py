from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Date
from backend.app.db.session import Base


class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, nullable=False)
    doc_type = Column(String(50), nullable=False)
    doc_name = Column(String(255), nullable=False)
    version = Column(String(50), nullable=False)
    file_path = Column(String(500), nullable=False)
    uploaded_by = Column(String(255), nullable=False)
    upload_time = Column(DateTime, nullable=True)
    remarks = Column(String(1000), nullable=True)
    status = Column(String(50), nullable=False, default="draft")
    download_count = Column(Integer, default=0)
    is_deleted = Column(Boolean, default=False)
    calibration_due_date = Column(Date, nullable=True)

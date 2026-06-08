from sqlalchemy import Column, Integer, String, Boolean, DateTime
from backend.app.db.session import Base


class Device(Base):
    __tablename__ = "devices"
    id = Column(Integer, primary_key=True, index=True)
    device_code = Column(String(128), unique=True, nullable=False)
    device_name = Column(String(256), nullable=False)
    model = Column(String(128), nullable=True)
    location = Column(String(256), nullable=True)
    status = Column(String(32), nullable=False, default="active")
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=True)

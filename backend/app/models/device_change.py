"""DeviceStatusRequest ORM model.

Represents a request to change a device's status (e.g. active → retired).
Requests go through an approval workflow (pending → approved / rejected).
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, func

from backend.app.db.session import Base


class DeviceStatusRequest(Base):
    __tablename__ = "device_status_requests"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    new_status = Column(String(32), nullable=False)
    reason = Column(String(1000), nullable=True)
    requested_by = Column(String(128), nullable=False)
    created_at = Column("created_at", DateTime, server_default=func.current_timestamp())
    status = Column(String(32), default="pending")  # pending / approved / rejected
    decided_by = Column(String(128), nullable=True)
    decided_at = Column(DateTime, nullable=True)
    comment = Column(Text, nullable=True)

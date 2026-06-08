from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, func

from backend.app.db.session import Base


class MaintenancePlan(Base):
    __tablename__ = "maintenance_plan"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, nullable=False)
    maintenance_type = Column(String(50), nullable=False)
    interval_days = Column(Integer, nullable=False)
    next_due_date = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)
    is_closed = Column(Boolean, default=False)
    closed_at = Column(DateTime, nullable=True)
    closed_by = Column(String(255), nullable=True)
    close_reason = Column(Text, nullable=True)
    created_by = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=True, server_default=func.current_timestamp())
    updated_at = Column(DateTime, nullable=True, server_default=func.current_timestamp(), onupdate=func.current_timestamp())


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_record"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, nullable=False)
    device_id = Column(Integer, nullable=False)
    maintenance_type = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    result = Column(String(50), nullable=False)
    performed_by = Column(String(255), nullable=False)
    performed_at = Column(String(50), nullable=True)
    next_due_date = Column(String(50), nullable=True)
    parts_used = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=True, server_default=func.current_timestamp())


class DeviceRepairRecord(Base):
    __tablename__ = "repair_record"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    result = Column(String(50), nullable=False)
    performed_by = Column(String(255), nullable=False)
    performed_at = Column(String(50), nullable=True)
    parts_used = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=True, server_default=func.current_timestamp())

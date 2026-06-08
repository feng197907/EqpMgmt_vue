from sqlalchemy import Column, Integer, String, DateTime, Text, func

from backend.app.db.session import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user = Column(String(128), nullable=True)
    action = Column(String(128), nullable=True)
    target_type = Column(String(50), nullable=True)
    target_id = Column(Integer, nullable=True)
    details = Column(String(2000), nullable=True)
    before_value = Column(String(1000), nullable=True)
    after_value = Column(String(1000), nullable=True)
    reason = Column(String(1000), nullable=True)
    ip_address = Column(String(50), nullable=True)
    log_time = Column(DateTime, server_default=func.current_timestamp())


class SystemSetting(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    setting_key = Column(String(128), unique=True, nullable=False)
    setting_value = Column(Text, nullable=True)
    description = Column(String(256), nullable=True)
    updated_by = Column(String(128), nullable=True)
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

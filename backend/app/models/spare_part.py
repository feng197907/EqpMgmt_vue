from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Date, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.app.db.session import Base


class SparePart(Base):
    __tablename__ = "spare_parts"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    category = Column(String(64), default="other")
    specification = Column(String(200), nullable=True)
    unit = Column(String(20), default="个")
    brand = Column(String(100), nullable=True)
    safety_stock_min = Column(Integer, default=0)
    safety_stock_max = Column(Integer, default=9999)
    current_stock = Column(Integer, default=0)
    weighted_avg_price = Column(Numeric(10, 2), default=0)
    supplier_name = Column(String(200), nullable=True)
    supplier_contact = Column(String(100), nullable=True)
    supplier_phone = Column(String(50), nullable=True)
    supplier_doc_path = Column(String(500), nullable=True)
    remark = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class SparePartInbound(Base):
    __tablename__ = "spare_part_inbounds"

    id = Column(Integer, primary_key=True, index=True)
    spare_part_id = Column(Integer, ForeignKey("spare_parts.id"), nullable=False)
    quantity = Column(Integer, default=0)
    unit_price = Column(Numeric(10, 2), default=0)
    batch_no = Column(String(50), nullable=True)
    inbound_date = Column(Date, nullable=False)
    doc_path = Column(String(500), nullable=True)
    remark = Column(Text, nullable=True)
    created_by = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    spare_part = relationship("SparePart", backref="inbounds")


class SparePartConsumption(Base):
    __tablename__ = "spare_part_consumptions"

    id = Column(Integer, primary_key=True, index=True)
    spare_part_id = Column(Integer, ForeignKey("spare_parts.id"), nullable=False)
    maintenance_record_id = Column(Integer, nullable=True)
    quantity = Column(Integer, default=0)
    unit_price = Column(Numeric(10, 2), default=0)
    batch_no = Column(String(50), nullable=True)
    consumed_by = Column(String(128), nullable=True)
    consumed_at = Column(DateTime, default=datetime.now)
    remark = Column(Text, nullable=True)

    spare_part = relationship("SparePart", backref="consumptions")


class SparePartAlert(Base):
    __tablename__ = "spare_part_alerts"

    id = Column(Integer, primary_key=True, index=True)
    spare_part_id = Column(Integer, ForeignKey("spare_parts.id"), nullable=False)
    alert_type = Column(String(32), nullable=False)
    current_stock = Column(Integer, default=0)
    threshold = Column(Integer, default=0)
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    spare_part = relationship("SparePart", backref="alerts")

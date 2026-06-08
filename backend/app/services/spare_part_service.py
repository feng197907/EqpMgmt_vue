"""Spare-part service — CRUD, inbound/consumption, stock alerts, and audit.

All database mutations go through this module so that audit logging is
enforced consistently.
"""

import datetime as dt
from typing import Optional, List

from sqlalchemy.orm import Session

from backend.app.models.spare_part import SparePart, SparePartInbound, SparePartConsumption, SparePartAlert
from backend.app.models.user import User
from backend.app.services.audit_service import log_action


# ── Spare Parts CRUD ───────────────────────────────────────────────────────


def list_spare_parts(
    db: Session,
    *,
    category: Optional[str] = None,
    search: Optional[str] = None,
    stock_filter: Optional[str] = None,
    include_inactive: bool = False,
) -> List[SparePart]:
    """Return spare parts with optional filters."""
    q = db.query(SparePart)
    if not include_inactive:
        q = q.filter(SparePart.is_active == True)
    if category:
        q = q.filter(SparePart.category == category)
    if search:
        like = f"%{search}%"
        q = q.filter(
            (SparePart.name.ilike(like))
            | (SparePart.code.ilike(like))
            | (SparePart.specification.ilike(like))
            | (SparePart.brand.ilike(like))
        )
    if stock_filter == "low":
        q = q.filter(SparePart.current_stock > 0, SparePart.current_stock <= SparePart.safety_stock_min)
    elif stock_filter == "out":
        q = q.filter(SparePart.current_stock <= 0)
    elif stock_filter == "over":
        q = q.filter(SparePart.safety_stock_max > 0, SparePart.current_stock >= SparePart.safety_stock_max)
    elif stock_filter == "normal":
        q = q.filter(SparePart.current_stock > SparePart.safety_stock_min)
        q = q.filter((SparePart.safety_stock_max == 0) | (SparePart.current_stock < SparePart.safety_stock_max))
    return q.order_by(SparePart.updated_at.desc(), SparePart.id.desc()).all()


def list_active_for_select(db: Session) -> List[dict]:
    """Return a lightweight list for dropdown selections."""
    parts = db.query(SparePart).filter(SparePart.is_active == True).order_by(SparePart.code).all()
    return [
        {
            "id": p.id,
            "code": p.code,
            "name": p.name,
            "specification": p.specification,
            "unit": p.unit,
            "current_stock": p.current_stock,
        }
        for p in parts
    ]


def get_spare_part(db: Session, part_id: int) -> SparePart:
    """Return a spare part or raise ``ValueError``."""
    part = db.query(SparePart).filter(SparePart.id == part_id).first()
    if not part:
        raise ValueError("Spare part not found")
    return part


def _generate_code(db: Session) -> str:
    """Auto-generate a spare-part code in the form ``SP-YYYY-NNNNN``."""
    year = dt.datetime.now().strftime("%Y")
    latest = db.query(SparePart).filter(SparePart.code.like(f"SP-{year}-%")).order_by(SparePart.code.desc()).first()
    if latest:
        try:
            seq = int(latest.code.split("-")[-1]) + 1
        except (ValueError, IndexError):
            seq = 1
    else:
        seq = 1
    return f"SP-{year}-{seq:05d}"


def create_spare_part(
    db: Session,
    *,
    name: str,
    category: str = "other",
    specification: Optional[str] = None,
    unit: str = "个",
    brand: Optional[str] = None,
    safety_stock_min: int = 0,
    safety_stock_max: int = 9999,
    supplier_name: Optional[str] = None,
    supplier_contact: Optional[str] = None,
    supplier_phone: Optional[str] = None,
    remark: Optional[str] = None,
    current_user: Optional[User] = None,
) -> SparePart:
    """Create a new spare part with an auto-generated code."""
    code = _generate_code(db)
    part = SparePart(
        code=code,
        name=name,
        category=category,
        specification=specification,
        unit=unit,
        brand=brand,
        safety_stock_min=safety_stock_min,
        safety_stock_max=safety_stock_max,
        supplier_name=supplier_name,
        supplier_contact=supplier_contact,
        supplier_phone=supplier_phone,
        remark=remark,
    )
    db.add(part)
    db.flush()

    operator = current_user.username if current_user else "system"
    log_action(db, operator, "create_spare_part", "spare_part", part.id, f"创建备件 {code}")

    db.commit()
    db.refresh(part)
    return part


def update_spare_part(
    db: Session,
    part_id: int,
    *,
    current_user: Optional[User] = None,
    **kwargs,
) -> SparePart:
    """Update a spare part.  Only supplied keyword arguments are modified."""
    part = get_spare_part(db, part_id)
    for k, v in kwargs.items():
        if v is not None:
            setattr(part, k, v)

    operator = current_user.username if current_user else "system"
    log_action(db, operator, "update_spare_part", "spare_part", part.id, f"更新备件 {part.code}")
    db.commit()
    db.refresh(part)
    return part


def delete_spare_part(
    db: Session,
    part_id: int,
    *,
    current_user: Optional[User] = None,
) -> None:
    """Soft-delete a spare part by setting ``is_active=False``."""
    part = get_spare_part(db, part_id)
    part.is_active = False
    operator = current_user.username if current_user else "system"
    log_action(db, operator, "delete_spare_part", "spare_part", part.id, f"删除备件 {part.code}")
    db.commit()


# ── Inbound ────────────────────────────────────────────────────────────────


def inbound_spare_part(
    db: Session,
    part_id: int,
    *,
    quantity: int,
    unit_price: float = 0,
    batch_no: Optional[str] = None,
    inbound_date: Optional[str] = None,
    remark: Optional[str] = None,
    current_user: User,
) -> SparePartInbound:
    """Record an inbound (restocking) for a spare part with weighted-avg price."""
    part = get_spare_part(db, part_id)

    old_value = part.current_stock * float(part.weighted_avg_price or 0)
    new_value = quantity * float(unit_price or 0)
    new_stock = part.current_stock + quantity
    new_price = round((old_value + new_value) / new_stock, 2) if new_stock > 0 else 0

    part.current_stock = new_stock
    part.weighted_avg_price = new_price

    parsed_date = None
    if inbound_date:
        try:
            parsed_date = dt.datetime.strptime(inbound_date, "%Y-%m-%d")
        except ValueError:
            parsed_date = dt.datetime.now()

    record = SparePartInbound(
        spare_part_id=part_id,
        quantity=quantity,
        unit_price=unit_price,
        batch_no=batch_no,
        inbound_date=parsed_date or dt.datetime.now(),
        remark=remark,
        created_by=current_user.username,
    )
    db.add(record)
    log_action(db, current_user.username, "inbound_spare_part", "spare_part", part_id,
               f"入库 {quantity} 件")
    db.commit()
    db.refresh(record)
    return record


def list_inbounds(db: Session, part_id: int) -> List[SparePartInbound]:
    """Return inbound records for a spare part."""
    return (
        db.query(SparePartInbound)
        .filter(SparePartInbound.spare_part_id == part_id)
        .order_by(SparePartInbound.inbound_date.desc(), SparePartInbound.id.desc())
        .all()
    )


# ── Consumption ────────────────────────────────────────────────────────────


def consume_spare_part(
    db: Session,
    part_id: int,
    *,
    quantity: int,
    maintenance_record_id: Optional[int] = None,
    batch_no: Optional[str] = None,
    remark: Optional[str] = None,
    current_user: User,
) -> SparePartConsumption:
    """Record a consumption (usage) of a spare part."""
    part = get_spare_part(db, part_id)
    if part.current_stock < quantity:
        raise ValueError(f"Stock insufficient: have {part.current_stock}, need {quantity}")

    part.current_stock -= quantity
    record = SparePartConsumption(
        spare_part_id=part_id,
        maintenance_record_id=maintenance_record_id,
        quantity=quantity,
        unit_price=part.weighted_avg_price,
        batch_no=batch_no,
        consumed_by=current_user.username,
        remark=remark,
    )
    db.add(record)
    log_action(db, current_user.username, "consume_spare_part", "spare_part", part_id,
               f"领用 {quantity} 件")
    db.commit()
    db.refresh(record)
    return record


def list_consumptions(db: Session, part_id: int) -> List[SparePartConsumption]:
    """Return consumption records for a spare part."""
    return (
        db.query(SparePartConsumption)
        .filter(SparePartConsumption.spare_part_id == part_id)
        .order_by(SparePartConsumption.consumed_at.desc(), SparePartConsumption.id.desc())
        .all()
    )


# ── Alerts ─────────────────────────────────────────────────────────────────


def list_alerts(db: Session, part_id: int, *, unresolved_only: bool = False) -> List[SparePartAlert]:
    """Return alerts for a spare part."""
    q = db.query(SparePartAlert).filter(SparePartAlert.spare_part_id == part_id)
    if unresolved_only:
        q = q.filter(SparePartAlert.is_resolved == False)
    return q.order_by(SparePartAlert.created_at.desc()).all()


def resolve_alert(db: Session, alert_id: int, *, current_user: User) -> None:
    """Mark an alert as resolved."""
    alert = db.query(SparePartAlert).filter(SparePartAlert.id == alert_id).first()
    if not alert:
        raise ValueError("Alert not found")
    alert.is_resolved = True
    alert.resolved_at = dt.datetime.now()
    log_action(db, current_user.username, "resolve_alert", "spare_part_alert", alert_id, "解决库存预警")
    db.commit()


def unresolved_alert_count(db: Session) -> int:
    """Return the count of unresolved spare-part alerts."""
    return db.query(SparePartAlert).filter(SparePartAlert.is_resolved == False).count()

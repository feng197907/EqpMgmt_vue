"""Maintenance service — maintenance plans, records, and repair records.

All database mutations go through this module so that audit logging is
enforced consistently.
"""

from datetime import date, datetime, timedelta
from typing import Optional, List

from sqlalchemy.orm import Session

from backend.app.models.maintenance import MaintenancePlan, MaintenanceRecord, DeviceRepairRecord
from backend.app.models.device import Device
from backend.app.models.user import User
from backend.app.services.audit_service import log_action


# ── Utility helpers ────────────────────────────────────────────────────────


def calc_next_due_date(performed_at: str, interval_days: int) -> str:
    """Calculate the next due date from a performed date string and interval."""
    if isinstance(performed_at, str):
        performed_at = datetime.strptime(performed_at, "%Y-%m-%d").date()
    next_due = performed_at + timedelta(days=int(interval_days))
    return next_due.strftime("%Y-%m-%d")


def calc_urgency(due_date: Optional[str]) -> str:
    """Calculate urgency level based on how close the due date is."""
    if not due_date:
        return "info"
    if isinstance(due_date, datetime):
        due = due_date.date()
    elif isinstance(due_date, date):
        due = due_date
    else:
        due = datetime.strptime(str(due_date), "%Y-%m-%d").date()
    delta = (due - date.today()).days
    if delta <= 0:
        return "danger"
    elif delta <= 3:
        return "warning"
    elif delta <= 7:
        return "info"
    return "success"


def _device_or_raise(db: Session, device_id: int) -> Device:
    device = db.query(Device).filter(Device.id == device_id, Device.is_deleted == False).first()
    if not device:
        raise ValueError("Device not found")
    return device


def _plan_to_out_dict(plan: MaintenancePlan) -> dict:
    """Convert a MaintenancePlan to a dict suitable for MaintenancePlanOut."""
    overdue_days = 0
    if plan.next_due_date:
        try:
            due = datetime.strptime(plan.next_due_date, "%Y-%m-%d").date()
            overdue_days = max((date.today() - due).days, 0)
        except (ValueError, TypeError):
            pass
    return {
        "id": plan.id,
        "device_id": plan.device_id,
        "maintenance_type": plan.maintenance_type,
        "interval_days": plan.interval_days,
        "next_due_date": plan.next_due_date,
        "is_active": bool(plan.is_active),
        "is_closed": bool(plan.is_closed),
        "closed_at": plan.closed_at,
        "closed_by": plan.closed_by,
        "close_reason": plan.close_reason,
        "created_by": plan.created_by,
        "created_at": plan.created_at,
        "updated_at": plan.updated_at,
        "urgency": calc_urgency(plan.next_due_date),
        "overdue_days": overdue_days,
    }


# ── Maintenance Plans ──────────────────────────────────────────────────────


def list_plans(
    db: Session, device_id: int, *, active_only: bool = True, include_closed: bool = False,
) -> List[dict]:
    """Return maintenance plans for a device as out-dicts."""
    _device_or_raise(db, device_id)
    q = db.query(MaintenancePlan).filter(MaintenancePlan.device_id == device_id)
    if active_only:
        q = q.filter(MaintenancePlan.is_active == True)
    if not include_closed:
        q = q.filter(MaintenancePlan.is_closed == False)
    plans = q.order_by(MaintenancePlan.next_due_date.asc()).all()
    return [_plan_to_out_dict(p) for p in plans]


def create_plan(
    db: Session,
    device_id: int,
    *,
    maintenance_type: str,
    interval_days: int,
    next_due_date: str,
    current_user: User,
) -> dict:
    """Create a maintenance plan for a device."""
    _device_or_raise(db, device_id)
    existing = db.query(MaintenancePlan).filter(
        MaintenancePlan.device_id == device_id,
        MaintenancePlan.maintenance_type == maintenance_type,
        MaintenancePlan.is_active == True,
    ).first()
    if existing:
        raise ValueError("Active plan of this type already exists")

    plan = MaintenancePlan(
        device_id=device_id,
        maintenance_type=maintenance_type,
        interval_days=interval_days,
        next_due_date=next_due_date,
        is_active=True,
        is_closed=False,
        created_by=current_user.username,
    )
    db.add(plan)
    db.flush()

    log_action(db, current_user.username, "create_maintenance_plan", "maintenance_plan", plan.id,
               "创建维护计划")
    db.commit()
    db.refresh(plan)
    return _plan_to_out_dict(plan)


def update_plan(
    db: Session,
    device_id: int,
    plan_id: int,
    *,
    maintenance_type: Optional[str] = None,
    interval_days: Optional[int] = None,
    next_due_date: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User,
) -> dict:
    """Update an existing maintenance plan."""
    _device_or_raise(db, device_id)
    plan = db.query(MaintenancePlan).filter(
        MaintenancePlan.id == plan_id, MaintenancePlan.device_id == device_id,
    ).first()
    if not plan:
        raise ValueError("Plan not found")

    before = {"interval_days": plan.interval_days, "next_due_date": plan.next_due_date}
    if maintenance_type is not None:
        plan.maintenance_type = maintenance_type
    if interval_days is not None:
        if interval_days < 1 or interval_days > 365:
            raise ValueError("interval_days must be between 1 and 365")
        plan.interval_days = interval_days
    if next_due_date is not None:
        plan.next_due_date = next_due_date
    if is_active is not None:
        plan.is_active = bool(is_active)
    plan.updated_at = datetime.utcnow()

    after = {"interval_days": plan.interval_days, "next_due_date": plan.next_due_date}
    log_action(
        db, current_user.username, "update_maintenance_plan", "maintenance_plan", plan.id,
        "更新维护计划", before_value=str(before), after_value=str(after),
    )
    db.commit()
    db.refresh(plan)
    return _plan_to_out_dict(plan)


def delete_plan(db: Session, device_id: int, plan_id: int, *, current_user: User) -> None:
    """Soft-delete (deactivate) a maintenance plan."""
    _device_or_raise(db, device_id)
    plan = db.query(MaintenancePlan).filter(
        MaintenancePlan.id == plan_id, MaintenancePlan.device_id == device_id,
    ).first()
    if not plan:
        raise ValueError("Plan not found")
    plan.is_active = False
    plan.updated_at = datetime.utcnow()
    log_action(db, current_user.username, "delete_maintenance_plan", "maintenance_plan", plan.id,
               "软删除维护计划")
    db.commit()


def close_plan(
    db: Session,
    device_id: int,
    plan_id: int,
    *,
    close_reason: str,
    current_user: User,
) -> None:
    """Close an overdue maintenance plan with a reason."""
    _device_or_raise(db, device_id)
    plan = db.query(MaintenancePlan).filter(
        MaintenancePlan.id == plan_id, MaintenancePlan.device_id == device_id,
    ).first()
    if not plan:
        raise ValueError("Plan not found")
    if not plan.is_active:
        raise ValueError("Plan is already deleted")
    if plan.is_closed:
        raise ValueError("Plan is already closed")
    if not plan.next_due_date or calc_urgency(plan.next_due_date) == "success":
        raise ValueError("Only overdue plans can be closed")
    if not close_reason:
        raise ValueError("close_reason is required")

    plan.is_closed = True
    plan.closed_at = datetime.utcnow()
    plan.closed_by = current_user.username
    plan.close_reason = close_reason
    plan.updated_at = datetime.utcnow()

    log_action(db, current_user.username, "close_maintenance_plan", "maintenance_plan", plan.id,
               "关闭维护计划", reason=close_reason)
    db.commit()


# ── Maintenance Records ────────────────────────────────────────────────────


def list_records(db: Session, device_id: int, plan_id: int) -> List[MaintenanceRecord]:
    """Return maintenance records for a plan."""
    _device_or_raise(db, device_id)
    return (
        db.query(MaintenanceRecord)
        .filter(MaintenanceRecord.plan_id == plan_id, MaintenanceRecord.device_id == device_id)
        .order_by(MaintenanceRecord.created_at.desc())
        .all()
    )


def create_record(
    db: Session,
    device_id: int,
    plan_id: int,
    *,
    content: str,
    result: str,
    parts_used: Optional[str] = None,
    current_user: User,
) -> MaintenanceRecord:
    """Create a maintenance record for a plan."""
    _device_or_raise(db, device_id)
    plan = db.query(MaintenancePlan).filter(
        MaintenancePlan.id == plan_id,
        MaintenancePlan.device_id == device_id,
        MaintenancePlan.is_active == True,
    ).first()
    if not plan:
        raise ValueError("Plan not found")
    if not content or not result:
        raise ValueError("content and result are required")

    performed_at = date.today().strftime("%Y-%m-%d")
    next_due = calc_next_due_date(performed_at, plan.interval_days)

    record = MaintenanceRecord(
        plan_id=plan.id,
        device_id=device_id,
        maintenance_type=plan.maintenance_type,
        content=content,
        result=result,
        performed_by=current_user.username,
        performed_at=performed_at,
        next_due_date=next_due,
        parts_used=parts_used,
    )
    db.add(record)
    if result == "qualified":
        plan.next_due_date = next_due
        plan.updated_at = datetime.utcnow()

    log_action(db, current_user.username, "create_maintenance_record", "maintenance_record",
               record.id, "提交维护记录")
    db.commit()
    db.refresh(record)
    return record


# ── Repair Records ─────────────────────────────────────────────────────────


def list_repair_records(db: Session, device_id: int) -> List[DeviceRepairRecord]:
    """Return repair records for a device."""
    _device_or_raise(db, device_id)
    return (
        db.query(DeviceRepairRecord)
        .filter(DeviceRepairRecord.device_id == device_id)
        .order_by(DeviceRepairRecord.created_at.desc())
        .all()
    )


def create_repair_record(
    db: Session,
    device_id: int,
    *,
    content: str,
    result: str,
    parts_used: Optional[str] = None,
    current_user: User,
) -> DeviceRepairRecord:
    """Create a repair record for a device."""
    _device_or_raise(db, device_id)
    if not content or not result:
        raise ValueError("content and result are required")

    record = DeviceRepairRecord(
        device_id=device_id,
        content=content,
        result=result,
        performed_by=current_user.username,
        performed_at=date.today().strftime("%Y-%m-%d"),
        parts_used=parts_used,
    )
    db.add(record)
    log_action(db, current_user.username, "create_repair_record", "repair_record", record.id,
               "提交维修记录")
    db.commit()
    db.refresh(record)
    return record


def delete_repair_record(
    db: Session,
    device_id: int,
    record_id: int,
    *,
    current_user: User,
) -> None:
    """Hard-delete a repair record."""
    _device_or_raise(db, device_id)
    record = db.query(DeviceRepairRecord).filter(
        DeviceRepairRecord.id == record_id, DeviceRepairRecord.device_id == device_id,
    ).first()
    if not record:
        raise ValueError("Repair record not found")
    log_action(db, current_user.username, "delete_repair_record", "repair_record", record_id,
               "删除维修记录")
    db.delete(record)
    db.commit()

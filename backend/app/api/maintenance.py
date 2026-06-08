from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db, get_current_user, require_admin
from backend.app.models.maintenance import MaintenancePlan, MaintenanceRecord, DeviceRepairRecord
from backend.app.models.device import Device
from backend.app.schemas.maintenance import (
    MaintenancePlanCreate,
    MaintenancePlanOut,
    MaintenancePlanUpdate,
    MaintenanceRecordCreate,
    MaintenanceRecordOut,
    RepairRecordCreate,
    RepairRecordOut,
)
from utils.audit import log_action
from utils.maintenance import calc_next_due_date, calc_urgency

router = APIRouter(prefix="/devices/{device_id}/maintenance")


def _to_plan_out(plan: MaintenancePlan) -> MaintenancePlanOut:
    return MaintenancePlanOut(
        id=plan.id,
        device_id=plan.device_id,
        maintenance_type=plan.maintenance_type,
        interval_days=plan.interval_days,
        next_due_date=plan.next_due_date,
        is_active=bool(plan.is_active),
        is_closed=bool(plan.is_closed),
        closed_at=plan.closed_at,
        closed_by=plan.closed_by,
        close_reason=plan.close_reason,
        created_by=plan.created_by,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
        urgency=calc_urgency(plan.next_due_date),
        overdue_days=max((date.today() - datetime.strptime(plan.next_due_date, "%Y-%m-%d").date()).days, 0) if plan.next_due_date else 0,
    )


def _load_device_or_404(db: Session, device_id: int) -> Device:
    device = db.query(Device).filter(Device.id == device_id, Device.is_deleted == False).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.get("/plans", response_model=List[MaintenancePlanOut])
def list_plans(device_id: int, db: Session = Depends(get_db), active_only: bool = True, include_closed: bool = False):
    _load_device_or_404(db, device_id)
    query = db.query(MaintenancePlan).filter(MaintenancePlan.device_id == device_id)
    if active_only:
        query = query.filter(MaintenancePlan.is_active == True)
    if not include_closed:
        query = query.filter(MaintenancePlan.is_closed == False)
    plans = query.order_by(MaintenancePlan.next_due_date.asc()).all()
    return [_to_plan_out(plan) for plan in plans]


@router.post("/plans", response_model=MaintenancePlanOut, dependencies=[Depends(require_admin)])
def create_plan(device_id: int, payload: MaintenancePlanCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _load_device_or_404(db, device_id)
    if payload.device_id != device_id:
        raise HTTPException(status_code=400, detail="device_id mismatch")
    existing = db.query(MaintenancePlan).filter(
        MaintenancePlan.device_id == device_id,
        MaintenancePlan.maintenance_type == payload.maintenance_type,
        MaintenancePlan.is_active == True,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Active plan of this type already exists")
    plan = MaintenancePlan(
        device_id=device_id,
        maintenance_type=payload.maintenance_type,
        interval_days=payload.interval_days,
        next_due_date=payload.next_due_date,
        is_active=True,
        is_closed=False,
        created_by=current_user.username,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    log_action(current_user.username, "create_maintenance_plan", "maintenance_plan", plan.id, "创建维护计划")
    return _to_plan_out(plan)


@router.put("/plans/{plan_id}", response_model=MaintenancePlanOut, dependencies=[Depends(require_admin)])
def update_plan(device_id: int, plan_id: int, payload: MaintenancePlanUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _load_device_or_404(db, device_id)
    plan = db.query(MaintenancePlan).filter(MaintenancePlan.id == plan_id, MaintenancePlan.device_id == device_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    before = {"interval_days": plan.interval_days, "next_due_date": plan.next_due_date}
    if payload.maintenance_type is not None:
        plan.maintenance_type = payload.maintenance_type
    if payload.interval_days is not None:
        if payload.interval_days < 1 or payload.interval_days > 365:
            raise HTTPException(status_code=400, detail="interval_days must be between 1 and 365")
        plan.interval_days = payload.interval_days
    if payload.next_due_date is not None:
        plan.next_due_date = payload.next_due_date
    if payload.is_active is not None:
        plan.is_active = bool(payload.is_active)
    plan.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(plan)
    log_action(current_user.username, "update_maintenance_plan", "maintenance_plan", plan.id, "更新维护计划", before_value=before, after_value={"interval_days": plan.interval_days, "next_due_date": plan.next_due_date})
    return _to_plan_out(plan)


@router.delete("/plans/{plan_id}", dependencies=[Depends(require_admin)])
def delete_plan(device_id: int, plan_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _load_device_or_404(db, device_id)
    plan = db.query(MaintenancePlan).filter(MaintenancePlan.id == plan_id, MaintenancePlan.device_id == device_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    plan.is_active = False
    plan.updated_at = datetime.utcnow()
    db.commit()
    log_action(current_user.username, "delete_maintenance_plan", "maintenance_plan", plan.id, "软删除维护计划")
    return {"message": "维护计划已删除"}


@router.post("/plans/{plan_id}/close", dependencies=[Depends(require_admin)])
def close_plan(device_id: int, plan_id: int, payload: dict | None = None, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _load_device_or_404(db, device_id)
    plan = db.query(MaintenancePlan).filter(MaintenancePlan.id == plan_id, MaintenancePlan.device_id == device_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    close_reason = (payload or {}).get("close_reason", "").strip()
    if not plan.is_active:
        raise HTTPException(status_code=400, detail="Plan is already deleted")
    if plan.is_closed:
        raise HTTPException(status_code=400, detail="Plan is already closed")
    if not plan.next_due_date or calc_urgency(plan.next_due_date) == "success":
        raise HTTPException(status_code=400, detail="Only overdue plans can be closed")
    if not close_reason:
        raise HTTPException(status_code=400, detail="close_reason is required")
    plan.is_closed = True
    plan.closed_at = datetime.utcnow()
    plan.closed_by = current_user.username
    plan.close_reason = close_reason
    plan.updated_at = datetime.utcnow()
    db.commit()
    log_action(current_user.username, "close_maintenance_plan", "maintenance_plan", plan.id, "关闭维护计划", reason=close_reason)
    return {"message": "维护计划已关闭"}


@router.get("/plans/{plan_id}/records", response_model=List[MaintenanceRecordOut])
def list_records(device_id: int, plan_id: int, db: Session = Depends(get_db)):
    _load_device_or_404(db, device_id)
    records = db.query(MaintenanceRecord).filter(MaintenanceRecord.plan_id == plan_id, MaintenanceRecord.device_id == device_id).order_by(MaintenanceRecord.created_at.desc()).all()
    return records


@router.post("/plans/{plan_id}/records", response_model=MaintenanceRecordOut, dependencies=[Depends(require_admin)])
def create_record(device_id: int, plan_id: int, payload: MaintenanceRecordCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _load_device_or_404(db, device_id)
    plan = db.query(MaintenancePlan).filter(MaintenancePlan.id == plan_id, MaintenancePlan.device_id == device_id, MaintenancePlan.is_active == True).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if not payload.content or not payload.result:
        raise HTTPException(status_code=400, detail="content and result are required")

    performed_at = date.today().strftime("%Y-%m-%d")
    next_due_date = calc_next_due_date(performed_at, plan.interval_days)
    record = MaintenanceRecord(
        plan_id=plan.id,
        device_id=device_id,
        maintenance_type=plan.maintenance_type,
        content=payload.content,
        result=payload.result,
        performed_by=current_user.username,
        performed_at=performed_at,
        next_due_date=next_due_date,
        parts_used=payload.parts_used,
    )
    db.add(record)
    if payload.result == "qualified":
        plan.next_due_date = next_due_date
        plan.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(record)
    log_action(current_user.username, "create_maintenance_record", "maintenance_record", record.id, "提交维护记录")
    return record


@router.get("/repair-records", response_model=List[RepairRecordOut])
def list_repair_records(device_id: int, db: Session = Depends(get_db)):
    _load_device_or_404(db, device_id)
    return db.query(DeviceRepairRecord).filter(DeviceRepairRecord.device_id == device_id).order_by(DeviceRepairRecord.created_at.desc()).all()


@router.post("/repair-records", response_model=RepairRecordOut, dependencies=[Depends(require_admin)])
def create_repair_record(device_id: int, payload: RepairRecordCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _load_device_or_404(db, device_id)
    if not payload.content or not payload.result:
        raise HTTPException(status_code=400, detail="content and result are required")
    record = DeviceRepairRecord(
        device_id=device_id,
        content=payload.content,
        result=payload.result,
        performed_by=current_user.username,
        performed_at=date.today().strftime("%Y-%m-%d"),
        parts_used=payload.parts_used,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    log_action(current_user.username, "create_repair_record", "repair_record", record.id, "提交维修记录")
    return record


@router.delete("/repair-records/{record_id}", dependencies=[Depends(require_admin)])
def delete_repair_record(device_id: int, record_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _load_device_or_404(db, device_id)
    record = db.query(DeviceRepairRecord).filter(DeviceRepairRecord.id == record_id, DeviceRepairRecord.device_id == device_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Repair record not found")
    db.delete(record)
    db.commit()
    log_action(current_user.username, "delete_repair_record", "repair_record", record_id, "删除维修记录")
    return {"message": "维修记录已删除"}

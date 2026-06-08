"""Maintenance routes — plans, records, and repair records.

All business logic is delegated to :mod:`backend.app.services.maintenance_service`.
Legacy Flask imports have been removed.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db, get_current_user, require_admin
from backend.app.models.user import User
from backend.app.schemas.maintenance import (
    MaintenancePlanCreate,
    MaintenancePlanOut,
    MaintenancePlanUpdate,
    MaintenanceRecordCreate,
    MaintenanceRecordOut,
    RepairRecordCreate,
    RepairRecordOut,
)
from backend.app.services import maintenance_service

router = APIRouter(prefix="/devices/{device_id}")


@router.get("/plans", response_model=List[MaintenancePlanOut])
def list_plans(
    device_id: int,
    db: Session = Depends(get_db),
    active_only: bool = True,
    include_closed: bool = False,
):
    """Return maintenance plans for a device."""
    try:
        return maintenance_service.list_plans(
            db, device_id, active_only=active_only, include_closed=include_closed,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/plans", response_model=MaintenancePlanOut, dependencies=[Depends(require_admin)])
def create_plan(
    device_id: int,
    payload: MaintenancePlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a maintenance plan for a device."""
    try:
        return maintenance_service.create_plan(
            db, device_id,
            maintenance_type=payload.maintenance_type,
            interval_days=payload.interval_days,
            next_due_date=payload.next_due_date,
            current_user=current_user,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/plans/{plan_id}", response_model=MaintenancePlanOut, dependencies=[Depends(require_admin)])
def update_plan(
    device_id: int,
    plan_id: int,
    payload: MaintenancePlanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a maintenance plan."""
    try:
        return maintenance_service.update_plan(
            db, device_id, plan_id,
            maintenance_type=payload.maintenance_type,
            interval_days=payload.interval_days,
            next_due_date=payload.next_due_date,
            is_active=payload.is_active,
            current_user=current_user,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/plans/{plan_id}", dependencies=[Depends(require_admin)])
def delete_plan(
    device_id: int,
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft-delete (deactivate) a maintenance plan."""
    try:
        maintenance_service.delete_plan(db, device_id, plan_id, current_user=current_user)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"message": "维护计划已删除"}


@router.post("/plans/{plan_id}/close", dependencies=[Depends(require_admin)])
def close_plan(
    device_id: int,
    plan_id: int,
    payload: Optional[dict] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Close an overdue maintenance plan with a reason."""
    close_reason = (payload or {}).get("close_reason", "").strip()
    try:
        maintenance_service.close_plan(
            db, device_id, plan_id, close_reason=close_reason, current_user=current_user,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"message": "维护计划已关闭"}


@router.get("/plans/{plan_id}/records", response_model=List[MaintenanceRecordOut])
def list_records(device_id: int, plan_id: int, db: Session = Depends(get_db)):
    """Return maintenance records for a plan."""
    try:
        return maintenance_service.list_records(db, device_id, plan_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/plans/{plan_id}/records", response_model=MaintenanceRecordOut, dependencies=[Depends(require_admin)])
def create_record(
    device_id: int,
    plan_id: int,
    payload: MaintenanceRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a maintenance record for a plan."""
    try:
        return maintenance_service.create_record(
            db, device_id, plan_id,
            content=payload.content,
            result=payload.result,
            parts_used=payload.parts_used,
            current_user=current_user,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/repair-records", response_model=List[RepairRecordOut])
def list_repair_records(device_id: int, db: Session = Depends(get_db)):
    """Return repair records for a device."""
    try:
        return maintenance_service.list_repair_records(db, device_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/repair-records", response_model=RepairRecordOut, dependencies=[Depends(require_admin)])
def create_repair_record(
    device_id: int,
    payload: RepairRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a repair record for a device."""
    try:
        return maintenance_service.create_repair_record(
            db, device_id,
            content=payload.content,
            result=payload.result,
            parts_used=payload.parts_used,
            current_user=current_user,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/repair-records/{record_id}", dependencies=[Depends(require_admin)])
def delete_repair_record(
    device_id: int,
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a repair record."""
    try:
        maintenance_service.delete_repair_record(db, device_id, record_id, current_user=current_user)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"message": "维修记录已删除"}

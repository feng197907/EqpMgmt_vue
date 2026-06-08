"""Spare-part routes — CRUD, inbound, consumption, and alerts.

All business logic is delegated to :mod:`backend.app.services.spare_part_service`.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db, get_current_user
from backend.app.models.user import User
from backend.app.schemas.spare_part import (
    SparePartCreate,
    SparePartUpdate,
    SparePartOut,
    InboundCreate,
    InboundOut,
    ConsumptionCreate,
    ConsumptionOut,
    AlertOut,
)
from backend.app.services import spare_part_service

router = APIRouter()


# ---- Spare Parts CRUD ----

@router.get("/", response_model=List[SparePartOut])
def list_spare_parts(
    category: Optional[str] = None,
    search: Optional[str] = None,
    stock_filter: Optional[str] = None,
    include_inactive: bool = False,
    db: Session = Depends(get_db),
):
    """Return spare parts with optional filters."""
    return spare_part_service.list_spare_parts(
        db, category=category, search=search, stock_filter=stock_filter,
        include_inactive=include_inactive,
    )


@router.get("/active-list")
def list_active_for_select(db: Session = Depends(get_db)):
    """Return lightweight list for dropdown selections."""
    return spare_part_service.list_active_for_select(db)


@router.post("/", response_model=SparePartOut)
def create_spare_part(
    payload: SparePartCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new spare part."""
    try:
        return spare_part_service.create_spare_part(
            db,
            name=payload.name,
            category=payload.category,
            specification=payload.specification,
            unit=payload.unit,
            brand=payload.brand,
            safety_stock_min=payload.safety_stock_min,
            safety_stock_max=payload.safety_stock_max,
            supplier_name=payload.supplier_name,
            supplier_contact=payload.supplier_contact,
            supplier_phone=payload.supplier_phone,
            remark=payload.remark,
            current_user=current_user,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{part_id}", response_model=SparePartOut)
def get_spare_part(part_id: int, db: Session = Depends(get_db)):
    """Return a spare part by ID."""
    try:
        return spare_part_service.get_spare_part(db, part_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.put("/{part_id}", response_model=SparePartOut)
def update_spare_part(
    part_id: int,
    payload: SparePartUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a spare part."""
    try:
        return spare_part_service.update_spare_part(
            db, part_id, current_user=current_user, **payload.model_dump(exclude_unset=True),
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/{part_id}")
def delete_spare_part(
    part_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft-delete a spare part."""
    try:
        spare_part_service.delete_spare_part(db, part_id, current_user=current_user)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"status": "deleted"}


# ---- Inbound ----

@router.post("/{part_id}/inbound", response_model=InboundOut)
def inbound_spare_part(
    part_id: int,
    payload: InboundCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Record an inbound (restocking) for a spare part."""
    try:
        return spare_part_service.inbound_spare_part(
            db, part_id,
            quantity=payload.quantity,
            unit_price=payload.unit_price,
            batch_no=payload.batch_no,
            inbound_date=payload.inbound_date,
            remark=payload.remark,
            current_user=current_user,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{part_id}/inbounds", response_model=List[InboundOut])
def list_inbounds(part_id: int, db: Session = Depends(get_db)):
    """Return inbound records for a spare part."""
    return spare_part_service.list_inbounds(db, part_id)


# ---- Consumption ----

@router.post("/{part_id}/consumption", response_model=ConsumptionOut)
def consume_spare_part(
    part_id: int,
    payload: ConsumptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Record a consumption (usage) of a spare part."""
    try:
        return spare_part_service.consume_spare_part(
            db, part_id,
            quantity=payload.quantity,
            maintenance_record_id=payload.maintenance_record_id,
            batch_no=payload.batch_no,
            remark=payload.remark,
            current_user=current_user,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{part_id}/consumptions", response_model=List[ConsumptionOut])
def list_consumptions(part_id: int, db: Session = Depends(get_db)):
    """Return consumption records for a spare part."""
    return spare_part_service.list_consumptions(db, part_id)


# ---- Alerts ----

@router.get("/{part_id}/alerts", response_model=List[AlertOut])
def list_alerts(part_id: int, unresolved_only: bool = False, db: Session = Depends(get_db)):
    """Return alerts for a spare part."""
    return spare_part_service.list_alerts(db, part_id, unresolved_only=unresolved_only)


@router.post("/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Mark an alert as resolved."""
    try:
        spare_part_service.resolve_alert(db, alert_id, current_user=current_user)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"status": "resolved"}


@router.get("/alerts-list/unresolved-count")
def unresolved_alert_count(db: Session = Depends(get_db)):
    """Return the count of unresolved spare-part alerts."""
    count = spare_part_service.unresolved_alert_count(db)
    return {"count": count}

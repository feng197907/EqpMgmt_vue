"""Device management routes — CRUD for devices.

All business logic is delegated to :mod:`backend.app.services.device_service`.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db, require_admin, get_current_user
from backend.app.models.user import User
from backend.app.schemas.device import DeviceCreate, DeviceOut, DeviceUpdate
from backend.app.services import device_service

router = APIRouter()


@router.get("/", response_model=List[DeviceOut])
def list_devices(show_inactive: bool = False, db: Session = Depends(get_db)):
    """Return all non-deleted devices."""
    return device_service.list_devices(db, show_inactive=show_inactive)


@router.get("/{device_id}", response_model=DeviceOut)
def get_device(device_id: int, db: Session = Depends(get_db)):
    """Return a single device by ID."""
    try:
        return device_service.get_device(db, device_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/", response_model=DeviceOut, dependencies=[Depends(require_admin)])
def create_device(payload: DeviceCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Create a new device."""
    try:
        return device_service.create_device(
            db,
            device_code=payload.device_code,
            device_name=payload.device_name,
            model=payload.model,
            location=payload.location,
            current_user=current_user,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/{device_id}", response_model=DeviceOut, dependencies=[Depends(require_admin)])
def update_device(
    device_id: int,
    payload: DeviceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing device.  If status is being changed a
    device-change request is automatically created.
    """
    try:
        device = device_service.get_device(db, device_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    # If status is being changed, create a change request
    new_status = payload.status
    if new_status is not None and new_status != device.status:
        from backend.app.services import device_change_service
        try:
            device_change_service.create_change_request(
                db,
                device_id=device_id,
                new_status=new_status,
                reason=f"Status change via device update API",
                current_user=current_user,
            )
        except ValueError:
            pass  # Non-critical — still proceed with the update

    try:
        return device_service.update_device(
            db,
            device_id,
            device_code=payload.device_code,
            device_name=payload.device_name,
            model=payload.model,
            location=payload.location,
            status=payload.status,
            current_user=current_user,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/{device_id}", dependencies=[Depends(require_admin)])
def delete_device(device_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Soft-delete a device."""
    try:
        device_service.delete_device(db, device_id, current_user=current_user)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"status": "deleted"}

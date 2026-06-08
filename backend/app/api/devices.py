from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db, require_admin
from backend.app.models.device import Device
from backend.app.schemas.device import DeviceCreate, DeviceOut, DeviceUpdate

router = APIRouter()


@router.get("/", response_model=List[DeviceOut])
def list_devices(show_inactive: bool = False, db: Session = Depends(get_db)):
    q = db.query(Device).filter(Device.is_deleted == False)
    if not show_inactive:
        q = q.filter(Device.status == "active")
    devices = q.all()
    return devices


@router.get("/{device_id}", response_model=DeviceOut)
def get_device(device_id: int, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id, Device.is_deleted == False).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.post("/", response_model=DeviceOut, dependencies=[Depends(require_admin)])
def create_device(payload: DeviceCreate, db: Session = Depends(get_db)):
    existing = db.query(Device).filter(Device.device_code == payload.device_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Device code already exists")
    device = Device(**payload.dict())
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


@router.put("/{device_id}", response_model=DeviceOut, dependencies=[Depends(require_admin)])
def update_device(device_id: int, payload: DeviceUpdate, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id, Device.is_deleted == False).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(device, k, v)
    db.commit()
    db.refresh(device)
    return device


@router.delete("/{device_id}", dependencies=[Depends(require_admin)])
def delete_device(device_id: int, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id, Device.is_deleted == False).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    device.status = "inactive"
    device.is_deleted = True
    db.commit()
    return {"status": "deleted"}

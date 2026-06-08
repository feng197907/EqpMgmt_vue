"""Device service — device CRUD, status-change request triggering, and audit.

All database mutations go through this module so that audit logging is
enforced consistently.
"""

from typing import Optional, List

from sqlalchemy.orm import Session

from backend.app.models.device import Device
from backend.app.models.user import User
from backend.app.services.audit_service import log_action


# ── Helpers ────────────────────────────────────────────────────────────────


def _get_device_or_raise(db: Session, device_id: int) -> Device:
    """Return an active (non-deleted) device or raise ``ValueError``."""
    device = db.query(Device).filter(Device.id == device_id, Device.is_deleted == False).first()
    if not device:
        raise ValueError("Device not found")
    return device


# ── CRUD ───────────────────────────────────────────────────────────────────


def list_devices(db: Session, *, show_inactive: bool = False) -> List[Device]:
    """Return all non-deleted devices, optionally including inactive ones."""
    q = db.query(Device).filter(Device.is_deleted == False)
    if not show_inactive:
        q = q.filter(Device.status == "active")
    return q.all()


def get_device(db: Session, device_id: int) -> Device:
    """Return a single device by ID."""
    return _get_device_or_raise(db, device_id)


def create_device(
    db: Session,
    *,
    device_code: str,
    device_name: Optional[str] = None,
    model: Optional[str] = None,
    location: Optional[str] = None,
    current_user: Optional[User] = None,
) -> Device:
    """Create a new device.  Raises ``ValueError`` if the code is duplicated."""
    existing = db.query(Device).filter(Device.device_code == device_code).first()
    if existing:
        raise ValueError("Device code already exists")

    device = Device(
        device_code=device_code,
        device_name=device_name,
        model=model,
        location=location,
        status="active",
    )
    db.add(device)
    db.flush()

    operator = current_user.username if current_user else "system"
    log_action(db, operator, "create_device", "device", device.id, f"创建设备 {device_code}")

    db.commit()
    db.refresh(device)
    return device


def update_device(
    db: Session,
    device_id: int,
    *,
    device_code: Optional[str] = None,
    device_name: Optional[str] = None,
    model: Optional[str] = None,
    location: Optional[str] = None,
    status: Optional[str] = None,
    current_user: Optional[User] = None,
) -> Device:
    """Update an existing device.  Only non-None fields are modified."""
    device = _get_device_or_raise(db, device_id)

    before = {"device_code": device.device_code, "status": device.status}
    if device_code is not None:
        device.device_code = device_code
    if device_name is not None:
        device.device_name = device_name
    if model is not None:
        device.model = model
    if location is not None:
        device.location = location
    if status is not None:
        device.status = status
    after = {"device_code": device.device_code, "status": device.status}

    operator = current_user.username if current_user else "system"
    log_action(
        db,
        operator,
        "update_device",
        "device",
        device.id,
        f"更新设备 {device.device_code}",
        before_value=str(before),
        after_value=str(after),
    )

    db.commit()
    db.refresh(device)
    return device


def delete_device(
    db: Session,
    device_id: int,
    *,
    current_user: Optional[User] = None,
) -> None:
    """Soft-delete a device (set ``is_deleted=True`` and ``status=inactive``)."""
    device = _get_device_or_raise(db, device_id)
    device.status = "inactive"
    device.is_deleted = True

    operator = current_user.username if current_user else "system"
    log_action(db, operator, "delete_device", "device", device.id, f"删除设备 {device.device_code}")

    db.commit()

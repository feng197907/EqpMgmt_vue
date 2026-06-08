"""Device status-change service — request/approval workflow and audit.

Manages the lifecycle of device status-change requests (pending → approved /
rejected).
"""

from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Session

from backend.app.models.device_change import DeviceStatusRequest
from backend.app.models.device import Device
from backend.app.models.user import User
from backend.app.services.audit_service import log_action


# ── Query ──────────────────────────────────────────────────────────────────


def list_change_requests(
    db: Session,
    *,
    status: Optional[str] = None,
    device_id: Optional[int] = None,
) -> List[DeviceStatusRequest]:
    """Return device status-change requests, optionally filtered."""
    q = db.query(DeviceStatusRequest)
    if status:
        q = q.filter(DeviceStatusRequest.status == status)
    if device_id:
        q = q.filter(DeviceStatusRequest.device_id == device_id)
    return q.order_by(DeviceStatusRequest.created_at.desc()).all()


def get_change_request(db: Session, request_id: int) -> DeviceStatusRequest:
    """Return a device status-change request or raise ``ValueError``."""
    req = db.query(DeviceStatusRequest).filter(DeviceStatusRequest.id == request_id).first()
    if not req:
        raise ValueError("Change request not found")
    return req


# ── Create ─────────────────────────────────────────────────────────────────


def create_change_request(
    db: Session,
    *,
    device_id: int,
    new_status: str,
    reason: Optional[str] = None,
    current_user: User,
) -> DeviceStatusRequest:
    """Create a device status-change request."""
    device = db.query(Device).filter(Device.id == device_id, Device.is_deleted == False).first()
    if not device:
        raise ValueError("Device not found")

    request = DeviceStatusRequest(
        device_id=device_id,
        new_status=new_status,
        reason=reason,
        requested_by=current_user.username,
    )
    db.add(request)
    db.flush()

    log_action(
        db,
        current_user.username,
        "create_device_change",
        "device_change",
        request.id,
        f"申请设备 {device.device_code} 状态从 {device.status} 变更为 {new_status}",
    )
    db.commit()
    db.refresh(request)
    return request


# ── Approve / Reject ───────────────────────────────────────────────────────


def approve_change_request(
    db: Session,
    request_id: int,
    *,
    comment: Optional[str] = None,
    current_user: User,
) -> DeviceStatusRequest:
    """Approve a device status-change request and update the device."""
    req = get_change_request(db, request_id)
    if req.status != "pending":
        raise ValueError("Request is not in pending status")

    req.status = "approved"
    req.decided_by = current_user.username
    req.decided_at = datetime.utcnow()
    req.comment = comment

    # Apply the status change to the device
    device = db.query(Device).filter(Device.id == req.device_id).first()
    if device:
        before = device.status
        device.status = req.new_status
        log_action(
            db,
            current_user.username,
            "approve_device_change",
            "device_change",
            request_id,
            f"批准设备状态变更: {device.device_code} {before} → {req.new_status}",
        )
    else:
        log_action(
            db,
            current_user.username,
            "approve_device_change",
            "device_change",
            request_id,
            "批准设备状态变更（设备未找到）",
        )

    db.commit()
    db.refresh(req)
    return req


def reject_change_request(
    db: Session,
    request_id: int,
    *,
    comment: Optional[str] = None,
    current_user: User,
) -> DeviceStatusRequest:
    """Reject a device status-change request."""
    req = get_change_request(db, request_id)
    if req.status != "pending":
        raise ValueError("Request is not in pending status")

    req.status = "rejected"
    req.decided_by = current_user.username
    req.decided_at = datetime.utcnow()
    req.comment = comment

    log_action(
        db,
        current_user.username,
        "reject_device_change",
        "device_change",
        request_id,
        f"拒绝设备状态变更请求 {request_id}",
    )
    db.commit()
    db.refresh(req)
    return req

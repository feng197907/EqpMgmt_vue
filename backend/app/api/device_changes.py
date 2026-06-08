"""Device status-change routes — create, list, approve/reject change requests.

Creation is allowed for equipment engineers and admins; approval/rejection
requires admin or QA manager role.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db, get_current_user, require_role
from backend.app.models.user import User
from backend.app.schemas.device_change import DeviceChangeCreate, DeviceChangeOut, DeviceChangeDecision
from backend.app.services import device_change_service

router = APIRouter()


@router.get("/", response_model=list[DeviceChangeOut])
def list_change_requests(
    status: Optional[str] = None,
    device_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List device status-change requests."""
    return device_change_service.list_change_requests(db, status=status, device_id=device_id)


@router.post("/", response_model=DeviceChangeOut)
def create_change_request(
    payload: DeviceChangeCreate,
    db: Session = Depends(get_db),
    current_user: User = require_role("admin", "equipment_engineer"),
):
    """Create a device status-change request."""
    try:
        return device_change_service.create_change_request(
            db,
            device_id=payload.device_id,
            new_status=payload.new_status,
            reason=payload.reason,
            current_user=current_user,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{request_id}/decide", response_model=DeviceChangeOut)
def decide_change_request(
    request_id: int,
    payload: DeviceChangeDecision,
    db: Session = Depends(get_db),
    current_user: User = require_role("admin", "qa_manager"),
):
    """Approve or reject a device status-change request.

    The ``action`` field in the request body determines the outcome:
    ``"approve"`` or ``"reject"``.
    """
    action = getattr(payload, "action", "approve") or "approve"
    try:
        if action == "approve":
            return device_change_service.approve_change_request(
                db, request_id, comment=payload.comment, current_user=current_user,
            )
        else:
            return device_change_service.reject_change_request(
                db, request_id, comment=payload.comment, current_user=current_user,
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

"""Electronic-signature routes — query, create, and soft-delete signatures.

Implements 21 CFR Part 11 compliance: signatures are immutable after
creation (soft-delete only).  Creating a signature requires the user's
password to be re-verified as an anti-fraud measure.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db, get_current_user, require_role
from backend.app.models.user import User
from backend.app.schemas.esign import ESignCreate, ESignatureOut
from backend.app.services import esign_service
from backend.app.services.auth_service import verify_password

router = APIRouter()


class ESignCreateWithPassword(ESignCreate):
    """Extended creation schema that includes the signer's password for
    identity verification (21 CFR Part 11 requirement).
    """
    password: str = ""


@router.get("/", response_model=list[ESignatureOut])
def list_signatures(
    record_type: Optional[str] = None,
    record_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Query electronic signatures, optionally filtered by record."""
    return esign_service.list_signatures(db, record_type=record_type, record_id=record_id)


@router.post("/", response_model=ESignatureOut)
def create_signature(
    payload: ESignCreateWithPassword,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = require_role("admin", "qa_manager", "validation_engineer"),
):
    """Create an electronic signature after re-verifying the user's password.

    The ``password`` field in the request body is required for identity
    verification.  This is a 21 CFR Part 11 requirement to prevent
    unauthorised signing.
    """
    if not payload.password or not verify_password(payload.password, current_user.password):
        raise HTTPException(status_code=403, detail="密码验证失败，无法签名")

    # Get client IP for audit trail
    ip_address = request.client.host if request.client else None

    try:
        return esign_service.create_signature(
            db,
            record_type=payload.record_type,
            record_id=payload.record_id,
            sign_meaning=payload.sign_meaning,
            sign_meaning_label=payload.sign_meaning_label,
            remark=payload.remark,
            ip_address=ip_address,
            current_user=current_user,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/{signature_id}")
def soft_delete_signature(
    signature_id: int,
    db: Session = Depends(get_db),
    current_user: User = require_role("admin", "qa_manager", "validation_engineer"),
):
    """Soft-delete an electronic signature (compliance: never hard-delete)."""
    try:
        esign_service.soft_delete_signature(db, signature_id, current_user=current_user)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"status": "deleted"}

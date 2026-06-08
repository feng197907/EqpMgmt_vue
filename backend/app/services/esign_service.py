"""Electronic-signature service — signature recording, verification, and locking.

Implements 21 CFR Part 11 compliance features:
- Each signature is immutable after creation (soft-delete only via ``is_deleted``).
- The ``(record_type, record_id, sign_meaning)`` tuple acts as a locking
  table to prevent duplicate signatures with the same meaning.
"""

from typing import Optional, List

from sqlalchemy.orm import Session

from backend.app.models.esign import ElectronicSignature
from backend.app.models.user import User
from backend.app.services.audit_service import log_action


def create_signature(
    db: Session,
    *,
    record_type: str,
    record_id: int,
    sign_meaning: str,
    sign_meaning_label: str,
    remark: Optional[str] = None,
    ip_address: Optional[str] = None,
    current_user: User,
) -> ElectronicSignature:
    """Create an electronic signature.

    Raises ``ValueError`` if a non-deleted signature with the same
    ``(record_type, record_id, sign_meaning)`` already exists (lock check).
    """
    # Locking check: prevent duplicate active signatures
    existing = db.query(ElectronicSignature).filter(
        ElectronicSignature.record_type == record_type,
        ElectronicSignature.record_id == record_id,
        ElectronicSignature.sign_meaning == sign_meaning,
        ElectronicSignature.is_deleted == False,
    ).first()
    if existing:
        raise ValueError(
            f"Signature with meaning '{sign_meaning}' already exists for "
            f"{record_type}/{record_id}"
        )

    display_name = getattr(current_user, "display_name", None) or current_user.username
    signature = ElectronicSignature(
        record_type=record_type,
        record_id=record_id,
        signed_by=current_user.username,
        signed_by_display=display_name,
        sign_meaning=sign_meaning,
        sign_meaning_label=sign_meaning_label,
        ip_address=ip_address,
        remark=remark,
    )
    db.add(signature)
    db.flush()

    log_action(
        db,
        current_user.username,
        "create_signature",
        "electronic_signature",
        signature.id,
        f"签名 {sign_meaning_label} ({sign_meaning}) on {record_type}/{record_id}",
        ip_address=ip_address,
    )
    db.commit()
    db.refresh(signature)
    return signature


def list_signatures(
    db: Session,
    *,
    record_type: Optional[str] = None,
    record_id: Optional[int] = None,
) -> List[ElectronicSignature]:
    """Return electronic signatures, optionally filtered by record."""
    q = db.query(ElectronicSignature).filter(ElectronicSignature.is_deleted == False)
    if record_type:
        q = q.filter(ElectronicSignature.record_type == record_type)
    if record_id is not None:
        q = q.filter(ElectronicSignature.record_id == record_id)
    return q.order_by(ElectronicSignature.signed_at.desc()).all()


def verify_signature(db: Session, signature_id: int) -> ElectronicSignature:
    """Verify an electronic signature exists and is not deleted.

    Raises ``ValueError`` if the signature is not found or has been deleted.
    """
    sig = db.query(ElectronicSignature).filter(ElectronicSignature.id == signature_id).first()
    if not sig:
        raise ValueError("Signature not found")
    if sig.is_deleted:
        raise ValueError("Signature has been deleted")
    return sig


def soft_delete_signature(
    db: Session,
    signature_id: int,
    *,
    current_user: User,
) -> None:
    """Soft-delete an electronic signature (compliance: never hard-delete)."""
    sig = db.query(ElectronicSignature).filter(ElectronicSignature.id == signature_id).first()
    if not sig:
        raise ValueError("Signature not found")
    sig.is_deleted = True
    log_action(
        db,
        current_user.username,
        "delete_signature",
        "electronic_signature",
        signature_id,
        f"删除签名 on {sig.record_type}/{sig.record_id}",
    )
    db.commit()

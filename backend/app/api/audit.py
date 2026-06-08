"""Audit, settings, and search routes.

All business logic is delegated to corresponding Service modules.
This router keeps the same URL structure as before but no longer
contains inline DB operations.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db, get_current_user
from backend.app.models.user import User
from backend.app.schemas.audit import AuditLogOut
from backend.app.schemas.settings import SettingOut, SettingUpdate
from backend.app.services import audit_service
from backend.app.services import settings_service
from backend.app.services import search_service

router = APIRouter()


# ---- Audit Logs ----

@router.get("/audit-logs", response_model=List[AuditLogOut])
def list_audit_logs(
    user: Optional[str] = None,
    action: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return paginated audit logs."""
    return audit_service.query_audit_logs(db, user=user, action=action, page=page, page_size=page_size)


# ---- System Settings ----

@router.get("/settings", response_model=List[SettingOut])
def list_settings(db: Session = Depends(get_db)):
    """Return all system settings."""
    return settings_service.list_settings(db)


@router.put("/settings/{setting_key}", response_model=SettingOut)
def update_setting(
    setting_key: str,
    payload: SettingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update (or create) a system setting."""
    return settings_service.update_setting(
        db, setting_key, setting_value=payload.setting_value, current_user=current_user,
    )


# ---- Global Search ----

@router.get("/search")
def global_search(
    q: str = Query(..., min_length=1),
    type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Unified search across devices, documents, and borrow records."""
    return search_service.global_search(db, q=q, type=type)

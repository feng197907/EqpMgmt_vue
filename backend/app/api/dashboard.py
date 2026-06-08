"""Dashboard routes — aggregated statistics for the main dashboard.

Accessible to any authenticated user.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db, get_current_user
from backend.app.models.user import User
from backend.app.schemas.dashboard import DashboardStats
from backend.app.services import dashboard_service

router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Return aggregated dashboard statistics."""
    return dashboard_service.get_dashboard_stats(db)

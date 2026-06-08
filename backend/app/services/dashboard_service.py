"""Dashboard service — aggregated statistics for the main dashboard.

Queries multiple models to build a unified stats payload.
"""

from sqlalchemy.orm import Session

from backend.app.models.device import Device
from backend.app.models.maintenance import MaintenancePlan
from backend.app.models.approval import ApprovalRequest
from backend.app.models.borrowing import BorrowRecord
from backend.app.models.spare_part import SparePart, SparePartAlert
from backend.app.models.password_reset import PasswordResetRequest
from backend.app.models.device_change import DeviceStatusRequest
from backend.app.schemas.dashboard import DashboardStats


def get_dashboard_stats(db: Session) -> DashboardStats:
    """Compute and return aggregated dashboard statistics."""
    total_devices = db.query(Device).filter(Device.is_deleted == False).count()
    active_devices = db.query(Device).filter(Device.is_deleted == False, Device.status == "active").count()

    # Overdue maintenance: plans that are active, not closed, and next_due_date < today
    from datetime import date
    overdue_maintenance = 0
    plans = db.query(MaintenancePlan).filter(
        MaintenancePlan.is_active == True,
        MaintenancePlan.is_closed == False,
    ).all()
    for plan in plans:
        if plan.next_due_date:
            try:
                due = date.fromisoformat(plan.next_due_date)
                if due < date.today():
                    overdue_maintenance += 1
            except (ValueError, TypeError):
                pass

    pending_approvals = db.query(ApprovalRequest).filter(ApprovalRequest.status == "pending").count()
    borrowed_documents = db.query(BorrowRecord).filter(BorrowRecord.status == "borrowed").count()

    low_stock_parts = db.query(SparePart).filter(
        SparePart.is_active == True,
        SparePart.current_stock > 0,
        SparePart.current_stock <= SparePart.safety_stock_min,
    ).count()

    unresolved_alerts = db.query(SparePartAlert).filter(SparePartAlert.is_resolved == False).count()
    pending_password_resets = db.query(PasswordResetRequest).filter(
        PasswordResetRequest.status == "pending"
    ).count()
    pending_device_changes = db.query(DeviceStatusRequest).filter(
        DeviceStatusRequest.status == "pending"
    ).count()

    return DashboardStats(
        total_devices=total_devices,
        active_devices=active_devices,
        overdue_maintenance=overdue_maintenance,
        pending_approvals=pending_approvals,
        borrowed_documents=borrowed_documents,
        low_stock_parts=low_stock_parts,
        unresolved_alerts=unresolved_alerts,
        pending_password_resets=pending_password_resets,
        pending_device_changes=pending_device_changes,
    )

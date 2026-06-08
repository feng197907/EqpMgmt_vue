"""Dashboard Pydantic schemas.

Provides the response schema for the dashboard statistics endpoint.
"""

from typing import Optional

from pydantic import BaseModel


class DashboardStats(BaseModel):
    """Aggregated statistics for the main dashboard."""
    total_devices: int = 0
    active_devices: int = 0
    overdue_maintenance: int = 0
    pending_approvals: int = 0
    borrowed_documents: int = 0
    low_stock_parts: int = 0
    unresolved_alerts: int = 0
    pending_password_resets: int = 0
    pending_device_changes: int = 0

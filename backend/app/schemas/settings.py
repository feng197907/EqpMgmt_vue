"""System settings Pydantic schemas.

Moved from ``audit.py`` into a dedicated module per the architecture design.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict


class SettingOut(BaseModel):
    """Schema for a system-setting response."""
    id: int
    setting_key: str
    setting_value: Optional[str] = None
    description: Optional[str] = None
    updated_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SettingUpdate(BaseModel):
    """Schema for updating a system setting."""
    setting_value: str

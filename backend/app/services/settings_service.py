"""Settings service — system settings CRUD and audit.

Manages key-value system settings stored in the ``system_settings`` table.
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from backend.app.models.audit import SystemSetting
from backend.app.models.user import User
from backend.app.services.audit_service import log_action


def list_settings(db: Session) -> List[SystemSetting]:
    """Return all system settings."""
    return db.query(SystemSetting).all()


def get_setting(db: Session, setting_key: str) -> Optional[SystemSetting]:
    """Return a single setting by key, or None."""
    return db.query(SystemSetting).filter(SystemSetting.setting_key == setting_key).first()


def get_setting_value(db: Session, setting_key: str, default: Optional[str] = None) -> Optional[str]:
    """Return the value of a setting, or *default* if it does not exist."""
    setting = get_setting(db, setting_key)
    return setting.setting_value if setting else default


def update_setting(
    db: Session,
    setting_key: str,
    *,
    setting_value: str,
    current_user: User,
) -> SystemSetting:
    """Update (or create) a system setting.

    If the setting does not yet exist it is created automatically.
    """
    setting = db.query(SystemSetting).filter(SystemSetting.setting_key == setting_key).first()

    if not setting:
        setting = SystemSetting(setting_key=setting_key)
        db.add(setting)

    before = setting.setting_value
    setting.setting_value = setting_value
    setting.updated_by = current_user.username

    log_action(
        db,
        current_user.username,
        "update_setting",
        "system_setting",
        setting.id,
        f"更新设置 {setting_key}",
        before_value=str(before),
        after_value=str(setting_value),
    )
    db.commit()
    db.refresh(setting)
    return setting

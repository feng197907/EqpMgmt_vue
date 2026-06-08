"""RBAC permission definitions and role constants.

Defines the seven standard DMS roles and convenience role-set constants.
This module has **no** dependency on ``api.deps`` or the database layer,
so it can safely be imported by any module (including ``api.deps`` itself)
without creating circular imports.

The actual ``require_role()`` FastAPI dependency factory lives in
:mod:`backend.app.api.deps` because it needs ``get_current_user``.
"""

from typing import FrozenSet, List


# ── Role Definitions ──────────────────────────────────────────────────────

ROLES: List[str] = [
    "admin",
    "qa_manager",
    "equipment_engineer",
    "validation_engineer",
    "archivist",
    "production_supervisor",
    "metrology_engineer",
]

# Convenience sets for common role groupings
ROLE_ADMIN: FrozenSet[str] = frozenset({"admin"})
ROLE_QA: FrozenSet[str] = frozenset({"admin", "qa_manager"})
ROLE_EQUIPMENT: FrozenSet[str] = frozenset({"admin", "equipment_engineer"})
ROLE_VALIDATION: FrozenSet[str] = frozenset({"admin", "validation_engineer"})
ROLE_ARCHIVIST: FrozenSet[str] = frozenset({"admin", "archivist"})
ROLE_PRODUCTION: FrozenSet[str] = frozenset({"admin", "production_supervisor"})
ROLE_METROLOGY: FrozenSet[str] = frozenset({"admin", "metrology_engineer"})

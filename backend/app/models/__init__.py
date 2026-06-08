"""Models package — import all model modules so that Alembic auto-generate
can discover every SQLAlchemy model via ``Base.metadata``.

Each model module registers its classes with the shared ``Base`` simply
by being imported.  The ``# noqa: F401`` suppressions tell flake8 that
the side-effect import is intentional.
"""

from backend.app.models.user import User  # noqa: F401
from backend.app.models.device import Device  # noqa: F401
from backend.app.models.document import Document  # noqa: F401
from backend.app.models.maintenance import (  # noqa: F401
    MaintenancePlan,
    MaintenanceRecord,
    DeviceRepairRecord,
)
from backend.app.models.approval import ApprovalRequest, ApprovalStep  # noqa: F401
from backend.app.models.audit import AuditLog, SystemSetting  # noqa: F401
from backend.app.models.borrowing import BorrowRecord  # noqa: F401
from backend.app.models.spare_part import (  # noqa: F401
    SparePart,
    SparePartInbound,
    SparePartConsumption,
    SparePartAlert,
)
from backend.app.models.esign import ElectronicSignature  # noqa: F401
from backend.app.models.device_change import DeviceStatusRequest  # noqa: F401
from backend.app.models.password_reset import PasswordResetRequest  # noqa: F401

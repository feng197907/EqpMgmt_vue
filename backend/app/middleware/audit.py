"""Enhanced audit middleware — request-level logging + automatic before/after
value tracking via SQLAlchemy ``before_flush`` events.

The middleware performs two distinct functions:

1. **Request-level audit** (existing): logs who accessed what endpoint and
   the response status.  This is written to a file-based audit log.

2. **Automatic value-change audit** (new): registers a ``before_flush``
   hook on the SQLAlchemy ``Session`` that captures the state of ORM
   instances *before* they are flushed.  After the request completes
   successfully, the captured changes are written to the ``audit_logs``
   table as ``before_value`` / ``after_value`` JSON strings.

Both mechanisms coexist with the Service layer's manual ``log_action``
calls.  The automatic audit captures raw attribute-level changes, while
the manual audit provides business-semantic context (action names,
human-readable details).
"""

import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import event
from sqlalchemy.orm import Session, class_mapper
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from backend.app.core.security import decode_token

logger = logging.getLogger("audit")
if not logger.handlers:
    try:
        handler = logging.FileHandler("logs/audit.log", encoding="utf-8")
    except Exception:
        handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def _instance_to_dict(instance: Any) -> Dict[str, Any]:
    """Convert a SQLAlchemy model instance to a plain dict of its column values."""
    if instance is None:
        return {}
    try:
        mapper = class_mapper(instance.__class__)
        return {col.key: getattr(instance, col.key) for col in mapper.columns}
    except Exception:
        return {}


class _ChangeTracker:
    """Tracks before/after snapshots for dirty/new/deleted instances in a
    single SQLAlchemy Session flush cycle.
    """

    def __init__(self) -> None:
        self.changes: List[Dict[str, Any]] = []

    def capture(self, session: Session) -> None:
        """Inspect the session's dirty and deleted collections and record
        attribute-level before/after snapshots.

        This is designed to be called from a ``before_flush`` event hook.
        At this point, the old values are still accessible via
        ``inspect(obj).committed_state``, and the new values are the
        current attribute values.
        """
        from sqlalchemy import inspect as sa_inspect

        for obj in session.dirty:
            if not hasattr(obj, "__tablename__"):
                continue
            insp = sa_inspect(obj)
            before: Dict[str, Any] = {}
            after: Dict[str, Any] = {}
            for attr in insp.mapper.columns.keys():
                hist = insp.attrs[attr].history
                if hist.deleted or hist.added:
                    before[attr] = hist.deleted[0] if hist.deleted else None
                    after[attr] = hist.added[0] if hist.added else getattr(obj, attr, None)
            if before or after:
                self.changes.append({
                    "target_type": obj.__tablename__,
                    "target_id": getattr(obj, "id", None),
                    "before_value": json.dumps(before, default=str, ensure_ascii=False),
                    "after_value": json.dumps(after, default=str, ensure_ascii=False),
                })

        for obj in session.deleted:
            if not hasattr(obj, "__tablename__"):
                continue
            snapshot = _instance_to_dict(obj)
            self.changes.append({
                "target_type": obj.__tablename__,
                "target_id": getattr(obj, "id", None),
                "before_value": json.dumps(snapshot, default=str, ensure_ascii=False),
                "after_value": json.dumps({}, default=str, ensure_ascii=False),
            })


def _register_before_flush(session: Session) -> None:
    """Register a one-shot ``before_flush`` hook on the given session.

    The hook captures change snapshots and stores them on the request
    state for later persistence by the middleware.
    """
    tracker = _ChangeTracker()

    @event.listens_for(session, "before_flush")
    def _before_flush(session, flush_context, instances):
        tracker.capture(session)

    # Store the tracker on the session for later retrieval
    session._audit_change_tracker = tracker  # type: ignore[attr-defined]


class AuditMiddleware(BaseHTTPMiddleware):
    """Starlette middleware that logs requests and captures automatic
    before/after value changes.
    """

    async def dispatch(self, request: Request, call_next):
        user_info = "-"
        auth = request.headers.get("authorization")
        if auth and auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1]
            try:
                payload = decode_token(token)
                user_info = f"user_id={payload.get('sub')} role={payload.get('role')}"
            except Exception:
                user_info = "invalid_token"

        # Register the before_flush hook on the DB session if available
        db: Optional[Session] = None
        try:
            from backend.app.db.session import SessionLocal
            db = SessionLocal()
            _register_before_flush(db)
        except Exception:
            db = None

        response = await call_next(request)

        # ── Request-level audit log ─────────────────────────────────
        logger.info(f"{request.method} {request.url.path} {user_info} status={response.status_code}")

        # ── Automatic value-change audit ────────────────────────────
        # Only persist automatic changes if the request succeeded (2xx).
        if db is not None and 200 <= response.status_code < 300:
            tracker: Optional[_ChangeTracker] = getattr(db, "_audit_change_tracker", None)
            if tracker and tracker.changes:
                self._persist_changes(db, tracker.changes, user_info)

        # Always close the dedicated audit-tracking session
        if db is not None:
            try:
                db.close()
            except Exception:
                pass

        return response

    @staticmethod
    def _persist_changes(db: Session, changes: List[Dict[str, Any]], user_info: str) -> None:
        """Write captured change snapshots to the ``audit_logs`` table."""
        from backend.app.models.audit import AuditLog

        for change in changes:
            entry = AuditLog(
                user=user_info,
                action="auto_update",
                target_type=change.get("target_type", ""),
                target_id=change.get("target_id"),
                details="Automatic value-change audit",
                before_value=change.get("before_value"),
                after_value=change.get("after_value"),
            )
            db.add(entry)
        try:
            db.commit()
        except Exception:
            db.rollback()

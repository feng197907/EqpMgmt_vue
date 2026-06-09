"""
Frontend JS error reporting endpoint.

POST /api/v1/log/js-error  (no authentication required)
Accepts a JSON payload describing a client-side JS error and writes
it to logs/js_error.log via the dedicated 'js_error' logger.
"""

import logging
import time
from pathlib import Path

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

router = APIRouter()

# ── js_error logger ────────────────────────────────────────────────────────
_LOG_DIR = Path(__file__).resolve().parent.parent.parent.parent / "logs"
_LOG_DIR.mkdir(exist_ok=True)

from logging.handlers import RotatingFileHandler

_js_formatter = logging.Formatter(
    "%(asctime)s | %(levelname)-8s | js_error | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

_js_handler = RotatingFileHandler(
    _LOG_DIR / "js_error.log",
    maxBytes=5 * 1024 * 1024,   # 5 MB
    backupCount=5,
    encoding="utf-8",
)
_js_handler.setLevel(logging.ERROR)
_js_handler.setFormatter(_js_formatter)

js_error_logger = logging.getLogger("js_error")
if not js_error_logger.handlers:
    js_error_logger.setLevel(logging.ERROR)
    js_error_logger.addHandler(_js_handler)
    js_error_logger.propagate = False   # don't bubble up to root logger


# ── Schema ─────────────────────────────────────────────────────────────────
class JsErrorPayload(BaseModel):
    message: str = Field(..., description="Error message")
    source: str | None = Field(None, description="Script URL or source")
    lineno: int | None = Field(None, description="Line number")
    colno: int | None = Field(None, description="Column number")
    stack: str | None = Field(None, description="Full stack trace")
    page: str | None = Field(None, description="Current page URL / route path")
    user_agent: str | None = Field(None, description="Browser user agent")
    timestamp: str | None = Field(None, description="ISO 8601 client timestamp")
    extra: dict | None = Field(None, description="Any extra context")


# ── Endpoint ───────────────────────────────────────────────────────────────
@router.post("/js-error", status_code=204)
async def receive_js_error(payload: JsErrorPayload, request: Request):
    """
    Receive a frontend JS error and persist it to logs/js_error.log.
    Returns 204 No Content — the client should not block on this call.
    """
    client_ip = request.client.host if request.client else "unknown"

    log_line = (
        f"[{payload.page or 'unknown_page'}] "
        f"[IP:{client_ip}] "
        f"{payload.message}"
    )
    if payload.source:
        log_line += f" | source={payload.source}:{payload.lineno}:{payload.colno}"
    if payload.stack:
        # Indent stack trace lines for readability in log file
        indented_stack = "\n    ".join(payload.stack.splitlines())
        log_line += f"\n    Stack:\n    {indented_stack}"
    if payload.timestamp:
        log_line += f"\n    client_ts={payload.timestamp}"

    js_error_logger.error(log_line)

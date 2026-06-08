from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import logging
from backend.app.services.auth_service import decode_token

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


class AuditMiddleware(BaseHTTPMiddleware):
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
        response = await call_next(request)
        logger.info(f"{request.method} {request.url.path} {user_info} status={response.status_code}")
        return response

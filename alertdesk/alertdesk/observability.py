"""Structured request logging that excludes credentials and request bodies."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        fields: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": record.getMessage(),
        }
        fields.update(getattr(record, "event_fields", {}))
        return json.dumps(fields, separators=(",", ":"), default=str)


def configure_logging() -> None:
    logger = logging.getLogger("alertdesk.http")
    if not any(getattr(handler, "_alertdesk_json", False) for handler in logger.handlers):
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        handler._alertdesk_json = True  # type: ignore[attr-defined]
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        started = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
            logging.getLogger("alertdesk.http").info(
                "http_request",
                extra={"event_fields": {
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": status_code,
                    "duration_ms": elapsed_ms,
                }},
            )

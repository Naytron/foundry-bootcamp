"""Small security and request-context middleware components."""

import asyncio
import secrets
import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from support_assistant.config import Settings


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach a correlation ID and baseline security headers."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("x-request-id", str(uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        response.headers["x-content-type-options"] = "nosniff"
        response.headers["referrer-policy"] = "no-referrer"
        response.headers["content-security-policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self'; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'none'; "
            "form-action 'self'"
        )
        return response


class AccessTokenMiddleware(BaseHTTPMiddleware):
    """Require a generated workshop bearer token for protected API routes."""

    def __init__(self, app: Callable[..., Awaitable[None]], settings: Settings) -> None:
        super().__init__(app)
        self._expected = settings.bootcamp_access_token.get_secret_value()

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not request.url.path.startswith("/api/chat"):
            return await call_next(request)

        authorization = request.headers.get("authorization", "")
        scheme, _, token = authorization.partition(" ")
        if scheme.casefold() != "bearer" or not secrets.compare_digest(token, self._expected):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "A valid bootcamp access token is required."},
                headers={"WWW-Authenticate": "Bearer"},
            )
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Apply a per-process request limit to the chat endpoint."""

    def __init__(self, app: Callable[..., Awaitable[None]], settings: Settings) -> None:
        super().__init__(app)
        self._limit = settings.rate_limit_requests
        self._window = settings.rate_limit_window_seconds
        self._requests: defaultdict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not request.url.path.startswith("/api/chat"):
            return await call_next(request)

        client = request.client.host if request.client else "unknown"
        now = time.monotonic()
        async with self._lock:
            attempts = self._requests[client]
            while attempts and attempts[0] <= now - self._window:
                attempts.popleft()
            if len(attempts) >= self._limit:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Rate limit exceeded. Try again shortly."},
                    headers={"Retry-After": str(self._window)},
                )
            attempts.append(now)

        return await call_next(request)

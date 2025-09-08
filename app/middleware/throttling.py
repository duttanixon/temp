import asyncio
import time
from fastapi import Request, status, FastAPI
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.utils.logger import get_logger
from starlette.middleware.base import BaseHTTPMiddleware  # Added import

logger = get_logger("api")

class GlobalThrottlingMiddleware(BaseHTTPMiddleware):  # Subclass BaseHTTPMiddleware
    """Middleware to limit total number of concurrent in-flight HTTP requests.

    Uses an asyncio.Semaphore to cap concurrency across all endpoints.
    Requests that cannot obtain a slot within the configured timeout receive
    HTTP 429 Too Many Requests.
    """

    def __init__(
        self,
        app: FastAPI,
        max_concurrent_requests: int | None = None,
        acquire_timeout_seconds: int | None = None,
    ) -> None:
        super().__init__(app)
        self.max_concurrent = max_concurrent_requests or settings.THROTTLE_MAX_CONCURRENT_REQUESTS
        self.acquire_timeout = acquire_timeout_seconds or settings.THROTTLE_ACQUIRE_TIMEOUT_SECONDS
        self._semaphore = asyncio.Semaphore(self.max_concurrent)

    async def dispatch(self, request: Request, call_next):  # Replaced __call__ with dispatch
        start_wait = time.perf_counter()
        try:
            await asyncio.wait_for(self._semaphore.acquire(), timeout=self.acquire_timeout)
            wait_duration = time.perf_counter() - start_wait
            if wait_duration > 0.250:
                logger.warning(
                    "Request waited %.3fs for concurrency slot (%s %s)",
                    wait_duration,
                    request.method,
                    request.url.path,
                )
        except asyncio.TimeoutError:
            logger.error(
                "Concurrency limit reached (max=%d). Rejecting %s %s after %.3fs wait.",
                self.max_concurrent,
                request.method,
                request.url.path,
                time.perf_counter() - start_wait,
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Server is busy handling other requests. Please retry shortly.",
                    "max_concurrent": self.max_concurrent,
                    "timeout_seconds": self.acquire_timeout,
                },
            )

        try:
            response = await call_next(request)
            return response
        finally:
            self._semaphore.release()
            # Safe diagnostics headers
            try:
                in_flight = self.max_concurrent - self._semaphore._value
                if response and hasattr(response, "headers"):
                    response.headers["X-Concurrency-Limit"] = str(self.max_concurrent)
                    response.headers["X-Concurrency-In-Flight"] = str(in_flight)
            except Exception:  # pragma: no cover
                pass

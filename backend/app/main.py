"""FastAPI application entrypoint.

Responsibilities kept deliberately narrow: wire middleware, routers, and
startup/shutdown lifecycle. All business logic lives in app.services /
app.workers so this file stays a thin composition root.
"""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.routes import download, health, playlist
from app.config.settings import get_settings
from app.db.session import SessionLocal, init_db
from app.services.cleanup_service import (
    cleanup_abandoned_pending_jobs,
    cleanup_expired_jobs,
    cleanup_orphaned_storage,
    cleanup_stale_processing_jobs,
    reset_orphaned_active_jobs_on_startup,
)
from app.services.storage import get_storage_backend
from app.utils.errors import AppError
from app.utils.logging import configure_logging, get_logger, log_event
from app.utils.rate_limit import limiter
from app.workers.conversion_worker import process_job_with_timeout
from app.workers.queue import get_job_queue

configure_logging()
logger = get_logger("app")

MAX_REQUEST_BODY_BYTES = 64 * 1024  # API only accepts small JSON payloads
CLEANUP_INTERVAL_SECONDS = 900


class MaxBodySizeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_REQUEST_BODY_BYTES:
            return JSONResponse(
                status_code=413,
                content={"success": False, "error": {"code": "payload_too_large", "message": "Request body too large."}},
            )
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        settings = get_settings()
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        return response


async def _cleanup_loop() -> None:
    settings = get_settings()
    storage = get_storage_backend()
    while True:
        await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
        db = SessionLocal()
        try:
            expired = cleanup_expired_jobs(db, storage)
            timed_out = cleanup_stale_processing_jobs(db, settings)
            abandoned = cleanup_abandoned_pending_jobs(db, storage)
            orphaned = cleanup_orphaned_storage(db, storage)
            if expired or timed_out or abandoned or orphaned:
                log_event(
                    logger, 20, "cleanup_cycle",
                    expired=expired, timed_out=timed_out, abandoned=abandoned, orphaned=orphaned,
                )
        except Exception:
            logger.exception("Cleanup cycle failed")
        finally:
            db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()

    settings = get_settings()
    db = SessionLocal()
    try:
        orphaned = reset_orphaned_active_jobs_on_startup(db, settings)
        if orphaned:
            log_event(logger, 30, "orphaned_jobs_reset_on_startup", count=orphaned)
    finally:
        db.close()

    queue = get_job_queue()
    queue.start(process_job_with_timeout)
    cleanup_task = asyncio.create_task(_cleanup_loop())
    logger.info("Application startup complete")
    yield
    cleanup_task.cancel()
    await queue.stop()
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="YouTube Playlist Audio Downloader API",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/api/docs" if not settings.is_production else None,
        redoc_url=None,
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Content-Type"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(MaxBodySizeMiddleware)

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "error": {"code": exc.error_code, "message": exc.message}},
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {"code": "internal_error", "message": "An unexpected error occurred. Please try again."},
            },
        )

    app.include_router(health.router)
    app.include_router(playlist.router)
    app.include_router(download.router)

    return app


app = create_app()

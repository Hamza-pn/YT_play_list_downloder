"""Application-level exceptions.

Every error the API can return to a client is modeled here so the exception
handlers in app.main can map them to a consistent JSON shape without ever
leaking a stack trace or internal detail to the client.
"""
from __future__ import annotations


class AppError(Exception):
    """Base class for all handled application errors."""

    status_code: int = 400
    error_code: str = "app_error"

    def __init__(self, message: str, *, error_code: str | None = None, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        if error_code:
            self.error_code = error_code
        if status_code:
            self.status_code = status_code


class InvalidURLError(AppError):
    status_code = 422
    error_code = "invalid_url"


class UnsupportedContentError(AppError):
    status_code = 422
    error_code = "unsupported_content"


class PlaylistNotFoundError(AppError):
    status_code = 404
    error_code = "playlist_not_found"


class PlaylistEmptyError(AppError):
    status_code = 422
    error_code = "playlist_empty"


class ContentUnavailableError(AppError):
    status_code = 422
    error_code = "content_unavailable"


class PermissionDeniedError(AppError):
    status_code = 403
    error_code = "permission_denied"


class PlaylistTooLargeError(AppError):
    status_code = 422
    error_code = "playlist_too_large"


class JobNotFoundError(AppError):
    status_code = 404
    error_code = "job_not_found"


class JobLimitExceededError(AppError):
    status_code = 429
    error_code = "job_limit_exceeded"


class JobStillProcessingError(AppError):
    status_code = 409
    error_code = "job_still_processing"


class DailyLimitExceededError(AppError):
    status_code = 429
    error_code = "daily_limit_exceeded"


class ConversionFailedError(AppError):
    status_code = 502
    error_code = "conversion_failed"


class FileTooLargeError(AppError):
    status_code = 422
    error_code = "file_too_large"


class StorageError(AppError):
    status_code = 500
    error_code = "storage_error"


class TimeoutErrorApp(AppError):
    status_code = 504
    error_code = "timeout"


class RateLimitedError(AppError):
    status_code = 429
    error_code = "rate_limited"

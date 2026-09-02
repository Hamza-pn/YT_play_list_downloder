from app.services.storage.base import StorageBackend
from app.services.storage.local_storage import LocalStorage

__all__ = ["StorageBackend", "LocalStorage", "get_storage_backend"]


def get_storage_backend() -> StorageBackend:
    """Factory — swap this to return an S3Storage implementation in Phase 4
    without changing any calling code."""
    from app.config.settings import get_settings

    settings = get_settings()
    if settings.storage_backend == "s3":
        raise NotImplementedError(
            "S3 storage backend is planned for Phase 4. Set STORAGE_BACKEND=local for now."
        )
    return LocalStorage()

"""Central application configuration, loaded from environment variables.

Never hard-code secrets here — everything comes from the process environment
(populated from `.env` in development via pydantic-settings' dotenv support).
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/config/settings.py -> backend/. Anchoring here (rather than
# leaving .env/storage/sqlite paths relative to the process's CWD) means
# the app behaves identically whether launched as `uvicorn app.main:app`
# from backend/, via `--app-dir`, from Docker, or from a task runner that
# starts it from the repo root.
BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App ---
    environment: str = "development"
    secret_key: str = "dev-only-insecure-key-change-me"
    admin_email: str = "admin@example.com"
    admin_password: str = "change-me"
    backend_cors_origins: str = "http://localhost:3000"

    # --- Database ---
    database_url: str = "sqlite+pysqlite:///./storage/app.db"

    # --- Cache / Queue ---
    redis_url: str = "redis://localhost:6379/0"
    use_celery: bool = False

    # --- Storage ---
    storage_backend: str = "local"
    storage_local_path: str = "./storage"
    storage_bucket: str = ""
    storage_endpoint: str = ""
    storage_access_key: str = ""
    storage_secret_key: str = ""
    storage_region: str = "us-east-1"

    # --- Binaries ---
    ffmpeg_path: str = ""
    ffprobe_path: str = ""

    # --- Limits ---
    max_playlist_videos: int = 100
    max_file_size_mb: int = 500
    max_concurrent_jobs: int = 3
    max_concurrent_jobs_per_session: int = 1
    job_timeout_seconds: int = 3600
    file_retention_hours: int = 6
    max_requests_per_minute: int = 10
    max_daily_conversions_guest: int = 10
    max_quality_kbps_guest: int = 192

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.backend_cors_origins.split(",") if o.strip()]

    @property
    def storage_root(self) -> Path:
        path = Path(self.storage_local_path)
        if not path.is_absolute():
            path = BACKEND_ROOT / path
        path = path.resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def resolved_database_url(self) -> str:
        """database_url with a relative sqlite file path rebased onto
        BACKEND_ROOT instead of the process's CWD. Non-sqlite URLs (e.g.
        Postgres in Phase 2) pass through unchanged."""
        prefix = "sqlite+pysqlite:///"
        if not self.database_url.startswith(prefix):
            return self.database_url
        raw_path = self.database_url[len(prefix):]
        if raw_path.startswith("/") or (len(raw_path) > 1 and raw_path[1] == ":"):
            return self.database_url  # already absolute (posix or Windows drive letter)
        absolute = (BACKEND_ROOT / raw_path).resolve()
        return f"{prefix}{absolute.as_posix()}"

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()

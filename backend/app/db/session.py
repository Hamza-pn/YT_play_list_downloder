"""Database engine/session setup.

SQLite is used in Phase 1 for zero-dependency local development. Swapping to
Postgres in Phase 2 is a one-line change to DATABASE_URL — no code here is
SQLite-specific except the `check_same_thread` connect arg.
"""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config.settings import get_settings

settings = get_settings()
_database_url = settings.resolved_database_url

_connect_args = {}
if _database_url.startswith("sqlite"):
    _connect_args["check_same_thread"] = False

engine = create_engine(
    _database_url,
    connect_args=_connect_args,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create tables if they don't exist. Phase 1 only — Phase 2 uses Alembic."""
    from app.models import base  # noqa: F401  (ensures metadata is populated)

    base.Base.metadata.create_all(bind=engine)

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_uuid() -> str:
    return str(uuid.uuid4())


def ensure_aware(dt: datetime | None) -> datetime | None:
    """SQLite (unlike Postgres) drops tzinfo on round-trip even for
    DateTime(timezone=True) columns, so a value freshly loaded/refreshed
    from the DB comes back naive even though we always write UTC. Every
    call site that subtracts a DB-loaded datetime from an aware `now()`
    must normalize through this first."""
    if dt is None or dt.tzinfo is not None:
        return dt
    return dt.replace(tzinfo=timezone.utc)


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

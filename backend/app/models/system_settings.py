from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class SystemSettings(Base, TimestampMixin):
    """Admin-editable key/value overrides for the limits in Settings.

    Read at request time by app.services.limits_service, falling back to the
    .env-derived defaults when a key has no row here.
    """

    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value: Mapped[str] = mapped_column(String(1024), nullable=False)
    description: Mapped[str] = mapped_column(String(512), default="", nullable=False)

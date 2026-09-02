from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid


class PlanType(str, enum.Enum):
    FREE = "free"
    PREMIUM = "premium"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    NONE = "none"


class Subscription(Base, TimestampMixin):
    """Placeholder model so premium/payment integration (Phase 3) needs no
    schema migration beyond adding provider-specific columns."""

    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), unique=True, nullable=False)

    plan: Mapped[PlanType] = mapped_column(Enum(PlanType), default=PlanType.FREE, nullable=False)
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus), default=SubscriptionStatus.NONE, nullable=False
    )
    current_period_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Populated once a payment provider (e.g. Stripe) is wired up in Phase 3.
    provider_customer_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    provider_subscription_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    user: Mapped["User"] = relationship(back_populates="subscription")

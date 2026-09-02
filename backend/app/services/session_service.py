"""Anonymous guest session management.

Each browser gets an opaque, signed session id in an httponly cookie. No
registration, no PII. This id is the sole key used to enforce per-guest
limits (concurrent jobs, daily conversions, max quality).
"""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Request, Response
from itsdangerous import BadSignature, URLSafeTimedSerializer
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.models.base import ensure_aware
from app.models.job import Job, JobStatus
from app.models.user import User
from app.utils.errors import DailyLimitExceededError, JobLimitExceededError

SESSION_COOKIE_NAME = "ytad_session"
_SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 365

_ACTIVE_STATUSES = (JobStatus.PENDING, JobStatus.ANALYZING, JobStatus.PROCESSING)


def _serializer() -> URLSafeTimedSerializer:
    settings = get_settings()
    return URLSafeTimedSerializer(settings.secret_key, salt="guest-session")


def get_or_create_user(db: Session, request: Request, response: Response) -> User:
    settings = get_settings()
    token = request.cookies.get(SESSION_COOKIE_NAME)
    session_id: str | None = None

    if token:
        try:
            session_id = _serializer().loads(token, max_age=_SESSION_MAX_AGE_SECONDS)
        except BadSignature:
            session_id = None

    user: User | None = None
    if session_id:
        user = db.query(User).filter(User.session_id == session_id).one_or_none()

    if user is None:
        session_id = secrets.token_urlsafe(32)
        user = User(session_id=session_id, is_guest=True)
        db.add(user)
        db.commit()
        db.refresh(user)

    signed = _serializer().dumps(session_id)
    response.set_cookie(
        SESSION_COOKIE_NAME,
        signed,
        max_age=_SESSION_MAX_AGE_SECONDS,
        httponly=True,
        samesite="lax",
        secure=settings.is_production,
        path="/",
    )
    return user


def enforce_daily_limit(db: Session, user: User) -> None:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    if now - ensure_aware(user.daily_conversions_reset_at) > timedelta(hours=24):
        user.daily_conversions_count = 0
        user.daily_conversions_reset_at = now
        db.commit()

    limit = settings.max_daily_conversions_guest
    if not user.is_admin and user.daily_conversions_count >= limit:
        raise DailyLimitExceededError(
            f"You've reached the daily limit of {limit} conversions for guest users. Try again later."
        )


def increment_daily_count(db: Session, user: User) -> None:
    user.daily_conversions_count += 1
    db.commit()


def enforce_concurrent_job_limit(db: Session, user: User) -> None:
    settings = get_settings()
    active = (
        db.query(Job)
        .filter(Job.user_id == user.id, Job.status.in_(_ACTIVE_STATUSES))
        .count()
    )
    if not user.is_admin and active >= settings.max_concurrent_jobs_per_session:
        raise JobLimitExceededError(
            "You already have a conversion in progress. Wait for it to finish before starting another."
        )


def clamp_quality_for_user(user: User, quality_kbps: int | None) -> int | None:
    settings = get_settings()
    if quality_kbps is None or user.is_admin:
        return quality_kbps
    return min(quality_kbps, settings.max_quality_kbps_guest)

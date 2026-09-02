"""In-memory sliding-window rate limiter for Phase 1 (single-process).

Phase 2 swaps the backing store for Redis (slowapi supports this natively
via a `storage_uri=redis://...` change) without touching call sites.

Two tiers, deliberately:
  - `default_limits` is a generous global safety net applied to every
    request, mainly to blunt naive flooding.
  - MAX_REQUESTS_PER_MINUTE (the operator-configurable, abuse-prevention
    limit from .env) is applied via an explicit @limiter.limit(...)
    decorator ONLY on the expensive, state-changing endpoints
    (playlist analyze, job create) — see app/api/routes/*.py.

Applying the strict configured limit globally (the Phase 1 first draft)
was a real bug: it counted routine status polling and long-lived SSE
progress connections against the same budget as "start a conversion",
so a user watching one job's progress could exhaust the budget and then
get a spurious 429 on their next conversion request.
"""
from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

DEFAULT_GLOBAL_LIMIT = "300/minute"

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[DEFAULT_GLOBAL_LIMIT],
)


def action_rate_limit() -> str:
    """Limit string for expensive, abuse-relevant actions (playlist
    analyze, job create), read fresh from Settings at call time so it
    reflects the currently configured MAX_REQUESTS_PER_MINUTE."""
    from app.config.settings import get_settings

    return f"{get_settings().max_requests_per_minute}/minute"

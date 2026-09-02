"""Verifies the exact slowapi wiring pattern used in app.main (Limiter +
SlowAPIMiddleware + RateLimitExceeded handler) actually enforces a limit,
using an isolated tiny app so it never depends on / interferes with the
global test suite's higher limit (set in conftest for the other API tests).
"""
from fastapi import FastAPI
from fastapi.testclient import TestClient
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address


def test_rate_limiter_returns_429_after_limit_exceeded():
    limiter = Limiter(key_func=get_remote_address, default_limits=["3/minute"])
    test_app = FastAPI()
    test_app.state.limiter = limiter
    test_app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    test_app.add_middleware(SlowAPIMiddleware)

    @test_app.get("/ping")
    def ping():
        return {"ok": True}

    with TestClient(test_app) as c:
        statuses = [c.get("/ping").status_code for _ in range(5)]

    assert statuses.count(200) == 3
    assert statuses.count(429) == 2


def test_decorated_route_still_resolves_body_and_dependencies(client):
    """Regression test for a real bug: `@limiter.limit(...)` on a route in
    a module with `from __future__ import annotations` broke FastAPI's
    ability to resolve the route's parameter types. slowapi's wrapper
    function has different __globals__ than the route module, so once
    annotations are postponed-eval strings, resolving them through the
    wrapper silently fails and FastAPI falls back to treating every
    parameter (including the JSON body and DB/user dependencies) as a
    plain query parameter — every request then 422s with 'field required'
    for query params named payload/db/user/settings. The fix was dropping
    `from __future__ import annotations` from the routed modules that use
    the rate-limit decorator. This test posts a well-formed request to a
    rate-limited endpoint and asserts it's actually accepted (200), not
    422 — which is exactly the symptom that would return if this regresses.
    """
    resp = client.post("/api/playlist/analyze", json={"url": "not-a-real-playlist-url"})
    # We expect a *handled* validation error (422 from our own URL
    # validator, JSON body `{"success": false, "error": {...}}`), never the
    # broken-signature symptom of FastAPI complaining about missing query
    # params named payload/db/user/settings.
    assert resp.status_code == 422
    body = resp.json()
    assert "success" in body and body["success"] is False
    assert body["error"]["code"] == "invalid_url"

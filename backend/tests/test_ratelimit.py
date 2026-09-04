"""Rate-limiter unit tests (no network / no API key) — exercise the factory
directly so they don't depend on any endpoint's configured limit."""
import pytest
from fastapi import HTTPException

import app as appmod


class _Req:
    def __init__(self, ip="203.0.113.7"):
        self.headers = {"x-forwarded-for": ip}
        self.client = type("C", (), {"host": ip})()


def test_rate_limiter_blocks_after_limit():
    dep = appmod.rate_limiter("unit_bucket", 3, window=60)
    req = _Req("198.51.100.1")
    dep(req); dep(req); dep(req)          # 3 allowed
    with pytest.raises(HTTPException) as ei:
        dep(req)                           # 4th → 429
    assert ei.value.status_code == 429


def test_rate_limiter_is_per_ip():
    dep = appmod.rate_limiter("unit_bucket2", 1, window=60)
    dep(_Req("198.51.100.2"))             # first IP ok
    dep(_Req("198.51.100.3"))             # different IP ok (separate bucket)
    with pytest.raises(HTTPException):
        dep(_Req("198.51.100.2"))         # first IP again → blocked


def test_client_ip_prefers_xff():
    class R:
        headers = {"x-forwarded-for": "203.0.113.9, 10.0.0.1"}
        client = type("C", (), {"host": "10.0.0.1"})()
    assert appmod._client_ip(R()) == "203.0.113.9"

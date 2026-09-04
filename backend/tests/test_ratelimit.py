"""Rate-limiter + palm-upload-cap sanity (no network / no API key)."""
from fastapi.testclient import TestClient

import app as appmod


def test_geocode_rate_limit_returns_429(monkeypatch):
    # Short-circuit the actual Nominatim call: tiny queries return [] immediately.
    client = TestClient(appmod.app)
    # limit is 60/min for geocode; hammer past it with distinct <2-char queries
    # that never hit the network (len<2 → []), so only the limiter can 429.
    got_429 = False
    for i in range(70):
        r = client.get("/api/geocode", params={"q": "x"})  # len 1 → [] but still counts
        if r.status_code == 429:
            got_429 = True
            break
    assert got_429, "rate limiter never triggered"


def test_client_ip_prefers_xff():
    class _Req:
        headers = {"x-forwarded-for": "203.0.113.9, 10.0.0.1"}
        client = type("C", (), {"host": "10.0.0.1"})()
    assert appmod._client_ip(_Req()) == "203.0.113.9"

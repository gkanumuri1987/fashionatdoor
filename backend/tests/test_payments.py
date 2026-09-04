"""Payment-rail unit tests (signature math + plan table; no live gateways)."""

import hashlib
import hmac
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import payments


def test_plan_table_complete():
    assert set(payments.PLANS) == {"monthly_basic", "monthly_plus",
                                   "lifetime", "lifetime_plus"}
    for p in payments.PLANS.values():
        assert p["usd"] > 0 and p["inr"] > 0
        assert p["period"] in ("monthly", "lifetime")
    assert payments.PLANS["lifetime_plus"]["usd"] == 19.99
    assert payments.PLANS["monthly_basic"]["inr"] == 179


def test_config_dormant_without_keys(monkeypatch):
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    monkeypatch.delenv("RAZORPAY_KEY_ID", raising=False)
    c = payments.config()
    assert c["stripe"] is False and c["razorpay"]["enabled"] is False
    assert "plans" in c


def test_stripe_webhook_signature(monkeypatch):
    import time as _t
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test")
    payload = b'{"type":"ping"}'
    t = str(int(_t.time()))  # fresh timestamp (within the 5-min replay window)
    good = hmac.new(b"whsec_test", f"{t}.".encode() + payload,
                    hashlib.sha256).hexdigest()
    assert payments.stripe_webhook(payload, f"t={t},v1={good}") == {"received": True}
    # A bad signature is rejected.
    assert "error" in payments.stripe_webhook(payload, f"t={t},v1=deadbeef")
    # Multiple v1 candidates (Stripe rotates secrets) — one valid is enough.
    assert payments.stripe_webhook(payload, f"t={t},v1=deadbeef,v1={good}") == {"received": True}
    # Replay protection: a stale timestamp is refused even with a valid signature.
    stale = "1700000000"  # Nov 2023
    stale_sig = hmac.new(b"whsec_test", f"{stale}.".encode() + payload,
                         hashlib.sha256).hexdigest()
    assert "error" in payments.stripe_webhook(payload, f"t={stale},v1={stale_sig}")


def test_razorpay_signature(monkeypatch):
    monkeypatch.setenv("RAZORPAY_KEY_SECRET", "rzp_secret")
    monkeypatch.setenv("RAZORPAY_KEY_ID", "rzp_id")
    sig = hmac.new(b"rzp_secret", b"order_1|pay_1", hashlib.sha256).hexdigest()
    # Bad signature short-circuits before any order lookup.
    assert "error" in payments.razorpay_verify("order_1", "pay_1", "bad", "u", "lifetime")
    # Good signature proceeds to the order cross-check (fails offline — but the
    # error is the lookup, not the signature).
    r = payments.razorpay_verify("order_1", "pay_1", sig, "u", "lifetime")
    assert r.get("error") in ("order lookup failed", "order does not match this user/plan")

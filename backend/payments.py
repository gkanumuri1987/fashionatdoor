"""Payments — Stripe (cards, international) + Razorpay (UPI/cards, India).

Both gateways are implemented over their raw REST APIs (no SDK deps) and are
DORMANT until their env keys exist — /api/pay/config tells the frontend which
rails are live. Activation is strictly server-side:

  Stripe:   Checkout Session (USD) → webhook `checkout.session.completed`
            (signature-verified) → _activate_plan()
  Razorpay: Order (INR) → client-side Checkout → /verify with the payment
            signature (HMAC-verified) → _activate_plan()

_activate_plan writes user_flags via the Supabase SERVICE ROLE key — the only
writer of premium state, matching the RLS design (clients cannot self-flag).

Env (Railway):
  STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET
  RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET
  SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import time

import httpx

logger = logging.getLogger("payments")

# plan → pricing + entitlement period. INR prices are the Razorpay rail.
PLANS: dict[str, dict] = {
    "monthly_basic": {"usd": 1.99, "inr": 179, "period": "monthly",
                      "label": "Jyotish AI — Basic (monthly)"},
    "monthly_plus": {"usd": 2.99, "inr": 269, "period": "monthly",
                     "label": "Jyotish AI — Plus (monthly)"},
    "lifetime": {"usd": 9.99, "inr": 899, "period": "lifetime",
                 "label": "Jyotish AI — Lifetime"},
    "lifetime_plus": {"usd": 19.99, "inr": 1799, "period": "lifetime",
                      "label": "Jyotish AI — Lifetime Plus"},
}


def _env(name: str) -> str:
    return os.environ.get(name, "").strip()


def config() -> dict:
    """Which rails are live (frontend adapts its buttons)."""
    return {
        "stripe": bool(_env("STRIPE_SECRET_KEY")),
        "razorpay": {"enabled": bool(_env("RAZORPAY_KEY_ID") and _env("RAZORPAY_KEY_SECRET")),
                     "key_id": _env("RAZORPAY_KEY_ID") or None},
        "plans": {k: {"usd": v["usd"], "inr": v["inr"], "period": v["period"]}
                  for k, v in PLANS.items()},
    }


# ── Supabase activation (service role — the single writer of premium) ───────

def _activate_plan(user_id: str, plan: str, gateway: str, payment_ref: str) -> bool:
    url = _env("SUPABASE_URL")
    key = _env("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        logger.error("activation skipped: SUPABASE_URL/SERVICE_ROLE_KEY missing "
                     "(user=%s plan=%s ref=%s)", user_id, plan, payment_ref)
        return False
    period = PLANS.get(plan, {}).get("period", "monthly")
    expires = None
    if period == "monthly":
        expires = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + 32 * 86400))
    headers = {"apikey": key, "Authorization": f"Bearer {key}",
               "Content-Type": "application/json",
               # return=representation so we can VERIFY a row was actually
               # written (a silent 0-row upsert would otherwise log success).
               "Prefer": "resolution=merge-duplicates,return=representation"}
    try:
        r = httpx.post(f"{url}/rest/v1/user_flags?on_conflict=user_id", headers=headers,
                       json={"user_id": user_id, "is_premium": True, "plan": plan,
                             "plan_started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                             "plan_expires_at": expires,
                             "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
                       timeout=15.0)
        ok = r.status_code in (200, 201, 204)
        if not ok:
            logger.error("activation write failed %s: %s", r.status_code, r.text[:300])
        elif r.status_code != 204:
            # Confirm the upsert affected a row (guards the "RLS silently blocks
            # writes / no-op upsert" trap — success status but nothing persisted).
            try:
                body = r.json()
                if isinstance(body, list) and not body:
                    logger.error("activation wrote 0 rows (no-op) user=%s plan=%s", user_id, plan)
                    ok = False
            except Exception:
                pass
        # Mark the latest matching request active (best-effort).
        httpx.patch(f"{url}/rest/v1/subscription_requests"
                    f"?user_id=eq.{user_id}&plan=eq.{plan}&status=eq.pending",
                    headers=headers, json={"status": "active"}, timeout=15.0)
        logger.info("plan ACTIVATED user=%s plan=%s via %s ref=%s", user_id, plan,
                    gateway, payment_ref)
        return ok
    except Exception as exc:
        logger.error("activation error: %s", exc)
        return False


# ── Stripe ──────────────────────────────────────────────────────────────────

def stripe_checkout(plan: str, user_id: str, email: str, origin: str) -> dict:
    sk = _env("STRIPE_SECRET_KEY")
    if not sk:
        return {"error": "Stripe is not configured"}
    p = PLANS[plan]
    data = {
        "mode": "payment",
        "success_url": f"{origin}/subscription?paid=1",
        "cancel_url": f"{origin}/subscription?cancelled=1",
        "customer_email": email or None,
        "metadata[user_id]": user_id,
        "metadata[plan]": plan,
        "line_items[0][quantity]": "1",
        "line_items[0][price_data][currency]": "usd",
        "line_items[0][price_data][unit_amount]": str(int(round(p["usd"] * 100))),
        "line_items[0][price_data][product_data][name]": p["label"],
    }
    data = {k: v for k, v in data.items() if v is not None}
    r = httpx.post("https://api.stripe.com/v1/checkout/sessions",
                   auth=(sk, ""), data=data, timeout=20.0)
    if r.status_code != 200:
        logger.error("stripe checkout failed %s: %s", r.status_code, r.text[:300])
        return {"error": "Could not start Stripe checkout"}
    return {"url": r.json()["url"]}


def stripe_webhook(payload: bytes, sig_header: str) -> dict:
    """Verify Stripe-Signature (t=...,v1=...) and activate on completion."""
    secret = _env("STRIPE_WEBHOOK_SECRET")
    if not secret:
        return {"error": "webhook secret not configured"}
    try:
        items = [kv.split("=", 1) for kv in (sig_header or "").split(",") if "=" in kv]
        t = next((v for k, v in items if k == "t"), None)
        v1s = [v for k, v in items if k == "v1"]  # may be several; check them all
        if not t or not v1s:
            return {"error": "bad signature header"}
        # Replay protection: reject events whose timestamp is outside a 5-minute
        # window (a captured valid webhook must not be replayable indefinitely).
        if abs(time.time() - int(t)) > 300:
            return {"error": "timestamp outside tolerance"}
        signed = f"{t}.".encode() + payload
        expected = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
        if not any(hmac.compare_digest(expected, v1) for v1 in v1s):
            return {"error": "bad signature"}
    except Exception:
        return {"error": "bad signature header"}
    import json as _json
    event = _json.loads(payload)
    if event.get("type") == "checkout.session.completed":
        s = event["data"]["object"]
        meta = s.get("metadata") or {}
        if s.get("payment_status") == "paid" and meta.get("user_id") and meta.get("plan"):
            _activate_plan(meta["user_id"], meta["plan"], "stripe", s.get("id", ""))
    return {"received": True}


# ── Razorpay ────────────────────────────────────────────────────────────────

def razorpay_order(plan: str, user_id: str) -> dict:
    kid, ks = _env("RAZORPAY_KEY_ID"), _env("RAZORPAY_KEY_SECRET")
    if not (kid and ks):
        return {"error": "Razorpay is not configured"}
    p = PLANS[plan]
    r = httpx.post("https://api.razorpay.com/v1/orders", auth=(kid, ks),
                   json={"amount": int(p["inr"] * 100), "currency": "INR",
                         "notes": {"user_id": user_id, "plan": plan}},
                   timeout=20.0)
    if r.status_code != 200:
        logger.error("razorpay order failed %s: %s", r.status_code, r.text[:300])
        return {"error": "Could not create Razorpay order"}
    o = r.json()
    return {"order_id": o["id"], "amount": o["amount"], "currency": o["currency"],
            "key_id": kid, "label": p["label"]}


def razorpay_verify(order_id: str, payment_id: str, signature: str,
                    user_id: str, plan: str) -> dict:
    ks = _env("RAZORPAY_KEY_SECRET")
    if not ks:
        return {"error": "Razorpay is not configured"}
    expected = hmac.new(ks.encode(), f"{order_id}|{payment_id}".encode(),
                        hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        return {"error": "signature verification failed"}
    # Cross-check the order's notes so a verified payment can only activate
    # the user/plan it was created for.
    kid = _env("RAZORPAY_KEY_ID")
    try:
        r = httpx.get(f"https://api.razorpay.com/v1/orders/{order_id}",
                      auth=(kid, ks), timeout=15.0)
        notes = (r.json().get("notes") or {}) if r.status_code == 200 else {}
        if notes.get("user_id") != user_id or notes.get("plan") != plan:
            return {"error": "order does not match this user/plan"}
    except Exception:
        return {"error": "order lookup failed"}
    ok = _activate_plan(user_id, plan, "razorpay", payment_id)
    return {"activated": ok}

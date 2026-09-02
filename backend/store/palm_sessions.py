"""Palm session store — tokenized links, 48h expiry, biometric-safe retention.

File-backed (one JSON per token under backend/output/palm_sessions/), thread-safe,
never raises on read. RETENTION RULE: palm images are biometric-adjacent personal
data — the image bytes are NEVER written to disk; only the derived feature JSON
and reading are stored. Expired sessions are swept on every create.
"""

from __future__ import annotations

import json
import re
import secrets
import threading
import time as _time
from pathlib import Path

_LOCK = threading.RLock()
_DIR = Path(__file__).resolve().parent.parent / "output" / "palm_sessions"
TTL_SECONDS = 48 * 3600
_TOKEN_RE = re.compile(r"^[a-f0-9]{32}$")


def _path(token: str) -> Path:
    return _DIR / f"{token}.json"


def create_session(now: float | None = None) -> dict:
    now = now if now is not None else _time.time()
    sweep_expired(now)
    token = secrets.token_hex(16)
    session = {"token": token, "status": "awaiting_photo",
               "created_at": now, "expires_at": now + TTL_SECONDS, "result": None}
    with _LOCK:
        _DIR.mkdir(parents=True, exist_ok=True)
        with open(_path(token), "w") as f:
            json.dump(session, f)
    return session


def get_session(token: str, now: float | None = None) -> dict | None:
    if not _TOKEN_RE.match(token or ""):
        return None
    now = now if now is not None else _time.time()
    with _LOCK:
        try:
            with open(_path(token)) as f:
                s = json.load(f)
        except (OSError, json.JSONDecodeError):
            return None
    if s.get("expires_at", 0) < now:
        return None
    return s


def save_result(token: str, result: dict, now: float | None = None) -> dict | None:
    s = get_session(token, now)
    if s is None:
        return None
    s["status"] = "complete" if result.get("usable") else "retake_needed"
    s["result"] = result
    with _LOCK:
        with open(_path(token), "w") as f:
            json.dump(s, f, ensure_ascii=False)
    return s


def sweep_expired(now: float | None = None) -> int:
    """Delete expired session files. Best-effort, returns count removed."""
    now = now if now is not None else _time.time()
    removed = 0
    with _LOCK:
        if not _DIR.is_dir():
            return 0
        for p in _DIR.glob("*.json"):
            try:
                with open(p) as f:
                    s = json.load(f)
                if s.get("expires_at", 0) < now:
                    p.unlink()
                    removed += 1
            except (OSError, json.JSONDecodeError):
                try:
                    p.unlink()
                    removed += 1
                except OSError:
                    pass
    return removed

"""Central AI dispatch — NEVER raises; always returns a dict.

Pattern ported from the proven Taabel `_call_ai`: on any failure the caller
gets ``{"_error": True, "_error_message": "..."}`` instead of an exception, so
route handlers always return valid JSON.

Resilience: Google's Gemini service intermittently returns transient errors
(503 UNAVAILABLE / 429 RESOURCE_EXHAUSTED / 500). Every call retries with
backoff and then falls through a model chain before giving up, and the final
failure message is human-friendly — raw Google error JSON never reaches users.
"""

from __future__ import annotations

import logging
import os
import time

logger = logging.getLogger("ai.client")

DEFAULT_TEXT_MODEL = os.environ.get("GEMINI_TEXT_MODEL", "gemini-2.5-flash")
FALLBACK_TEXT_MODEL = os.environ.get("GEMINI_FALLBACK_MODEL", "gemini-2.0-flash")

_TRANSIENT_MARKERS = ("503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED",
                      "500", "INTERNAL", "DEADLINE", "overloaded")
_MAX_ATTEMPTS_PER_MODEL = 3
_BACKOFF_BASE_SEC = 2.0

_BUSY_MESSAGE = ("The AI service is briefly busy. Please try again in a few "
                 "seconds — your chart is computed and unaffected.")


def _is_transient(exc: Exception) -> bool:
    s = str(exc)
    return any(m in s for m in _TRANSIENT_MARKERS)


def _model_chain() -> list[str]:
    chain = [DEFAULT_TEXT_MODEL]
    if FALLBACK_TEXT_MODEL and FALLBACK_TEXT_MODEL != DEFAULT_TEXT_MODEL:
        chain.append(FALLBACK_TEXT_MODEL)
    return chain


def _generate(contents, system: str, temperature: float, max_tokens: int) -> dict:
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        return {"_error": True,
                "_error_message": "GEMINI_API_KEY is not configured on the server."}
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return {"_error": True, "_error_message": "google-genai SDK not installed."}

    client = genai.Client(api_key=api_key)
    last_exc: Exception | None = None
    for model in _model_chain():
        for attempt in range(_MAX_ATTEMPTS_PER_MODEL):
            try:
                resp = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system,
                        temperature=temperature,
                        max_output_tokens=max_tokens,
                    ),
                )
                text = (resp.text or "").strip()
                if not text:
                    raise RuntimeError("Model returned empty text.")
                if model != DEFAULT_TEXT_MODEL or attempt > 0:
                    logger.info("AI call succeeded on %s (attempt %d)", model, attempt + 1)
                return {"text": text}
            except Exception as exc:  # noqa: BLE001 — never-raises contract
                last_exc = exc
                if not _is_transient(exc):
                    # Auth/config/prompt errors won't heal with retries; a
                    # different model may still work (e.g. model-specific 404).
                    logger.error("AI call non-transient on %s: %s", model, exc)
                    break
                wait = _BACKOFF_BASE_SEC * (2 ** attempt)
                logger.warning("AI transient error on %s (attempt %d/%d), retrying in %.0fs: %s",
                               model, attempt + 1, _MAX_ATTEMPTS_PER_MODEL, wait, exc)
                if attempt < _MAX_ATTEMPTS_PER_MODEL - 1:
                    time.sleep(wait)

    logger.error("AI call exhausted all models/retries: %s", last_exc)
    if last_exc is not None and _is_transient(last_exc):
        return {"_error": True, "_error_message": _BUSY_MESSAGE}
    return {"_error": True,
            "_error_message": "The AI service could not complete this request. "
                              "Please try again; if it persists, contact support."}


def call_ai(system: str, prompt: str, temperature: float = 0.6,
            max_tokens: int = 8192) -> dict:
    """Returns {"text": str} or {"_error": True, "_error_message": str}."""
    return _generate(prompt, system, temperature, max_tokens)


def call_ai_vision(system: str, prompt: str, images: list[bytes],
                   mime_type: str = "image/jpeg", temperature: float = 0.3,
                   max_tokens: int = 8192) -> dict:
    """Vision call (palmistry). Same never-raises + retry contract."""
    try:
        from google.genai import types
    except ImportError:
        return {"_error": True, "_error_message": "google-genai SDK not installed."}
    parts: list = [types.Part.from_bytes(data=b, mime_type=mime_type) for b in images]
    parts.append(prompt)
    return _generate(parts, system, temperature, max_tokens)

"""Central AI dispatch — NEVER raises; always returns a dict.

Pattern ported from the proven Taabel `_call_ai`: on any failure the caller
gets ``{"_error": True, "_error_message": "..."}`` instead of an exception, so
route handlers always return valid JSON.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger("ai.client")

DEFAULT_TEXT_MODEL = os.environ.get("GEMINI_TEXT_MODEL", "gemini-2.5-flash")


def call_ai(system: str, prompt: str, temperature: float = 0.6,
            max_tokens: int = 8192) -> dict:
    """Returns {"text": str} or {"_error": True, "_error_message": str}."""
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        return {"_error": True,
                "_error_message": "GEMINI_API_KEY is not configured on the server."}
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return {"_error": True, "_error_message": "google-genai SDK not installed."}

    try:
        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(
            model=DEFAULT_TEXT_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system,
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )
        text = (resp.text or "").strip()
        if not text:
            return {"_error": True, "_error_message": "Model returned empty text."}
        return {"text": text}
    except Exception as exc:
        logger.error("AI call failed: %s", exc)
        return {"_error": True, "_error_message": str(exc)}


def call_ai_vision(system: str, prompt: str, images: list[bytes],
                   mime_type: str = "image/jpeg", temperature: float = 0.3,
                   max_tokens: int = 8192) -> dict:
    """Vision call (palmistry). Same never-raises contract."""
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        return {"_error": True,
                "_error_message": "GEMINI_API_KEY is not configured on the server."}
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return {"_error": True, "_error_message": "google-genai SDK not installed."}
    try:
        client = genai.Client(api_key=api_key)
        parts: list = [types.Part.from_bytes(data=b, mime_type=mime_type) for b in images]
        parts.append(prompt)
        resp = client.models.generate_content(
            model=DEFAULT_TEXT_MODEL,
            contents=parts,
            config=types.GenerateContentConfig(
                system_instruction=system,
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )
        text = (resp.text or "").strip()
        if not text:
            return {"_error": True, "_error_message": "Model returned empty text."}
        return {"text": text}
    except Exception as exc:
        logger.error("AI vision call failed: %s", exc)
        return {"_error": True, "_error_message": str(exc)}

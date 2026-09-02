"""Palmistry analysis — two-step Gemini vision, refuse-don't-hallucinate.

Step 1: STRUCTURED EXTRACTION — the model returns strict JSON describing what is
actually visible (lines, mounts, hand shape). An unusable photo returns
{"usable": false, "reason": ...} and we ask for a retake instead of inventing.

Step 2: NARRATIVE — written from that JSON only (same discipline as the chart
reading: the writer never adds features the extractor didn't report).
"""

from __future__ import annotations

import json
import re

from .client import call_ai, call_ai_vision
from .guardrails import PROMPT_RULES, scrub

PROMPT_VERSION = "1.0.0"

_EXTRACT_SYSTEM = """You are a careful palmistry feature extractor. You look at
palm photographs and report ONLY what is clearly visible. You never guess.

Return STRICT JSON (no markdown fence, no commentary) with this shape:
{
  "usable": true/false,
  "reason": "only when unusable: blurry / too dark / not a palm / palm not open / too far",
  "hand": "left" | "right" | "unknown",
  "hand_shape": {"type": "earth|air|fire|water|unknown", "notes": "..."},
  "major_lines": {
    "heart": {"visible": bool, "length": "short|medium|long", "depth": "faint|moderate|deep", "curve": "straight|curved", "notes": "..."},
    "head":  {...same...},
    "life":  {...same...},
    "fate":  {"visible": bool, "notes": "..."},
    "sun":   {"visible": bool, "notes": "..."},
    "mercury": {"visible": bool, "notes": "..."}
  },
  "mounts": {"jupiter": "flat|developed|prominent", "saturn": "...", "apollo": "...",
             "mercury": "...", "venus": "...", "luna": "...", "mars": "..."},
  "fingers": {"relative_lengths": "...", "notes": "..."},
  "special_marks": ["only clearly visible marks: crosses, stars, islands, chains, grilles"]
}
Mark anything not clearly visible as "unknown" or visible:false. If the image is
not a clear open palm, set usable:false with the reason."""

_NARRATIVE_SYSTEM = f"""You are a warm, experienced palm reader writing from an
EXTRACTED FEATURE REPORT. You interpret ONLY the features in the report — if a
line or mount is marked unknown or not visible, you do not mention it or you say
it was not clearly visible. Classical palmistry meanings only (heart line —
emotional nature; head line — thinking style; life line — vitality NOT lifespan;
fate/sun/mercury — career, recognition, communication; mounts — planetary
temperaments; hand element — basic disposition).

{PROMPT_RULES}
Additional palm rule: the life line NEVER indicates lifespan or death — say so
explicitly if its length might be misread. 350-500 words, flowing prose, warm
and specific to the reported features. Write in the requested language."""


def _parse_json(text: str) -> dict | None:
    """Parse model JSON, salvaging the first {...} block if prose-wrapped."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                return None
    return None


def extract_features(images: list[bytes]) -> dict:
    result = call_ai_vision(_EXTRACT_SYSTEM,
                            "Extract palm features from these photo(s). STRICT JSON only.",
                            images, temperature=0.2)
    if result.get("_error"):
        return result
    data = _parse_json(result["text"])
    if data is None:
        return {"_error": True, "_error_message": "Feature extraction returned unparseable output."}
    if not data.get("usable", False):
        return {"usable": False,
                "reason": data.get("reason", "The photo was not clear enough to read.")}
    data["usable"] = True
    return data


def analyze_palm(images: list[bytes], language: str = "en") -> dict:
    """Full flow: extract → narrate → scrub. Never raises."""
    features = extract_features(images)
    if features.get("_error"):
        return features
    if not features.get("usable"):
        return {"usable": False, "reason": features["reason"],
                "retake_hint": "Open palm flat, fill the frame, bright even light, "
                               "no shadows across the palm."}

    lang_names = {"en": "English", "te": "Telugu (Telugu script)", "hi": "Hindi (Devanagari)"}
    prompt = (
        f"LANGUAGE: {lang_names.get(language, 'English')}\n\n"
        "=== EXTRACTED PALM FEATURES (the only features that exist) ===\n"
        + json.dumps(features, ensure_ascii=False)
    )
    result = call_ai(_NARRATIVE_SYSTEM, prompt, temperature=0.6)
    if result.get("_error"):
        return result
    cleaned = scrub(result["text"])
    return {
        "usable": True,
        "features": features,
        "reading": cleaned["text"],
        "violations_removed": cleaned["violations"],
        "language": language,
        "prompt_version": PROMPT_VERSION,
    }

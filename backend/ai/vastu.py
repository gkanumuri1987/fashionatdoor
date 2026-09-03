"""Vastu analysis — floor-plan photo → vision extraction → deterministic rules
→ narrative. Mirrors the palmistry pattern: the model EXTRACTS what it sees
(with confidence), vastu/rules.py JUDGES, the writer only narrates computed
findings. The plan image is processed in memory and never stored."""

from __future__ import annotations

import json

from vastu.rules import ZONES, evaluate

from .client import call_ai, call_ai_vision
from .guardrails import PROMPT_RULES, scrub

MIN_CONFIDENCE = 0.4

_EXTRACT_SYSTEM = f"""You are a careful floor-plan reader. You receive a floor
plan image and the direction that the TOP of the image faces (given in the
prompt). Report ONLY rooms you can clearly identify.

Return STRICT JSON (no markdown fence):
{{
  "usable": true/false,
  "reason": "only when unusable: not a floor plan / too blurry / unreadable labels",
  "overall_confidence": 0.0-1.0,
  "rooms": [
    {{"label": "text on the plan or best description",
      "type": "entrance|kitchen|master_bedroom|bedroom|pooja|toilet|bathroom|living|dining|study|store|staircase|water_tank|balcony|garage",
      "zone": "one of {ZONES} or center",
      "confidence": 0.0-1.0}}
  ]
}}
To find each room's zone: mentally rotate the plan so the given top-direction
is up, divide the dwelling's footprint into a 4x4 grid of compass sectors plus
the centre, and locate the room's centroid. Be conservative — when a room's
type or position is unclear, LOWER its confidence or omit it. Never invent
rooms that are not drawn."""

_NARRATIVE_SYSTEM = f"""You are a warm, practical Vastu counselor writing from a
COMPUTED FINDINGS REPORT. You interpret ONLY the findings given — never add
placements that are not listed, never frighten. For each notable finding,
explain the classical reasoning in one plain sentence; for avoid/grave
placements present the soft remedy honestly as mitigation. Praise what is
well-placed. End with the brahmasthan note and the disclaimer.

{PROMPT_RULES}
350-500 words, flowing prose, in the requested language."""


def analyze_floor_plan(image_bytes: bytes, top_direction: str,
                       language: str = "en", mime_type: str = "image/jpeg") -> dict:
    prompt = (f"The TOP of this floor plan faces: {top_direction}. "
              "Extract the rooms and their compass zones as instructed.")
    result = call_ai_vision(_EXTRACT_SYSTEM, prompt, [image_bytes], mime_type=mime_type)
    if result.get("_error"):
        return result
    try:
        raw = result["text"].strip()
        if raw.startswith("```"):
            raw = raw.strip("`").lstrip("json").strip()
        data = json.loads(raw[raw.index("{"):raw.rindex("}") + 1])
    except (ValueError, KeyError):
        return {"usable": False,
                "reason": "Could not read the floor plan — try a clearer, flatter photo."}
    conf = float(data.get("overall_confidence", 1.0) or 0)
    if not data.get("usable", False) or conf < MIN_CONFIDENCE:
        return {"usable": False,
                "reason": data.get("reason") or
                "The plan is not clear enough for an honest analysis — "
                "retake with the full plan flat and well-lit."}

    rooms = [r for r in data.get("rooms", [])
             if isinstance(r, dict) and float(r.get("confidence", 1.0) or 0) >= MIN_CONFIDENCE]
    if not rooms:
        return {"usable": False, "reason": "No rooms could be identified with confidence."}

    computed = evaluate(rooms)

    lang_names = {"en": "English", "te": "Telugu (Telugu script)", "hi": "Hindi (Devanagari)"}
    nprompt = (f"LANGUAGE: {lang_names.get(language, 'English')}\n"
               "=== COMPUTED VASTU FINDINGS (the only facts that exist) ===\n"
               + json.dumps(computed, ensure_ascii=False))
    narrative = call_ai(_NARRATIVE_SYSTEM, nprompt, temperature=0.6)
    if narrative.get("_error"):
        return {"usable": True, **computed, "narrative": None,
                "narrative_error": narrative["_error_message"]}
    cleaned = scrub(narrative["text"])
    return {"usable": True, **computed, "narrative": cleaned["text"],
            "extraction_confidence": conf, "language": language}

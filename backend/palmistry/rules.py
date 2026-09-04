"""Deterministic palmistry interpretation — the rules layer (Hasta Samudrika).

Same two-layer discipline as jyotish/ and vastu/: the vision model only
EXTRACTS the visible palm features (with confidence); THIS module maps each
feature to its classical meaning; the AI narrator only phrases the computed
findings. No meaning is improvised by the LLM, and no feature is invented.

Sources: the Indian Hasta Samudrika Shastra tradition and classical Western
palmistry (Cheiro). Freshly paraphrased — no copied text.

HARD RULES (also enforced downstream by ai/guardrails):
- The life line NEVER denotes lifespan, longevity, or timing of death — only
  constitution / vitality / energy. Every life-line finding says so.
- Special marks are presented as gentle classical signals, never as doom.
"""

from __future__ import annotations

# ── Hand shape → elemental temperament ───────────────────────────────────────
_HAND_ELEMENT = {
    "earth": ("Earth hand (square palm, short fingers)",
              "practical, grounded and reliable; you trust what is tangible and "
              "built to last, and you steady the people around you"),
    "air": ("Air hand (square palm, long fingers)",
            "intellectual, communicative and curious; you live in ideas, words "
            "and connections, and you reason before you feel"),
    "fire": ("Fire hand (long palm, short fingers)",
             "energetic, spontaneous and driven; you lead with instinct and "
             "action, warm and restless in equal measure"),
    "water": ("Water hand (long palm, long fingers)",
              "sensitive, intuitive and imaginative; you feel deeply and read a "
              "room before a word is spoken"),
}

# ── Major-line attribute meanings ────────────────────────────────────────────
# Each line composes its finding from the attributes the extractor reported.
_HEART_CURVE = {
    "curved": "warm, expressive and demonstrative in love — your feelings show",
    "straight": "loyal and self-contained in love — you love through steady acts "
                "more than grand words",
}
_HEART_LENGTH = {
    "long": "you give your heart fully and value deep, whole-hearted bonds",
    "medium": "you balance the heart's warmth with a clear head",
    "short": "you are selective and focused in affection — a few deep ties over many",
}
_HEAD_CURVE = {
    "straight": "a logical, practical, focused thinker who likes a clear line to the point",
    "curved": "an imaginative, flexible, creative thinker who sees round corners",
}
_HEAD_LENGTH = {
    "long": "thorough and wide-ranging — you like to think a thing all the way through",
    "medium": "a balanced thinker, neither hasty nor over-deliberating",
    "short": "decisive and to-the-point — you reach conclusions quickly",
}
_LIFE_DEPTH = {
    "deep": "a robust, steady constitution and dependable physical energy",
    "moderate": "a healthy, even vitality",
    "faint": "a finer constitution that rewards good rest and steady rhythms",
}
_LIFE_CURVE = {
    "curved": "a warm, outgoing physical vigour and love of life",
    "straight": "a measured, self-contained energy you spend deliberately",
}
_DEPTH_INTENSITY = {
    "deep": "strongly and clearly marked",
    "moderate": "clearly present",
    "faint": "lightly drawn",
}
_SECONDARY_LINE = {
    "fate": ("Fate line (Saturn line)",
             "a clear sense of direction and a self-made path — steadiness of career and purpose",
             "a free, self-directed path not bound to a single fixed track (its "
             "absence is never a lack of success — many self-made lives show a light fate line)"),
    "sun": ("Sun line (Apollo line)",
            "a capacity for recognition, creativity and the appreciation of others",
            "recognition that comes from within rather than the spotlight"),
    "mercury": ("Mercury line",
                "aptitude for communication, business and quick practical wit",
                "health and business themes read from other signs instead"),
}

# ── Mounts → planetary temperament, by development ───────────────────────────
_MOUNT_MEANING = {
    "jupiter": "ambition, confidence and natural leadership",
    "saturn": "discipline, responsibility and depth of character",
    "apollo": "creativity, warmth and the joy of self-expression",
    "mercury": "communication, wit and a head for commerce",
    "venus": "vitality, affection and a love of life and beauty",
    "luna": "imagination, intuition and empathy",
    "mars": "courage, resilience and steady drive",
}
_MOUNT_STATE = {
    "prominent": "strongly expressed",
    "developed": "healthily present",
    "flat": "understated — a quality you can grow into",
}

# ── Special marks (gentle, classical — never doom) ───────────────────────────
_MARK_MEANING = {
    "star": "a classical sign of a bright culmination or burst of good fortune "
            "in that area of life",
    "cross": "a crossing or turning point — a moment that asks for a considered choice",
    "island": "a temporary dip or divided focus in that line's theme, which passes",
    "chain": "a period of fluctuation in that line's theme — feelings or focus "
             "that ebb and flow",
    "grille": "scattered energy on that mount — a strength best gathered and "
              "channelled",
    "triangle": "a classical sign of talent and good judgement in that area",
    "square": "a mark of protection — a steadying, guarding influence",
}

_SOURCE = "Hasta Samudrika Shastra"


def _line_finding(name: str, entry: dict) -> dict | None:
    if not isinstance(entry, dict) or not entry.get("visible", False):
        return None
    length = (entry.get("length") or "").lower()
    depth = (entry.get("depth") or "").lower()
    curve = (entry.get("curve") or "").lower()
    parts: list[str] = []

    if name == "heart":
        if curve in _HEART_CURVE:
            parts.append(_HEART_CURVE[curve])
        if length in _HEART_LENGTH:
            parts.append(_HEART_LENGTH[length])
        label = "Heart line"
    elif name == "head":
        if curve in _HEAD_CURVE:
            parts.append(_HEAD_CURVE[curve])
        if length in _HEAD_LENGTH:
            parts.append(_HEAD_LENGTH[length])
        label = "Head line"
    elif name == "life":
        if depth in _LIFE_DEPTH:
            parts.append(_LIFE_DEPTH[depth])
        if curve in _LIFE_CURVE:
            parts.append(_LIFE_CURVE[curve])
        label = "Life line"
    else:
        return None

    if not parts:
        parts.append("clearly present" if depth not in _DEPTH_INTENSITY
                     else _DEPTH_INTENSITY[depth])

    finding = {"feature": label, "observation": _observed(entry),
               "meaning": "; ".join(parts), "source": _SOURCE}
    if name == "life":
        finding["caveat"] = ("The life line shows constitution and vitality — it "
                             "NEVER indicates lifespan or the timing of death.")
    return finding


def _observed(entry: dict) -> str:
    bits = [entry.get(k) for k in ("length", "depth", "curve") if entry.get(k)]
    return ", ".join(str(b) for b in bits) or "visible"


def interpret(features: dict) -> dict:
    """features: the extractor's report (ai/palm.extract_features output).
    Returns computed classical findings for the narrator — never raises."""
    findings: list[dict] = []
    traits: list[str] = []

    # Hand element
    shape = (features.get("hand_shape") or {})
    elem = (shape.get("type") or "unknown").lower()
    hand_element = None
    if elem in _HAND_ELEMENT:
        label, meaning = _HAND_ELEMENT[elem]
        hand_element = {"element": elem, "label": label, "meaning": meaning, "source": _SOURCE}
        findings.append({"feature": "Hand shape", "observation": label,
                         "meaning": meaning, "source": _SOURCE})
        traits.append(elem)

    # Major lines
    lines = features.get("major_lines") or {}
    for name in ("heart", "head", "life"):
        f = _line_finding(name, lines.get(name, {}))
        if f:
            findings.append(f)

    # Secondary lines (presence-based)
    _any_line_visible = any(isinstance(v, dict) and v.get("visible")
                            for v in lines.values())
    for name in ("fate", "sun", "mercury"):
        entry = lines.get(name) or {}
        if not isinstance(entry, dict):
            continue
        label, present_meaning, absent_meaning = _SECONDARY_LINE[name]
        if entry.get("visible", False):
            findings.append({"feature": label, "observation": "present",
                             "meaning": present_meaning, "source": _SOURCE})
        # Absence is reassured only for the fate line (the one people worry
        # about) AND only when the palm actually read some lines — never
        # fabricate a fate note for a palm where nothing was extracted.
        elif name == "fate" and _any_line_visible:
            findings.append({"feature": label, "observation": "faint or absent",
                             "meaning": absent_meaning, "source": _SOURCE})

    # Mounts
    mounts = features.get("mounts") or {}
    mount_findings = []
    for planet, state in mounts.items():
        p = str(planet).lower()
        s = str(state).lower()
        if p in _MOUNT_MEANING and s in _MOUNT_STATE:
            mount_findings.append({
                "feature": f"Mount of {planet.title()}",
                "observation": s,
                "meaning": f"{_MOUNT_STATE[s]} — {_MOUNT_MEANING[p]}",
                "source": _SOURCE,
            })
    findings.extend(mount_findings)

    # Special marks (gentle)
    mark_findings = []
    for raw in (features.get("special_marks") or []):
        key = str(raw).strip().lower()
        for mk, meaning in _MARK_MEANING.items():
            if mk in key:
                mark_findings.append({"feature": f"{mk.title()} mark",
                                      "observation": str(raw),
                                      "meaning": meaning, "source": _SOURCE})
                break

    return {
        "schema": "PalmReadingV1",
        "hand": features.get("hand", "unknown"),
        "hand_element": hand_element,
        "findings": findings,
        "special_marks": mark_findings,
        "traits": traits,
        "life_line_rule": ("The life line reflects vitality and constitution only "
                           "— never lifespan or death."),
        "disclaimer": ("Palmistry is offered for reflection and self-understanding, "
                       "not prediction — the hand describes tendencies, not a fixed fate."),
    }

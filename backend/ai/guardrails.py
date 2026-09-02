"""Output guardrails — non-negotiable, applied to every AI reading.

Two layers:
1. PROMPT_RULES injected into every system prompt.
2. scrub() post-filter: refuses/redacts forbidden claims that slip through.

Forbidden: death/lifespan timing, medical diagnosis or treatment, legal or
investment directives, fear-driven doom language, paid-remedy upselling.
"""

from __future__ import annotations

import re

PROMPT_RULES = """
NON-NEGOTIABLE RULES:
- NEVER predict death, cause of death, lifespan, or the timing of anyone's death.
- NEVER give a medical diagnosis, name a disease someone "will get", or prescribe
  treatment. Health themes stay general (vitality, stress, rest) and always add
  "consult a qualified doctor" for anything specific.
- NEVER give legal directives or investment/financial instructions (no "buy",
  "sell", "invest in", specific stocks, gold timing, or lottery/gambling claims).
- NEVER use fear to motivate: no doom, no curses, no "great danger awaits", and
  never sell remedies — remedies offered are free traditional practices only.
- NEVER state a planetary position, degree, date, or chart fact that is not in
  the COMPUTED FACTS given to you. You interpret; you do not calculate.
- Tone: a wise, warm elder — honest about challenges, never fatalistic. Every
  difficult indication comes with its classical remedial direction.
- End with: guidance for reflection, not a substitute for professional advice.
"""

_FORBIDDEN_PATTERNS = [
    (re.compile(r"\b(will|shall|going to)\s+(die|pass away)\b", re.I), "death prediction"),
    (re.compile(r"\b(death|mrityu)\s+(will|is likely|is predicted|occurs?)\b", re.I), "death prediction"),
    (re.compile(r"\blifespan\s+(is|of|will be)\s+\d", re.I), "lifespan claim"),
    (re.compile(r"\byou\s+(have|will\s+(get|develop|suffer))\s+(cancer|diabetes|tumou?r|heart\s+attack|stroke|hiv|aids)\b", re.I), "medical diagnosis"),
    (re.compile(r"\b(buy|sell|invest\s+in)\s+(stocks?|shares?|gold|crypto|bitcoin|land|property)\b", re.I), "investment directive"),
    (re.compile(r"\b(lottery|jackpot|gambling)\s+(win|luck|number)", re.I), "gambling claim"),
    (re.compile(r"\bpay\s+(for|us|me)\s+.{0,30}(remedy|pooja|puja|yagya|gemstone)", re.I), "paid remedy upsell"),
]

DISCLAIMER = ("This reading is offered for guidance and reflection. It is not a "
              "substitute for professional medical, legal, or financial advice.")


def scrub(text: str) -> dict:
    """Returns {"text": cleaned, "violations": [...]} — violating sentences are
    removed, never rewritten (rewriting risks softening a claim that shouldn't
    exist at all)."""
    violations: list[str] = []
    kept: list[str] = []
    # Split on sentence-ish boundaries, preserving markdown structure lines.
    for line in text.split("\n"):
        sentences = re.split(r"(?<=[.!?])\s+", line) if line.strip() else [line]
        kept_sentences = []
        for s in sentences:
            hit = next((label for pat, label in _FORBIDDEN_PATTERNS if pat.search(s)), None)
            if hit:
                violations.append(f"{hit}: {s.strip()[:120]}")
            else:
                kept_sentences.append(s)
        kept.append(" ".join(kept_sentences))
    cleaned = "\n".join(kept).strip()
    if DISCLAIMER.split(".")[0].lower() not in cleaned.lower():
        cleaned = f"{cleaned}\n\n_{DISCLAIMER}_"
    return {"text": cleaned, "violations": violations}


def refuse_topic(question: str) -> str | None:
    """Hard refusals for direct forbidden asks (used when free-text questions land)."""
    q = question.lower()
    if re.search(r"\b(when|how)\b.{0,40}\b(die|death|pass away)\b", q):
        return ("Jyotish tradition itself counsels against death prediction, and this "
                "service never provides it. I can speak to health themes and "
                "longevity-supporting practices instead.")
    if re.search(r"\b(disease|diagnos|cancer|tumou?r)\b", q):
        return ("I can't diagnose or predict medical conditions. For health, please "
                "consult a qualified doctor; I can discuss general vitality themes "
                "in the chart.")
    if re.search(r"\b(stock|share|crypto|bitcoin|lottery|gambl|bet)\b", q):
        return ("I don't give investment or gambling guidance. I can discuss the "
                "chart's general themes around wealth-building temperament instead.")
    return None

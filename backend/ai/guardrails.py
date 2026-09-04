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
    # Death / lifespan — cover the plain future forms AND the softer euphemisms.
    (re.compile(r"\b(will|shall|going to|may|might)\s+(die|pass away|perish|not survive)\b", re.I), "death prediction"),
    (re.compile(r"\b(death|mrityu|demise|passing)\s+(will|is likely|is predicted|is imminent|occurs?|awaits)\b", re.I), "death prediction"),
    (re.compile(r"\byour\s+(life|end|time)\s+(will|shall|is going to)\s+end", re.I), "death prediction"),
    (re.compile(r"\b(fatal|terminal|life-?threatening|life will end|end of (your )?life)\b", re.I), "death/fatality claim"),
    (re.compile(r"\blife\s*span\s+(is|of|will be)\s+\d", re.I), "lifespan claim"),
    (re.compile(r"\b(longevity|how long).{0,20}\b(is|will be|of)\s+\d", re.I), "lifespan claim"),
    # Medical — the fixed disease list PLUS a generic "you will get/develop <condition>".
    (re.compile(r"\byou\s+(have|will\s+(get|develop|suffer\s+from?|contract)|are\s+going\s+to\s+(get|develop))\s+(a\s+|an\s+)?(cancer|diabetes|tumou?r|heart\s+attack|stroke|hiv|aids|kidney|liver|failure|disease|disorder|illness|infection|paralysis)\b", re.I), "medical diagnosis"),
    (re.compile(r"\b(diagnos|prescrib)\w*\b", re.I), "medical directive"),
    # Financial — directives and the softer "put your money/savings into".
    (re.compile(r"\b(buy|sell|invest\s+in|put\s+(your\s+)?(money|savings|funds)\s+(in|into))\s+(stocks?|shares?|gold|silver|crypto|bitcoin|land|property|real\s*estate|mutual\s+funds?)\b", re.I), "investment directive"),
    (re.compile(r"\b(lottery|jackpot|gambl\w+|betting)\s+(win|luck|number|success)", re.I), "gambling claim"),
    (re.compile(r"\bpay\s+(for|us|me)\s+.{0,30}(remedy|pooja|puja|yagya|homa|gemstone|dosha)", re.I), "paid remedy upsell"),
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
    """Hard refusals for direct forbidden asks — checked on the INPUT before any
    model call, so a "when will I die?" / disease / stock question is never sent
    to the LLM. This is the primary safety net; scrub() is defense-in-depth on
    the output. Wire this at the top of every free-text path (chat)."""
    q = question.lower()
    if re.search(r"\b(longevity|life\s*span|when will i die|how long will i live)\b", q) \
            or re.search(r"\b(when|how|how\s+long).{0,45}\b(die|death|pass away|live|survive|end of (my |your )?life)\b", q) \
            or re.search(r"\b(when|will|how\s+long).{0,25}\b(i|we|he|she|they)\b.{0,15}\b(die|live|last)\b", q):
        return ("Jyotish tradition itself counsels against death and lifespan "
                "prediction, and this service never provides it. I can speak to "
                "health themes and longevity-supporting practices instead.")
    if re.search(r"\b(disease|diagnos|cancer|tumou?r|illness|what\s+sickness|will\s+i\s+(get|have)\s+(sick|ill)|medical\s+condition)\b", q):
        return ("I can't diagnose or predict medical conditions. For health, please "
                "consult a qualified doctor; I can discuss general vitality themes "
                "in the chart.")
    if re.search(r"\b(stock|share\s+price|crypto|bitcoin|lottery|jackpot|gambl|which\s+.{0,15}\b(buy|sell)|should\s+i\s+(buy|sell|invest))\b", q):
        return ("I don't give investment or gambling guidance. I can discuss the "
                "chart's general themes around wealth-building temperament instead.")
    return None


# ── Anti-hallucination tripwire ──────────────────────────────────────────────
# The prompt tells the model never to state a degree/date not in the facts, but
# a prompt rule is only advisory. This is the enforcement: any calendar year or
# ecliptic-degree token in the OUTPUT that is not present in the FACTS handed to
# the model is a fabrication — the sentence carrying it is removed.

_DEGREE_RE = re.compile(r"\b\d{1,3}(?:\.\d+)?\s?(?:°|degrees?|deg\b|arc\s?min)", re.I)
_DMS_RE = re.compile(r"\d{1,3}\s?°\s?\d{1,2}\s?['′]")
_YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")


def verify_grounding(text: str, facts_text: str = "") -> dict:
    """Redact sentences that assert a degree/DMS position, or a calendar year
    that does not appear in ``facts_text`` (the exact facts JSON given to the
    model — every legitimate dasha/transit date is in there). Returns
    {"text": cleaned, "violations": [...]}."""
    allowed_years = set(_YEAR_RE.findall(facts_text or ""))
    violations: list[str] = []
    kept_lines: list[str] = []
    for line in text.split("\n"):
        sentences = re.split(r"(?<=[.!?])\s+", line) if line.strip() else [line]
        kept: list[str] = []
        for s in sentences:
            reason = None
            if _DEGREE_RE.search(s) or _DMS_RE.search(s):
                reason = "ungrounded degree"
            else:
                fabricated = [y for y in _YEAR_RE.findall(s) if y not in allowed_years]
                if fabricated:
                    reason = f"ungrounded date ({', '.join(sorted(set(fabricated)))})"
            if reason:
                violations.append(f"{reason}: {s.strip()[:120]}")
            else:
                kept.append(s)
        kept_lines.append(" ".join(kept))
    return {"text": "\n".join(kept_lines).strip(), "violations": violations}


def sanitize(text: str, facts_text: str = "") -> dict:
    """Full output pass: strip fabricated numbers/dates (verify_grounding) then
    forbidden topical claims (scrub). Use this instead of a bare scrub() on any
    path that hands the model computed chart dates."""
    grounded = verify_grounding(text, facts_text)
    cleaned = scrub(grounded["text"])
    return {"text": cleaned["text"],
            "violations": grounded["violations"] + cleaned["violations"]}

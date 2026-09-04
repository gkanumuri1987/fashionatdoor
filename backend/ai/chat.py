"""Jaathakam chat assistant — question answering grounded ONLY in the
computed chart.

The user asks in their own words ("when will I marry?", "career improvement",
"children?", "summarize everything"). The assistant receives the SAME
receipted material as the reading engine — claims with weights, resolved
verdicts, the dasha timeline with real dates, current transits — plus
house-topic hints, and must answer from those facts alone. Timing questions
are answered as DASHA WINDOWS (real dates from the computed vimshottari),
never invented dates. Guardrails apply in full (no death/lifespan timing, no
medical/legal/financial directives, no fear).
"""

from __future__ import annotations

import json

from jyotish.chart import transit_report

from .client import call_ai
from .guardrails import PROMPT_RULES, refuse_topic, sanitize
from .presentation import reading_page

_SYSTEM = f"""You are a warm, experienced Jyotish counselor in a CHAT with the
person whose computed jaathakam is provided. Answer their question directly,
personally and briefly (120-250 words), like a wise elder — plain words,
honest, encouraging, never fatalistic.

HARD RULES:
- Answer ONLY from the COMPUTED FACTS, RANKED CLAIMS, VERDICTS, TIMELINE and
  TRANSITS given. Never invent a position, yoga, or date.
- TIMING questions (marriage, children, career changes): frame answers as the
  relevant DASHA/ANTARDASHA WINDOWS from the timeline — quote their real
  start/end dates — plus supportive transits. Say plainly that windows show
  FAVOURABLE PERIODS, not certainties.
- Marriage → judge 7th house, Venus, the upapada; children → 5th house,
  Jupiter; career → 10th house, Saturn/Sun and the current dasha. Use the
  claims that touch those factors.
- "Summary" requests: weave the strongest claims and every topic verdict into
  one flowing overview.
- If the birth time was inexact (uncertainty notes present), soften
  house-based statements and say why once.
- If a question cannot be answered from this chart's facts, say so honestly
  and suggest what could (e.g. a rectified birth time, the partner's chart
  for matching).

{PROMPT_RULES}
Reply in the requested language. No headings; conversational prose.
"""


def answer_question(chart: dict, question: str, language: str = "en",
                    history: list[dict] | None = None) -> dict:
    """One chat turn. history: [{"role": "user"|"assistant", "text": ...}]."""
    # Hard input refusal BEFORE any model call — death/lifespan, medical, or
    # financial asks are never sent to the LLM (primary safety net; sanitize()
    # on the output is defense-in-depth).
    refusal = refuse_topic(question or "")
    if refusal:
        return {"answer": refusal, "violations_removed": ["refused: forbidden topic"],
                "language": language, "refused": True}
    page = reading_page(chart, language)
    try:
        transits = transit_report(chart)
        transit_slim = {
            "sade_sati": transits["sade_sati"],
            "tarabala": transits.get("tarabala"),
            "jupiter": transits["transits"]["jupiter"],
            "saturn": transits["transits"]["saturn"],
        }
    except Exception:
        transit_slim = None

    lang_names = {"en": "English", "te": "Telugu (Telugu script)", "hi": "Hindi (Devanagari)"}
    convo = ""
    for h in (history or [])[-6:]:
        role = "Person" if h.get("role") == "user" else "You"
        convo += f"{role}: {h.get('text', '')}\n"

    prompt = (
        f"LANGUAGE: {lang_names.get(language, 'English')}\n"
        + (f"\n=== CONVERSATION SO FAR ===\n{convo}" if convo else "")
        + f"\n=== THE PERSON'S QUESTION ===\n{question.strip()[:500]}\n"
        + "\n=== COMPUTED FACTS ===\n"
        + json.dumps({
            "lagna": chart["lagna"]["sign_name"],
            "moon": {"sign": chart["moon_sign_name"],
                     "nakshatra": chart["grahas"]["moon"]["nakshatra"]["name"]},
            "grahas": {g: {"sign": gd["sign_name"], "house": gd["house"],
                           "dignity": gd["dignity"], "retrograde": gd["retrograde"]}
                       for g, gd in chart["grahas"].items()},
            "functional_lords": chart.get("functional_lords", {}).get("yogakaraka"),
            "upapada_sign": (chart.get("jaimini") or {}).get("arudha_padas", {}).get("UL"),
            "time_accuracy": chart["input"]["time_accuracy"],
        }, ensure_ascii=False)
        + "\n\n=== RANKED CLAIMS (your only permitted statements) ===\n"
        + json.dumps(page["claims"], ensure_ascii=False)
        + "\n\n=== TOPIC VERDICTS (already weighed) ===\n"
        + json.dumps(page["verdicts"], ensure_ascii=False)
        + "\n\n=== DASHA TIMELINE (real dates — use THESE for timing) ===\n"
        + json.dumps(page["timeline"], ensure_ascii=False)
        + ("\n\n=== CURRENT TRANSITS ===\n" + json.dumps(transit_slim, ensure_ascii=False)
           if transit_slim else "")
        + ("\n\n=== UNCERTAINTY ===\n" + json.dumps(page["uncertainty"], ensure_ascii=False)
           if page["uncertainty"] else "")
    )

    result = call_ai(_SYSTEM, prompt, temperature=0.6)
    if result.get("_error"):
        return result
    # Anti-hallucination: the prompt (with every permitted date/fact) is the
    # grounding source — any year or degree in the answer that isn't in it is a
    # fabrication and its sentence is dropped.
    cleaned = sanitize(result["text"], facts_text=prompt)
    return {"answer": cleaned["text"],
            "violations_removed": cleaned["violations"],
            "language": language}

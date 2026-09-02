"""Life-reading generation — chart facts + retrieved dictums → sectioned prose.

The prompt contract is the whole game: the model interprets ONLY the computed
facts and dictums it is handed. It never computes, never adds positions/dates.
"""

from __future__ import annotations

import json

from .client import call_ai
from .guardrails import PROMPT_RULES, scrub
from .retrieval import archetypes_for_chart, dictums_for_chart

PROMPT_VERSION = "1.0.0"

SECTIONS = {
    "personality": "Personality & core nature (lagna, Moon, Sun, their dignities)",
    "career": "Career & purpose — artha (10th house themes, Saturn, Sun, current dasha)",
    "wealth": "Wealth & resources (2nd/11th themes, Jupiter, dhana indications)",
    "relationships": "Relationships & marriage (7th house themes, Venus, Moon)",
    "health": "Health & vitality — GENERAL themes only (lagna strength, 6th house)",
    "dharma": "Dharma & spiritual path (9th/12th themes, Jupiter, Ketu, the Puranic archetypes)",
    "dasha_outlook": "Current dasha outlook — what this period classically foregrounds",
    "remedies": "Traditional free remedies (from the archetype entries only)",
}

_SYSTEM = f"""You are an experienced, warm Jyotish counselor writing a life reading.
You speak like a wise elder: plain words, honest, encouraging, never fatalistic.

You are given COMPUTED FACTS (from a Swiss Ephemeris engine) and CLASSICAL
DICTUMS with sources (freshly paraphrased from BPHS, Phaladeepika, Saravali,
and Puranic archetypes). Your job is ONLY to weave these into flowing prose for
the requested section — synthesize, reconcile tensions between dictums using the
dignity/combustion/retrograde qualifiers, and make it personal and readable.

{PROMPT_RULES}

Write in the requested language. Cite sources sparingly in-line like (BPHS) —
at most a few per section. 250-400 words for the section. No headings, no lists
unless the section is 'remedies' (remedies may be a short list).
"""


def generate_reading(chart: dict, section: str, language: str = "en") -> dict:
    """Returns {"section", "text", "violations", "prompt_version"} or {"_error"...}."""
    if section not in SECTIONS:
        return {"_error": True, "_error_message": f"Unknown section '{section}'."}

    dictums = dictums_for_chart(chart)
    archetypes = archetypes_for_chart(chart)

    facts = {
        "lagna": chart["lagna"],
        "grahas": {g: {k: v for k, v in gd.items() if k != "vargas"}
                   for g, gd in chart["grahas"].items()},
        "yogas": chart["yogas"],
        "panchanga": chart["panchanga"],
        "current_dasha": chart["current_dasha"],
        "moon_sign": chart["moon_sign_name"],
        "time_accuracy": chart["input"]["time_accuracy"],
    }

    lang_names = {"en": "English", "te": "Telugu (Telugu script)", "hi": "Hindi (Devanagari)"}
    prompt = (
        f"SECTION TO WRITE: {SECTIONS[section]}\n"
        f"LANGUAGE: {lang_names.get(language, 'English')}\n"
        + ("NOTE: birth time is not exact — soften lagna-dependent claims and say so once.\n"
           if facts["time_accuracy"] != "exact" else "")
        + "\n=== COMPUTED FACTS (the only chart facts that exist) ===\n"
        + json.dumps(facts, ensure_ascii=False, default=str)
        + "\n\n=== CLASSICAL DICTUMS TRIGGERED BY THIS CHART ===\n"
        + json.dumps(dictums, ensure_ascii=False)
        + "\n\n=== PURANIC ARCHETYPES FOR THIS CHART'S PIVOTAL GRAHAS ===\n"
        + json.dumps(archetypes, ensure_ascii=False)
    )

    result = call_ai(_SYSTEM, prompt, temperature=0.65)
    if result.get("_error"):
        return result
    cleaned = scrub(result["text"])
    return {
        "section": section,
        "language": language,
        "text": cleaned["text"],
        "violations_removed": cleaned["violations"],
        "prompt_version": PROMPT_VERSION,
        "dictum_count": len(dictums),
    }


def generate_match_narrative(milan: dict, language: str = "en") -> dict:
    """Compatibility narrative from a computed MilanV1 — never invents points."""
    lang_names = {"en": "English", "te": "Telugu (Telugu script)", "hi": "Hindi (Devanagari)"}
    slim = {k: v for k, v in milan.items() if k not in ("boy_chart", "girl_chart")}
    prompt = (
        f"LANGUAGE: {lang_names.get(language, 'English')}\n"
        "Write a warm, honest 300-450 word compatibility narrative from this COMPUTED "
        "Ashtakoota result. State the total exactly as given. Walk through the kootas "
        "that scored low WITH their classical exceptions where present (nadi/bhakoot "
        "exceptions matter — a dosha with a classical exception must be presented as "
        "mitigated, not as doom). Present Manglik status exactly as computed. Do not "
        "invent numbers, remedies beyond tradition, or a verdict stronger than the data.\n\n"
        "=== COMPUTED MATCH (the only facts that exist) ===\n"
        + json.dumps(slim, ensure_ascii=False)
    )
    result = call_ai(_SYSTEM, prompt, temperature=0.6)
    if result.get("_error"):
        return result
    cleaned = scrub(result["text"])
    return {"text": cleaned["text"], "violations_removed": cleaned["violations"],
            "language": language, "prompt_version": PROMPT_VERSION}

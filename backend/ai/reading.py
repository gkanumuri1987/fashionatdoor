"""Life-reading generation — chart facts + retrieved dictums → sectioned prose.

The prompt contract is the whole game: the model interprets ONLY the computed
facts and dictums it is handed. It never computes, never adds positions/dates.
"""

from __future__ import annotations

import json

from .client import call_ai
from .guardrails import PROMPT_RULES, scrub
from .presentation import reading_page
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
computed WEIGHTS when present (weight is the graha's Shadbala strength ratio:
>=1.0 means the graha can deliver its promise — emphasize; <0.8 means the theme
is present but muted — mention briefly and honestly). A dictum flagged
"cancelled_by" is substantially neutralized — present the affliction as
overcome, never as an active curse. Judge primarily from the
dignity/combustion/retrograde qualifiers, and make it personal and readable.
Any point listed in boundary_alerts sits within arc-minutes of a sign/
nakshatra/pada boundary — a tiny birth-time error flips it, so soften any
claim that hangs on that placement and say why once, briefly.
When use_chandra_lagna is true the birth time was unknown: judge from the Moon
(Chandra lagna) and say so once, plainly. In the dharma and remedies sections,
when an ishta_devata is given, present that deity as the chart's own worship
direction (Jaimini karakamsa) — the most personal remedy there is.

{PROMPT_RULES}

Write in the requested language. Cite sources sparingly in-line like (BPHS) —
at most a few per section. 250-400 words for the section. No headings, no lists
unless the section is 'remedies' (remedies may be a short list).
"""


def generate_reading(chart: dict, section: str, language: str = "en") -> dict:
    """Returns {"section", "text", "violations", "prompt_version"} or {"_error"...}."""
    if section not in SECTIONS:
        return {"_error": True, "_error_message": f"Unknown section '{section}'."}

    page = reading_page(chart, language)
    # Rank claims: full > firm > moderate > thin (the writer sequences, never re-weighs).
    _order = {"full": 0, "firm": 1, "moderate": 2, "thin": 3}
    ranked_claims = sorted(page["claims"], key=lambda c: _order.get(c["strength"], 2))
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
    if chart.get("boundary_alerts"):
        facts["boundary_alerts"] = chart["boundary_alerts"]
    for key in ("functional_lords", "shadbala_summary", "use_chandra_lagna"):
        if chart.get(key):
            facts[key] = chart[key]
    jm = chart.get("jaimini") or {}
    if jm:
        facts["jaimini"] = {
            "atmakaraka": jm.get("chara_karakas", {}).get("karakas", {}).get("AK"),
            "karakamsa": jm.get("karakamsa"),
            "ishta_devata": jm.get("ishta_devata"),
            "arudha_lagna_sign": jm.get("arudha_padas", {}).get("AL"),
            "upapada_sign": jm.get("arudha_padas", {}).get("UL"),
        }

    # "What's active now": the dasha-outlook section additionally receives the
    # LIVE computed transit context (never model-recalled) — gochara over the
    # natal Moon is what this section is classically judged from.
    if section == "dasha_outlook":
        try:
            from jyotish.chart import transit_report
            rep = transit_report(chart)
            facts["current_transits"] = {
                "as_of": rep["as_of"],
                "sade_sati": rep["sade_sati"],
                "shani_flags": rep["shani_flags"],
                "tarabala": rep["tarabala"],
                "chandrabala": rep["chandrabala"],
                "jupiter_from_moon": rep["jupiter_from_moon"],
                "saturn": rep["transits"]["saturn"],
                "jupiter": rep["transits"]["jupiter"],
                "rahu": rep["transits"]["rahu"],
            }
        except Exception:  # pragma: no cover — reading must not die on transits
            pass

    lang_names = {"en": "English", "te": "Telugu (Telugu script)", "hi": "Hindi (Devanagari)"}
    prompt = (
        f"SECTION TO WRITE: {SECTIONS[section]}\n"
        f"LANGUAGE: {lang_names.get(language, 'English')}\n"
        + ("NOTE: birth time is not exact — soften lagna-dependent claims and say so once.\n"
           if facts["time_accuracy"] != "exact" else "")
        + "\n=== COMPUTED FACTS (the only chart facts that exist) ===\n"
        + json.dumps(facts, ensure_ascii=False, default=str)
        + "\n\n=== RANKED CLAIMS (pre-worded, with receipts — your ONLY source "
          "of statements; sequence and tone them, never invent beyond them; a "
          "claim marked thin is mentioned briefly or omitted; a cancellation "
          "means the affliction is overcome) ===\n"
        + json.dumps(ranked_claims, ensure_ascii=False)
        + "\n\n=== RESOLVED VERDICTS (one per topic — already weighed; never "
          "present competing views as unresolved) ===\n"
        + json.dumps(page["verdicts"], ensure_ascii=False)
        + "\n\n=== TIMELINE ===\n"
        + json.dumps({"current": page["timeline"]["current_sentence"],
                      "next_change": page["timeline"]["next_change"]}, ensure_ascii=False)
        + "\n\n=== UNCERTAINTY NOTES (state each once, plainly) ===\n"
        + json.dumps(page["uncertainty"], ensure_ascii=False)
        + "\n\n=== GLOSSES (use these plain twins for technical terms) ===\n"
        + json.dumps(page["glosses"], ensure_ascii=False)
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

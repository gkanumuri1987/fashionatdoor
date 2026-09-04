"""ReadingPageV1 — the deterministic presentation contract.

The seven rules this module enforces BEFORE any writer sees the data:
1. Numbers become words: Shadbala → strength bars (strong/balanced/thin),
   SAV bindus → supportive/neutral/thin. Raw numbers live only in the
   "why" layer.
2. Every sentence carries a receipt: each claim is
   {claim, chart_condition, source, strength, cancellations} — a sentence
   with no receipt cannot be rendered.
3. One verdict per topic: lagna-view vs Chandra-lagna-view contradictions are
   resolved HERE by weighting; the writer never receives two competing
   dictums without a winner marked.
4. Time is a timeline: maha bands with a you-are-here marker, the current
   sub-period in one sentence, the next change date. Prana tables live under
   the astrologer view.
5. Plain language with glosses: lagna/rasi/dasha kept; other terms get a
   two-word gloss per language (spoken register, not panchangam Sanskrit).
6. Uncertainty is shown: birth-time bands and boundary alerts become
   one-line notes, never silently dropped.
7. Depth is opt-in: plain → why → full tables.

No AI imports. Pure function of a ChartV1 dict.
"""

from __future__ import annotations

from .retrieval import dictums_for_chart

# Rule 5 — two-word glosses, spoken register per language.
GLOSSES: dict[str, dict[str, str]] = {
    "yogakaraka": {"en": "your key planet", "te": "మీ కీలక గ్రహం", "hi": "आपका मुख्य ग्रह"},
    "maraka": {"en": "health-sensitive lord", "te": "ఆరోగ్య సూచక గ్రహం", "hi": "स्वास्थ्य-संवेदी ग्रह"},
    "badhaka": {"en": "obstacle lord", "te": "అడ్డంకుల గ్రహం", "hi": "बाधक ग्रह"},
    "moolatrikona": {"en": "power seat", "te": "బల స్థానం", "hi": "बल स्थान"},
    "debilitated": {"en": "at its weakest sign", "te": "బలహీన రాశిలో", "hi": "नीच राशि में"},
    "exalted": {"en": "at its strongest sign", "te": "ఉచ్ఛ రాశిలో", "hi": "उच्च राशि में"},
    "combust": {"en": "too close to the Sun", "te": "సూర్యుని దగ్గరగా", "hi": "सूर्य के अति निकट"},
    "retrograde": {"en": "moving backward", "te": "వక్ర గతిలో", "hi": "वक्री"},
    "vargottama": {"en": "doubly placed", "te": "రెట్టింపు బలం", "hi": "दुगुना स्थित"},
    "kendra": {"en": "power house", "te": "కేంద్ర స్థానం", "hi": "केंद्र भाव"},
    "trikona": {"en": "fortune house", "te": "త్రికోణ స్థానం", "hi": "त्रिकोण भाव"},
    "sade_sati": {"en": "Saturn's long test", "te": "శని ఏలినాటి", "hi": "साढ़े साती"},
    "gulika": {"en": "Saturn's shadow point", "te": "శని ఛాయా బిందువు", "hi": "शनि छाया बिंदु"},
    "pranapada": {"en": "breath point", "te": "ప్రాణ బిందువు", "hi": "प्राण बिंदु"},
    "ishta_devata": {"en": "your worship deity", "te": "మీ ఇష్ట దైవం", "hi": "आपके इष्ट देव"},
}

# Topic → the houses and karakas that decide its verdict.
_TOPIC_FACTORS: dict[str, dict] = {
    "career": {"houses": [10, 6], "karakas": ["saturn", "sun", "mercury"]},
    "wealth": {"houses": [2, 11], "karakas": ["jupiter"]},
    "relationships": {"houses": [7, 5], "karakas": ["venus", "moon"]},
    "health": {"houses": [1, 6, 8], "karakas": ["sun", "saturn"]},
    "dharma": {"houses": [9, 12, 5], "karakas": ["jupiter", "ketu"]},
    "personality": {"houses": [1], "karakas": ["sun", "moon"]},
}


def _strength_word(ratio: float) -> str:
    if ratio >= 1.0:
        return "strong"
    if ratio >= 0.8:
        return "balanced"
    return "thin"


def _sav_word(bindus: int) -> str:
    if bindus >= 30:
        return "supportive"
    if bindus >= 25:
        return "neutral"
    return "thin"


def _claim_strength(weight: float | None) -> str:
    if weight is None:
        return "firm"
    if weight >= 1.2:
        return "full"
    if weight >= 1.0:
        return "firm"
    if weight >= 0.8:
        return "moderate"
    return "thin"


def strength_bars(chart: dict) -> dict:
    """Rule 1: Shadbala ratios and SAV bindus as words + bar percentages."""
    bars = {}
    for g, e in (chart.get("shadbala_summary") or {}).items():
        ratio = e["rupas"] / e["required"] if e.get("required") else 1.0
        bars[g] = {
            "level": _strength_word(ratio),
            "bar_percent": min(100, round(ratio * 62)),
            "why": {"rupas": e["rupas"], "required": e["required"]},
        }
    house_bars = {}
    for b in chart.get("bhavas", []):
        sb = b.get("sav_bindus")
        if sb is not None:
            house_bars[b["house"]] = {"level": _sav_word(sb), "why": {"sav_bindus": sb}}
    return {"grahas": bars, "houses": house_bars}


def build_claims(chart: dict) -> list[dict]:
    """Rule 2: every renderable statement as a receipted claim."""
    claims = []
    for i, d in enumerate(dictums_for_chart(chart)):
        claims.append({
            "id": f"C{i:03d}",
            "claim": d["dictum"],
            "chart_condition": d["trigger"],
            "source": d["source"],
            "strength": _claim_strength(d.get("weight")),
            "cancellations": [d["cancelled_by"]] if d.get("cancelled_by") else [],
        })
    return claims


def _house_score(chart: dict, house: int, from_sign: int) -> float:
    """Score a house seen from a reference sign: SAV of the sign + occupants'
    and lord's shadbala."""
    sign = (from_sign + house - 1) % 12
    sav = (chart.get("ashtakavarga") or {}).get("sarva")
    score = 0.0
    if sav:
        score += (sav[sign] - 28.0) / 8.0  # centered on the SAV mean
    sb = chart.get("shadbala_summary") or {}
    from_lagna_house = (sign - chart["lagna"]["sign"]) % 12 + 1
    for g, gd in chart["grahas"].items():
        if gd["house"] == from_lagna_house and g in sb:
            ratio = sb[g]["rupas"] / sb[g]["required"]
            score += (ratio - 1.0) * 1.5
    lord = chart["bhavas"][from_lagna_house - 1]["lord"]
    if lord in sb:
        score += (sb[lord]["rupas"] / sb[lord]["required"] - 1.0) * 2.0
    return score


def resolve_verdicts(chart: dict) -> dict:
    """Rule 3: one weighted verdict per topic, lagna-view vs Chandra-view
    resolved here. Unknown birth time → the Chandra view carries all weight."""
    lagna_sign = chart["lagna"]["sign"]
    moon_sign = chart["moon_sign"]
    lagna_w = 0.0 if chart.get("use_chandra_lagna") else 0.6
    moon_w = 1.0 - lagna_w
    sb = chart.get("shadbala_summary") or {}
    out = {}
    for topic, f in _TOPIC_FACTORS.items():
        views = []
        total = 0.0
        for label, ref, w in (("lagna", lagna_sign, lagna_w), ("chandra", moon_sign, moon_w)):
            if w <= 0:
                continue
            v = sum(_house_score(chart, h, ref) for h in f["houses"]) / len(f["houses"])
            views.append({"view": label, "score": round(v, 3), "weight": w})
            total += v * w
        for k in f["karakas"]:
            if k in sb:
                total += (sb[k]["rupas"] / sb[k]["required"] - 1.0) * 0.5
        verdict = ("supportive" if total >= 0.35 else
                   "challenging" if total <= -0.35 else "mixed")
        out[topic] = {"verdict": verdict, "score": round(total, 3),
                      "views_resolved": views}
    return out


def dasha_timeline(chart: dict) -> dict:
    """Rule 4: maha bands + you-are-here + one-sentence current period."""
    v = chart.get("vimshottari") or {}
    cur = chart.get("current_dasha") or {}
    now_maha = cur.get("maha")
    bands = []
    marker = None
    # Display one lifetime (the first vimshottari cycle = 9 mahadashas ≈ 120y);
    # the engine now holds a second cycle for current-period resolution beyond
    # that, but a 240-year on-screen timeline would be noise.
    for m in v.get("mahadashas", [])[:9]:
        band = {"lord": m["lord"], "start": m["start"][:10], "end": m["end"][:10],
                "years": m["years"], "current": m["lord"] == now_maha}
        if band["current"] and cur.get("maha_end"):
            total = m["end_jd"] - m["start_jd"]
            # position derived from the antar end vs band — approximate marker
            marker = {"lord": m["lord"], "start": band["start"], "end": band["end"]}
        bands.append(band)
    sentence = None
    if cur:
        sentence = (f"You are in the {cur['maha']} mahadasha, {cur['antar']} "
                    f"sub-period, until {str(cur.get('antar_end', ''))[:10]}.")
    return {"bands": bands, "you_are_here": marker,
            "current_sentence": sentence,
            "next_change": str(cur.get("antar_end", ""))[:10] or None,
            "astrologer_view": "full antar/pratyantar tables in the chart JSON"}


def uncertainty_notes(chart: dict) -> list[str]:
    """Rule 6: every precision caveat as one plain line."""
    notes = []
    ls = chart.get("lagna_sensitivity")
    if ls and not ls.get("stable", True):
        notes.append("Your birth time uncertainty spans more than one rising "
                     "sign — house-based results are tentative; Moon-based "
                     "results are firm.")
    elif ls:
        notes.append("Birth time is approximate, but the rising sign holds "
                     "across the band — house results are dependable.")
    for a in chart.get("boundary_alerts", []):
        notes.append(f"The {a['point']} sits within {a['arc_minutes']}' of a "
                     f"{a['boundary']} boundary — a few minutes of birth-time "
                     "error would move it.")
    tn = (chart.get("input") or {}).get("time_note")
    if tn:
        notes.append(tn)
    return notes


def reading_page(chart: dict, language: str = "en") -> dict:
    """The full ReadingPageV1 contract (Rule 7: plain / why / tables depth)."""
    claims = build_claims(chart)
    return {
        "schema": "ReadingPageV1",
        "language": language,
        "strength_bars": strength_bars(chart),
        "claims": claims,
        "verdicts": resolve_verdicts(chart),
        "timeline": dasha_timeline(chart),
        "glosses": {k: v.get(language, v["en"]) for k, v in GLOSSES.items()},
        "uncertainty": uncertainty_notes(chart),
        "depth": {
            "plain": "verdicts + strength_bars + timeline + uncertainty",
            "why": "claims (each with chart_condition, source, cancellations)",
            "tables": "the full ChartV1 JSON (astrologer view)",
        },
    }

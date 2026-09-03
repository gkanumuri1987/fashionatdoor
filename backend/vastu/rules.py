"""Deterministic Vastu Shastra evaluation — the rules layer.

Same architecture as jyotish/: the AI never judges placements. Vision extracts
the floor plan into {room type, 16-wind zone}; THIS module scores every room
against classical Vastu placement rules; the AI only narrates the computed
findings.

Zones: the 16 compass sectors (N, NNE, NE, ENE, E, ESE, SE, SSE, S, SSW, SW,
WSW, W, WNW, NW, NNW) + "center" (brahmasthan).

Rule sources: classical Vastu placement tradition (Brihat Samhita ch. 53,
Mayamata, Samarangana Sutradhara) — freshly stated, no copied text. Entrance
padas follow the 32-pada scheme: the auspicious entries are Mukhya/Bhallat/
Soma (north face) and Jayanta/Indra/Mahendra (east face) — approximated at
zone level (N/NNE and E/ENE) since a photo rarely resolves exact padas.
"""

from __future__ import annotations

ZONES = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
         "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]

# room type -> {zone: verdict}. Zones not listed = "neutral".
# Verdicts: excellent | good | neutral | avoid | grave
_RULES: dict[str, dict[str, str]] = {
    "entrance": {"N": "excellent", "NNE": "good", "NE": "good", "E": "excellent",
                 "ENE": "good", "W": "neutral", "NW": "neutral",
                 "S": "avoid", "SSW": "grave", "SW": "grave", "WSW": "avoid",
                 "SE": "avoid", "SSE": "avoid"},
    "kitchen": {"SE": "excellent", "NW": "good", "S": "neutral", "E": "neutral",
                "NE": "grave", "SW": "avoid", "N": "avoid", "center": "grave"},
    "master_bedroom": {"SW": "excellent", "S": "good", "W": "good",
                       "NE": "avoid", "SE": "avoid", "center": "avoid"},
    "bedroom": {"SW": "good", "S": "good", "W": "good", "NW": "good",
                "NE": "avoid", "SE": "neutral", "center": "avoid"},
    "pooja": {"NE": "excellent", "E": "good", "N": "good",
              "S": "avoid", "SW": "avoid", "center": "good"},
    "toilet": {"NW": "good", "WNW": "good", "W": "neutral", "WSW": "neutral",
               "NE": "grave", "SW": "avoid", "E": "avoid", "N": "avoid",
               "center": "grave"},
    "bathroom": {"NW": "good", "E": "good", "N": "neutral",
                 "NE": "avoid", "SW": "avoid", "center": "grave"},
    "living": {"N": "good", "NE": "good", "E": "good", "NW": "neutral",
               "center": "good"},
    "dining": {"W": "good", "E": "good", "S": "neutral"},
    "study": {"NE": "excellent", "N": "good", "E": "good", "W": "good",
              "SW": "neutral"},
    "store": {"SW": "good", "WSW": "good", "NW": "neutral", "NE": "avoid"},
    "staircase": {"S": "good", "SW": "good", "W": "good",
                  "NE": "grave", "center": "grave"},
    "water_tank": {"NE": "excellent", "N": "good", "E": "good",
                   "SW": "avoid", "SE": "avoid"},
    "balcony": {"N": "good", "NE": "good", "E": "good"},
    "garage": {"NW": "good", "SE": "neutral", "NE": "avoid"},
}

# Non-structural (soft) remedies per problem type — honest: a grave structural
# placement is acknowledged as structural; soft measures only mitigate.
_SOFT_REMEDIES: dict[str, str] = {
    "kitchen": "If relocation is impossible, shift the cooking flame to the "
               "south-east corner of the kitchen itself and face east while cooking.",
    "toilet": "Keep the door closed, ventilate well, and place a small bowl of "
              "sea salt inside (replaced weekly) — a mitigation, not a cure.",
    "master_bedroom": "Sleep with the head toward south or east; move heavier "
                      "furniture to the room's south-west.",
    "entrance": "Keep the entry brightly lit and unobstructed; a threshold "
                "(dehleez) and auspicious torana over the door strengthen a weak entry.",
    "staircase": "Keep the space under the stairs open and light — never a "
                 "pooja or store for valuables.",
    "pooja": "Relocate the altar itself to the home's north-east corner of "
             "whichever room is available — the altar's own placement matters most.",
    "water_tank": "An underground source in the south is best compensated by "
                  "keeping the north-east light, open and clutter-free.",
}

_VERDICT_SCORE = {"excellent": 2, "good": 1, "neutral": 0, "avoid": -1, "grave": -2}


def evaluate(rooms: list[dict]) -> dict:
    """rooms: [{"label": str, "type": str, "zone": str}] with zone in ZONES or
    'center'. Returns per-room findings + overall score + brahmasthan check."""
    findings = []
    score = 0
    brahmasthan_blocked = None
    for r in rooms:
        rtype = (r.get("type") or "").strip().lower()
        zone = (r.get("zone") or "").strip()
        rules = _RULES.get(rtype)
        if not rules or (zone not in ZONES and zone != "center"):
            findings.append({**r, "verdict": "unknown",
                             "note": "Room type or zone not recognised — skipped."})
            continue
        verdict = rules.get(zone, "neutral")
        score += _VERDICT_SCORE[verdict]
        entry = {**r, "verdict": verdict}
        if verdict in ("avoid", "grave"):
            entry["classical_position"] = _ideal_zones(rtype)
            soft = _SOFT_REMEDIES.get(rtype)
            if soft:
                entry["soft_remedy"] = soft
        if zone == "center" and verdict in ("avoid", "grave"):
            brahmasthan_blocked = rtype
        findings.append(entry)

    max_possible = 2 * max(1, len([f for f in findings if f["verdict"] != "unknown"]))
    return {
        "schema": "VastuV1",
        "findings": findings,
        "score": score,
        "score_out_of": max_possible,
        "brahmasthan": {
            "blocked_by": brahmasthan_blocked,
            "note": ("The brahmasthan (centre) is occupied by a heavy function — "
                     "the gravest classical objection; keep the centre open and light."
                     if brahmasthan_blocked else
                     "Centre appears open or lightly used — favourable."),
        },
        "disclaimer": "Vastu guidance is offered for reflection and harmony of "
                      "living space — structural decisions deserve a qualified "
                      "consultant's site visit.",
    }


def _ideal_zones(rtype: str) -> list[str]:
    rules = _RULES.get(rtype, {})
    return [z for z, v in rules.items() if v in ("excellent", "good")]

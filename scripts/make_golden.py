#!/usr/bin/env python
"""Generate golden regression snapshots for the deterministic Jyotish engine.

Writes backend/tests/golden/charts.json — a REDUCED, deterministic subset of
compute_chart() output for ~20 diverse births (edge cases from the audit list:
pre-1900 LMT, wartime DST, DST-gap nonexistent local time, southern hemisphere,
high latitude, equator, non-half-hour offsets, sign-boundary lagna, ...).

The snapshots deliberately EXCLUDE current_dasha and every other now-dependent
field, so the file is a pure function of (birth instant, place, engine code).

Run with the backend venv:

    backend/.venv/bin/python scripts/make_golden.py

A case that CRASHES the engine is recorded as {"error": "Type: message"} —
the test suite then asserts the same failure mode persists (documented
behavior), rather than skipping it.
"""

from __future__ import annotations

import json
import sys
from datetime import date, time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND = REPO_ROOT / "backend"
OUT_PATH = BACKEND / "tests" / "golden" / "charts.json"

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

HEADER_NOTE = (
    "ENGINE snapshots: self-consistent regression anchors pinned from "
    "jyotish.compute_chart(). Values were additionally spot-verified by eye "
    "against Jagannatha Hora at generation time. Any change to these values "
    "requires bumping jyotish.ENGINE_VERSION and deliberately regenerating "
    "this file via scripts/make_golden.py — never hand-editing it."
)

# id, date, time, tz, lat, lng, place label
CASES: list[tuple[str, str, str, str, float, float, str]] = [
    # ── audit edge list ──────────────────────────────────────────────────
    ("hyderabad_1990", "1990-05-15", "10:30", "Asia/Kolkata", 17.385, 78.4867,
     "Hyderabad, India"),
    ("pre1900_porbandar", "1869-10-02", "07:12", "Asia/Kolkata", 21.6417, 69.6293,
     "Porbandar, India (pre-1900, LMT era)"),
    ("wartime_dst_calcutta", "1943-06-01", "04:30", "Asia/Kolkata", 22.5726, 88.3639,
     "Calcutta, India (WWII +6:30 war time)"),
    ("midnight_delhi", "2000-01-01", "00:00", "Asia/Kolkata", 28.6139, 77.209,
     "Delhi, India (midnight boundary)"),
    ("us_dst_transition", "2020-03-08", "02:59", "America/New_York", 40.7128, -74.006,
     "New York, USA (nonexistent local time in DST spring-forward gap; "
     "snapshot pins whatever the geo layer deterministically resolves)"),
    ("southern_hemisphere", "1985-12-25", "15:45", "Australia/Sydney", -33.8688, 151.2093,
     "Sydney, Australia (southern hemisphere, DST)"),
    ("high_latitude", "1995-06-21", "12:00", "Europe/Oslo", 69.6492, 18.9553,
     "Tromsø, Norway (69.6°N midnight sun — Placidus degenerate)"),
    ("kathmandu_offset", "1988-04-14", "06:15", "Asia/Kathmandu", 27.7172, 85.324,
     "Kathmandu, Nepal (+05:45 offset)"),
    ("sign_boundary_lagna", "1990-05-15", "10:54", "Asia/Kolkata", 17.385, 78.4867,
     "Hyderabad, India (lagna near Cancer/Leo boundary)"),
    ("equator_singapore", "1975-08-09", "18:30", "Asia/Singapore", 1.3521, 103.8198,
     "Singapore (equator; historical +07:30 offset era)"),
    # ── 10 more across decades 1950-2020, different continents ───────────
    ("london_1951", "1951-02-06", "23:45", "Europe/London", 51.5074, -0.1278,
     "London, UK (late-night birth)"),
    ("moscow_1957", "1957-10-04", "22:28", "Europe/Moscow", 55.7558, 37.6173,
     "Moscow, USSR (Sputnik launch evening)"),
    ("lagos_1960", "1960-10-01", "09:00", "Africa/Lagos", 6.5244, 3.3792,
     "Lagos, Nigeria (near-equatorial West Africa)"),
    ("tokyo_1964", "1964-10-10", "14:00", "Asia/Tokyo", 35.6762, 139.6503,
     "Tokyo, Japan"),
    ("sao_paulo_1970", "1970-06-21", "03:20", "America/Sao_Paulo", -23.5505, -46.6333,
     "São Paulo, Brazil (southern winter solstice, pre-dawn)"),
    ("mexico_city_1985", "1985-09-19", "07:17", "America/Mexico_City", 19.4326, -99.1332,
     "Mexico City, Mexico"),
    ("cape_town_1994", "1994-04-27", "08:00", "Africa/Johannesburg", -33.9249, 18.4241,
     "Cape Town, South Africa"),
    ("leap_day_auckland", "2004-02-29", "16:20", "Pacific/Auckland", -36.8485, 174.7633,
     "Auckland, New Zealand (leap day, NZDT)"),
    ("honolulu_2011", "2011-08-04", "13:37", "Pacific/Honolulu", 21.3069, -157.8583,
     "Honolulu, USA (UTC-10, no DST)"),
    ("chennai_2015", "2015-11-14", "21:05", "Asia/Kolkata", 13.0827, 80.2707,
     "Chennai, India (night birth)"),
]

GRAHA_KEYS = ("sun", "moon", "mars", "mercury", "jupiter", "venus",
              "saturn", "rahu", "ketu")


def _round_floats(obj, ndigits: int = 6):
    """Recursively round every float to `ndigits` dp (JSON-native types only)."""
    if isinstance(obj, float):
        return round(obj, ndigits)
    if isinstance(obj, dict):
        return {k: _round_floats(v, ndigits) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_round_floats(v, ndigits) for v in obj]
    return obj


def reduce_chart(chart: dict) -> dict:
    """Deterministic REDUCED snapshot of a ChartV1 dict.

    Excludes current_dasha and every now-dependent field. This function is the
    single source of truth for what the golden tests compare — the test suite
    imports it from this script.
    """
    grahas = {}
    for g in GRAHA_KEYS:
        gd = chart["grahas"][g]
        grahas[g] = {
            "lon": gd["lon"],
            "sign": gd["sign"],
            "house": gd["house"],
            "retrograde": gd["retrograde"],
            "combust": gd["combust"],
            "dignity": gd["dignity"],
            "nakshatra": {"index": gd["nakshatra"]["index"],
                          "pada": gd["nakshatra"]["pada"]},
            "vargas": dict(gd["vargas"]),
        }

    pan = chart["panchanga"]
    vim = chart["vimshottari"]
    jai = chart["jaimini"]
    kp = chart.get("kp")
    chalita = chart.get("bhava_chalita")

    snap = {
        "input": {
            "utc": chart["input"]["utc"],
            "utc_offset_hours": chart["input"]["utc_offset_hours"],
        },
        "ayanamsa_value": chart["ayanamsa_value"],
        "lagna_lon": chart["lagna"]["lon"],
        "mc": chart["mc"],
        "grahas": grahas,
        "panchanga": {
            "tithi": pan["tithi"]["name"],
            "vara": pan["vara"]["name"],
            "yoga": pan["yoga"]["name"],
            "karana": pan["karana"]["name"],
        },
        "vimshottari": {
            "balance_at_birth_years": vim["balance_at_birth_years"],
            "first_mahadashas": [
                {"lord": md["lord"], "start": md["start"], "end": md["end"]}
                for md in vim["mahadashas"][:3]
            ],
        },
        "yoga_keys": sorted(y["key"] for y in chart["yogas"]),
        "shadbala_rupas": {g: sb["rupas"]
                           for g, sb in chart["shadbala_summary"].items()},
        "ashtakavarga_sarva": list(chart["ashtakavarga"]["sarva"]),
        "jaimini": {
            "chara_karakas": {
                k: {"graha": v["graha"], "deg_in_sign": v["deg_in_sign"]}
                for k, v in jai["chara_karakas"]["karakas"].items()
            },
            "arudha_AL": jai["arudha_padas"]["AL"],
            "arudha_UL": jai["arudha_padas"]["UL"],
            "karakamsa_sign": jai["karakamsa"]["sign"],
        },
        "kp_planets": ({
            g: {"star": kp["planets"][g]["star_lord"],
                "sub": kp["planets"][g]["sub_lord"],
                "sub_sub": kp["planets"][g]["sub_sub_lord"]}
            for g in GRAHA_KEYS
        } if kp else None),
        "bhava_chalita_houses": ({
            g: chalita["grahas"][g]["house"] for g in GRAHA_KEYS
        } if chalita else None),
    }
    return _round_floats(snap)


def build_case(case_id: str, d: str, t: str, tz: str, lat: float, lng: float,
               place: str) -> dict:
    from jyotish.chart import compute_chart

    entry = {
        "id": case_id,
        "place": place,
        "input": {"date": d, "time": t, "tz": tz, "lat": lat, "lng": lng},
    }
    y, mo, dy = (int(x) for x in d.split("-"))
    hh, mm = (int(x) for x in t.split(":"))
    try:
        chart = compute_chart(date(y, mo, dy), time(hh, mm), lat, lng, tz_name=tz)
    except Exception as exc:  # documented failure mode — pinned, not skipped
        entry["error"] = f"{type(exc).__name__}: {exc}"
        return entry
    entry["snapshot"] = reduce_chart(chart)
    return entry


def main() -> None:
    from jyotish import ENGINE_VERSION

    cases = []
    for spec in CASES:
        entry = build_case(*spec)
        status = f"ERROR ({entry['error']})" if "error" in entry else "ok"
        print(f"  {spec[0]:<24} {status}")
        cases.append(entry)

    doc = {
        "schema": "golden-charts-v1",
        "engine_version": ENGINE_VERSION,
        "note": HEADER_NOTE,
        "generated_by": "scripts/make_golden.py",
        "cases": cases,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
    ok = sum(1 for c in cases if "snapshot" in c)
    err = len(cases) - ok
    print(f"Wrote {OUT_PATH} — {len(cases)} cases ({ok} snapshots, "
          f"{err} pinned failure modes), engine {ENGINE_VERSION}")


if __name__ == "__main__":
    main()

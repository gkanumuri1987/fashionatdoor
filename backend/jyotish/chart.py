"""ChartV1 assembler — the canonical output of the deterministic engine.

compute_chart() is a PURE function of (birth instant, place, options): identical
inputs always produce identical output, which is why charts are cacheable on
(utc_instant, lat, lng, ayanamsa, house_system, node_type, engine_version).
"""

from __future__ import annotations

from datetime import date, datetime, time, timezone

from . import ENGINE_VERSION
from .constants import GRAHAS, GRAHA_NAMES, SIGNS, SIGN_LORD, SPECIAL_ASPECTS
from .dasha import current_period, vimshottari
from .dignity import combustion_flags, compound_relation, dignity_of
from .ephemeris import ayanamsa_value, houses, julian_day_ut, sidereal_positions
from .geo import to_utc
from .nakshatra import nakshatra_of
from .panchanga import panchanga
from .varga import all_vargas
from .yogas import detect_yogas

_SADE_SATI_PHASES = {12: "rising (first phase)", 1: "peak (second phase)", 2: "setting (third phase)"}


def _fmt_dms(lon: float) -> str:
    deg_in_sign = lon % 30
    d = int(deg_in_sign)
    m_f = (deg_in_sign - d) * 60
    m = int(m_f)
    s = int(round((m_f - m) * 60))
    if s == 60:
        s, m = 0, m + 1
    if m == 60:
        m, d = 0, d + 1
    return f"{d}°{m:02d}'{s:02d}\""


def _graha_aspects(grahas: dict[str, dict]) -> list[dict]:
    """Full sign-based drishti between grahas (7th for all; specials for Mars/Jup/Sat)."""
    out = []
    for g, gd in grahas.items():
        if g in ("rahu", "ketu"):
            continue  # nodal drishti is disputed; omitted by default
        houses_aspected = [7] + SPECIAL_ASPECTS.get(g, [])
        for other, od in grahas.items():
            if other == g:
                continue
            count = (od["sign"] - gd["sign"]) % 12 + 1
            if count in houses_aspected:
                out.append({"from": g, "to": other, "type": f"{count}th drishti"})
    return out


def compute_chart(birth_date: date, birth_time: time, lat: float, lng: float,
                  tz_name: str | None = None, ayanamsa: str = "lahiri",
                  house_system: str = "whole_sign", node_type: str = "true",
                  time_accuracy: str = "exact") -> dict:
    instant = to_utc(birth_date, birth_time, tz_name=tz_name, lat=lat, lng=lng)
    jd = julian_day_ut(instant.utc)

    positions = sidereal_positions(jd, ayanamsa=ayanamsa, true_node=(node_type == "true"))
    house_data = houses(jd, lat, lng, ayanamsa=ayanamsa, system=house_system)
    lagna_sign = int(house_data["ascendant"] // 30)
    combust = combustion_flags(positions)

    grahas: dict[str, dict] = {}
    for g in GRAHAS:
        lon = positions[g]["lon"]
        sign = int(lon // 30)
        entry = {
            "name": GRAHA_NAMES[g],
            "lon": round(lon, 6),
            "sign": sign,
            "sign_name": SIGNS[sign]["en"],
            "degree_in_sign": _fmt_dms(lon),
            "house": (sign - lagna_sign) % 12 + 1,
            "retrograde": positions[g]["retrograde"],
            "combust": combust[g],
            "dignity": dignity_of(g, lon),
            "nakshatra": nakshatra_of(lon),
            "vargas": all_vargas(lon),
        }
        grahas[g] = entry

    # Upgrade friend/enemy dignities to compound (needs all positions — the
    # temporal component counts from the graha's own sign to its sign lord's sign).
    for g, entry in grahas.items():
        if entry["dignity"] in ("friend", "neutral", "enemy"):
            lord = SIGN_LORD[entry["sign"]]
            if lord != g and lord in grahas:
                entry["dignity"] = compound_relation(g, lord, entry["sign"], grahas[lord]["sign"])

    dasha = vimshottari(positions["moon"]["lon"], jd)
    now_jd = julian_day_ut(datetime.now(timezone.utc))

    bhavas = []
    for h in range(1, 13):
        sign = (lagna_sign + h - 1) % 12
        bhavas.append({
            "house": h, "sign": sign, "sign_name": SIGNS[sign]["en"],
            "lord": SIGN_LORD[sign],
            "cusp": round(house_data["cusps"][h - 1], 6),
            "occupants": [g for g in GRAHAS if grahas[g]["house"] == h],
        })

    return {
        "schema": "ChartV1",
        "engine_version": ENGINE_VERSION,
        "input": {
            "date": birth_date.isoformat(), "time": birth_time.isoformat(),
            "lat": lat, "lng": lng, "tz": instant.tz_name,
            "utc": instant.utc.isoformat(),
            "utc_offset_hours": instant.utc_offset_hours,
            "time_accuracy": time_accuracy,
            "ayanamsa": ayanamsa, "house_system": house_system, "node_type": node_type,
        },
        "ayanamsa_value": round(ayanamsa_value(jd, ayanamsa), 6),
        "julian_day_ut": jd,
        "lagna": {
            "lon": round(house_data["ascendant"], 6),
            "sign": lagna_sign, "sign_name": SIGNS[lagna_sign]["en"],
            "degree_in_sign": _fmt_dms(house_data["ascendant"]),
            "nakshatra": nakshatra_of(house_data["ascendant"]),
            "lord": SIGN_LORD[lagna_sign],
        },
        "mc": round(house_data["mc"], 6),
        "grahas": grahas,
        "bhavas": bhavas,
        "aspects": _graha_aspects(grahas),
        "panchanga": panchanga(positions["sun"]["lon"], positions["moon"]["lon"], birth_date),
        "yogas": detect_yogas(grahas, lagna_sign),
        "vimshottari": dasha,
        "current_dasha": current_period(dasha, now_jd),
        "moon_sign": grahas["moon"]["sign"],
        "moon_sign_name": grahas["moon"]["sign_name"],
    }


def transit_report(chart: dict, as_of: datetime | None = None) -> dict:
    """Current sidereal transits relative to the natal chart (gochara + sade sati)."""
    as_of = as_of or datetime.now(timezone.utc)
    if as_of.tzinfo is None:
        as_of = as_of.replace(tzinfo=timezone.utc)
    jd = julian_day_ut(as_of)
    ay = chart["input"]["ayanamsa"]
    node_true = chart["input"]["node_type"] == "true"
    positions = sidereal_positions(jd, ayanamsa=ay, true_node=node_true)

    lagna_sign = chart["lagna"]["sign"]
    moon_sign = chart["moon_sign"]
    transits = {}
    for g in GRAHAS:
        lon = positions[g]["lon"]
        sign = int(lon // 30)
        transits[g] = {
            "lon": round(lon, 6), "sign": sign, "sign_name": SIGNS[sign]["en"],
            "retrograde": positions[g]["retrograde"],
            "house_from_lagna": (sign - lagna_sign) % 12 + 1,
            "house_from_moon": (sign - moon_sign) % 12 + 1,
            "nakshatra": nakshatra_of(lon)["name"],
        }

    sat_from_moon = transits["saturn"]["house_from_moon"]
    sade_sati = sat_from_moon in (12, 1, 2)
    return {
        "as_of": as_of.isoformat(),
        "transits": transits,
        "sade_sati": {
            "active": sade_sati,
            "phase": _SADE_SATI_PHASES.get(sat_from_moon) if sade_sati else None,
        },
    }

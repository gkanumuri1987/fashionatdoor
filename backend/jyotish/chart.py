"""ChartV1 assembler — the canonical output of the deterministic engine.

compute_chart() is a PURE function of (birth instant, place, options) EXCEPT
the convenience field ``current_dasha`` (evaluated at call time). Cache charts
on (utc_instant, lat, lng, ayanamsa, house_system, node_type, engine_version)
and re-derive current_dasha from ``vimshottari`` when serving a cached chart.
"""

from __future__ import annotations

from datetime import date, datetime, time, timezone

from . import ENGINE_VERSION
from .ashtakavarga import bhinnashtakavarga, sarvashtakavarga
from .avastha import avasthas_for, graha_yuddha
from .constants import GRAHAS, GRAHA_NAMES, SIGNS, SIGN_LORD, SPECIAL_ASPECTS
from .dasha import current_period, vimshottari
from .dignity import combustion_flags, compound_relation, dignity_of
from .ephemeris import (ayanamsa_value, houses, jd_to_utc, julian_day_ut,
                        sidereal_positions, sunrise_sunset)
from .bhava import bhava_chalita
from .geo import to_utc
from .jaimini import (arudha_padas, chara_dasha, chara_karakas, ishta_devata,
                      karakamsa)
from .kp import cusp_sublords, planet_significators, star_sub_subsub
from .lords import functional_nature
from .varga import d9
from .nakshatra import nakshatra_of
from .panchanga import panchanga
from .strength import ShadbalaInputs, ishta_kashta, shadbala
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
    ay_value = ayanamsa_value(jd, ayanamsa)

    # Sunrise/sunset — drives day/night balas AND the traditional vara
    # (a birth before sunrise belongs to the PREVIOUS vara).
    rise_jd, set_jd = sunrise_sunset(jd, lat, lng)
    from datetime import timedelta as _td
    vara_date = birth_date
    if rise_jd is not None and jd < rise_jd:
        vara_date = birth_date - _td(days=1)
    if rise_jd is not None and set_jd is not None:
        is_day_birth = rise_jd <= jd < set_jd
    else:  # polar fallback: local-solar-hour approximation
        local_frac = (jd + lng / 360.0 + 0.5) % 1.0
        is_day_birth = 0.25 <= local_frac < 0.75

    wars = graha_yuddha(positions)
    _lost_war = {w["loser"] for w in wars}

    # Functional nature per lagna (yogakaraka / maraka / badhaka — Rule: the
    # engine states these; the AI never derives them).
    fn = functional_nature(lagna_sign)

    # Shadbala (skipped only in polar no-sunrise conditions).
    sb: dict[str, dict] = {}
    if rise_jd is not None and set_jd is not None:
        sb = shadbala(ShadbalaInputs(
            positions=positions, lagna_lon=house_data["ascendant"], jd_ut=jd,
            lat=lat, lng=lng, sunrise_jd=rise_jd, sunset_jd=set_jd,
            is_day_birth=is_day_birth, weekday=vara_date.weekday(),
            ayanamsa_value=ay_value,
        ))

    bav = bhinnashtakavarga(
        {g: positions[g]["lon"] for g in
         ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn")},
        lagna_sign)
    sav = sarvashtakavarga(bav)

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
            "avasthas": avasthas_for(g, lon, combust[g], g in _lost_war),
        }
        if g in fn["per_graha"]:
            entry["functional"] = {
                "verdict": fn["per_graha"][g]["verdict"],
                "is_maraka": fn["per_graha"][g]["is_maraka"],
                "is_badhaka": fn["per_graha"][g]["is_badhaka"],
            }
        if g in sb:
            ik = ishta_kashta(sb[g]["sthana"]["uccha"], sb[g]["chesta"])
            entry["shadbala"] = {
                "total_rupas": sb[g]["total_rupas"],
                "required_rupas": sb[g]["required_rupas"],
                "ratio": sb[g]["ratio"],
                "is_strong": sb[g]["is_strong"],
                "ishta": round(ik[0], 2),
                "kashta": round(ik[1], 2),
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

    # ── Jaimini layer ────────────────────────────────────────────────────────
    graha_signs = {g: int(positions[g]["lon"] // 30) for g in GRAHAS}
    karakas = chara_karakas(positions)
    ak = karakas["karakas"]["AK"]["graha"]
    kamsa = karakamsa(ak, positions)
    d9_signs = {g: d9(positions[g]["lon"]) for g in GRAHAS}
    jaimini_block = {
        "chara_karakas": karakas,
        "arudha_padas": arudha_padas(lagna_sign, graha_signs),
        "karakamsa": kamsa,
        "ishta_devata": ishta_devata(kamsa["sign"], d9_signs),
        "chara_dasha": chara_dasha(lagna_sign, graha_signs, jd),
    }

    # ── Bhava chalita (degree-based membership; Sripati madhya) ──────────────
    try:
        sripati = houses(jd, lat, lng, ayanamsa=ayanamsa, system="sripati")
        chalita = bhava_chalita(sripati["cusps"], positions)
    except Exception:  # pragma: no cover — high-latitude degeneracy
        chalita = None

    # ── KP layer: star/sub/sub-sub per graha + Placidus cusp sublords ────────
    kp_block = None
    try:
        placidus = houses(jd, lat, lng, ayanamsa=ayanamsa, system="placidus")
        kp_block = {
            "note": "KP uses the Placidus cusps below regardless of the "
                    "chart's display house system; pair with ayanamsa='kp' "
                    "for strict Krishnamurti practice.",
            "planets": {g: star_sub_subsub(positions[g]["lon"]) for g in GRAHAS},
            "cusps": cusp_sublords(placidus["cusps"]),
            "significators": planet_significators(positions, placidus["cusps"]),
        }
    except Exception:  # pragma: no cover — polar Placidus degeneracy
        kp_block = None

    bhavas = []
    for h in range(1, 13):
        sign = (lagna_sign + h - 1) % 12
        bhavas.append({
            "house": h, "sign": sign, "sign_name": SIGNS[sign]["en"],
            "lord": SIGN_LORD[sign],
            "cusp": round(house_data["cusps"][h - 1], 6),
            "occupants": [g for g in GRAHAS if grahas[g]["house"] == h],
            "sav_bindus": sav[sign],
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
            "time_note": instant.time_note,
            "ayanamsa": ayanamsa, "house_system": house_system, "node_type": node_type,
        },
        "ayanamsa_value": round(ay_value, 6),
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
        "panchanga": panchanga(positions["sun"]["lon"], positions["moon"]["lon"],
                               birth_date, vara_date=vara_date),
        "yogas": _annotate_yoga_strength(detect_yogas(grahas, lagna_sign), sb),
        "vimshottari": dasha,
        "current_dasha": current_period(dasha, now_jd),
        "moon_sign": grahas["moon"]["sign"],
        "moon_sign_name": grahas["moon"]["sign_name"],
        "sunrise_utc": jd_to_utc(rise_jd).isoformat() if rise_jd else None,
        "sunset_utc": jd_to_utc(set_jd).isoformat() if set_jd else None,
        "is_day_birth": is_day_birth,
        "functional_lords": fn,
        "shadbala": sb,
        "shadbala_summary": {
            g: {"rupas": sb[g]["total_rupas"], "required": sb[g]["required_rupas"],
                "is_strong": sb[g]["is_strong"]}
            for g in sb
        },
        "ashtakavarga": {"bhinna": bav, "sarva": sav, "sarva_total": sum(sav)},
        "graha_yuddha": wars,
        "jaimini": jaimini_block,
        "bhava_chalita": chalita,
        "kp": kp_block,
        "lagna_sensitivity": _lagna_sensitivity(jd, lat, lng, ayanamsa, time_accuracy),
        # Unknown birth time → the Chandra-lagna view (houses from the Moon)
        # is the honest fallback; the flag tells the AI layer to judge from it.
        "use_chandra_lagna": time_accuracy == "unknown",
    }


def _lagna_sensitivity(jd: float, lat: float, lng: float, ayanamsa: str,
                       time_accuracy: str) -> dict | None:
    """Rectification honesty for inexact birth times: how far the lagna moves
    across the stated uncertainty band (±30 min approximate, ±3 h unknown).
    If the lagna sign CHANGES inside the band, every lagna-dependent result
    (houses, functional lords, dasha flavour) is uncertain — the report says
    exactly that instead of pretending precision."""
    if time_accuracy == "exact":
        return None
    band_min = 30 if time_accuracy == "approximate" else 180
    offsets = (-band_min, 0, band_min)
    signs = []
    for m in offsets:
        try:
            h = houses(jd + m / 1440.0, lat, lng, ayanamsa=ayanamsa, system="whole_sign")
            signs.append(int(h["ascendant"] // 30))
        except Exception:  # pragma: no cover
            return None
    stable = len(set(signs)) == 1
    return {
        "band_minutes": band_min,
        "lagna_signs_across_band": [SIGNS[s]["en"] for s in signs],
        "stable": stable,
        "note": ("Lagna holds the same sign across the uncertainty band — "
                 "house-based results are dependable despite the inexact time."
                 if stable else
                 "Lagna CHANGES sign within the uncertainty band — treat "
                 "house-based results as tentative; Moon-based results are firm."),
    }


def _annotate_yoga_strength(yogas: list[dict], sb: dict[str, dict]) -> list[dict]:
    """A yoga on strong grahas is a different statement from the same yoga on
    weak ones — attach the mean Shadbala ratio of the participants."""
    for y in yogas:
        parts = [g for g in y.get("grahas", []) if g in sb]
        if parts:
            avg = sum(sb[g]["ratio"] for g in parts) / len(parts)
            y["strength_ratio"] = round(avg, 3)
            y["strong"] = avg >= 1.0
    return yogas


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
        entry = {
            "lon": round(lon, 6), "sign": sign, "sign_name": SIGNS[sign]["en"],
            "retrograde": positions[g]["retrograde"],
            "house_from_lagna": (sign - lagna_sign) % 12 + 1,
            "house_from_moon": (sign - moon_sign) % 12 + 1,
            "nakshatra": nakshatra_of(lon)["name"],
        }
        sav_natal = (chart.get("ashtakavarga") or {}).get("sarva")
        if sav_natal:
            # Classical gochara judgment: a transit over a high-bindu sign
            # supports; over a low-bindu sign strains (SAV mean = 28).
            entry["sav_bindus"] = sav_natal[sign]
        transits[g] = entry

    sat_from_moon = transits["saturn"]["house_from_moon"]
    sade_sati = sat_from_moon in (12, 1, 2)

    # Tarabala: count today's Moon nakshatra from the NATAL Moon nakshatra
    # (janma tara), folded 1-9. Favourable: Sampat(2), Kshema(4), Sadhaka(6),
    # Mitra(8), Ati-mitra(9). Unfavourable: Vipat(3), Pratyari(5), Vadha(7).
    natal_nak = nakshatra_of(chart["grahas"]["moon"]["lon"])["index"]
    today_nak = nakshatra_of(positions["moon"]["lon"])["index"]
    tara_count = (today_nak - natal_nak) % 27 % 9 + 1
    tara_names = ["Janma", "Sampat", "Vipat", "Kshema", "Pratyari",
                  "Sadhaka", "Vadha", "Mitra", "Ati-mitra"]
    # Chandrabala: today's Moon sign counted from the natal Moon sign;
    # favourable at 1, 3, 6, 7, 10, 11.
    chandra_count = transits["moon"]["house_from_moon"]

    return {
        "as_of": as_of.isoformat(),
        "transits": transits,
        "sade_sati": {
            "active": sade_sati,
            "phase": _SADE_SATI_PHASES.get(sat_from_moon) if sade_sati else None,
        },
        "shani_flags": {
            "ashtama_shani": sat_from_moon == 8,
            "kantaka_shani": sat_from_moon in (4, 7, 10),
        },
        "tarabala": {
            "count": tara_count,
            "name": tara_names[tara_count - 1],
            "favourable": tara_count in (2, 4, 6, 8, 9),
        },
        "chandrabala": {
            "count": chandra_count,
            "favourable": chandra_count in (1, 3, 6, 7, 10, 11),
        },
        "jupiter_from_moon": transits["jupiter"]["house_from_moon"],
    }

"""Western/tropical astrology layer — tropical zodiac, major aspects, profections.

The ephemeris adapter exposes SIDEREAL longitudes only (the whole Jyotish engine
is sidereal). The tropical zodiac differs from the sidereal one by exactly the
ayanamsa at the instant, so every tropical longitude here is derived as:

    tropical = (sidereal + ayanamsa_value(jd)) % 360

This is an identity, not an approximation: sidereal = tropical - ayanamsa by
definition, so adding the SAME ayanamsa back (any named ayanamsa, as long as
positions and ayanamsa use the same one — we use the module default, Lahiri)
recovers the tropical longitude exactly. The same shift applies to house cusps,
ascendant and MC returned by ephemeris.houses(), which are sidereal for the
same reason — one consistent rotation of the whole frame.

Western naming: Rahu/Ketu are reported as "north_node"/"south_node".
Signs are tropical, 0 = Aries (constants.SIGNS supplies the English names;
constants.SIGN_LORD doubles as the TRADITIONAL rulership table used for the
profection year lord — Mars Aries/Scorpio, Venus Taurus/Libra, Mercury
Gemini/Virgo, Moon Cancer, Sun Leo, Jupiter Sagittarius/Pisces, Saturn
Capricorn/Aquarius — no modern rulers).
"""

from __future__ import annotations

from datetime import date, datetime, time, timezone

from .constants import SIGNS, SIGN_LORD
from .ephemeris import (ayanamsa_value, houses, julian_day_ut,
                        sidereal_positions)
from .geo import to_utc

# Rahu/Ketu → western node labels.
_NODE_LABELS = {"rahu": "north_node", "ketu": "south_node"}

# Major (Ptolemaic) aspects: name -> (exact angle, base orb in degrees).
MAJOR_ASPECTS = [
    ("conjunction", 0.0, 8.0),
    ("sextile", 60.0, 4.0),
    ("square", 90.0, 7.0),
    ("trine", 120.0, 7.0),
    ("opposition", 180.0, 8.0),
]
_LUMINARIES = ("sun", "moon")
_LUMINARY_ORB_BONUS = 2.0  # aspects involving Sun or Moon get a wider orb

_TRANSIT_ORB = 3.0  # "exact-ish" orb for transit-to-natal contacts

_DAYS_PER_YEAR = 365.25


def _fmt_dms(lon: float) -> str:
    """Degree-in-sign as D°MM'SS" (local copy of the chart.py formatter)."""
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


def tropical_positions(jd_ut: float) -> dict[str, dict]:
    """Tropical longitudes for Sun..Saturn + the lunar nodes.

    Returns {planet: {"lon": tropical deg, "speed": deg/day, "retrograde": bool}}
    with the nodes labelled "north_node"/"south_node". Derived from the sidereal
    ephemeris via tropical = (sidereal + ayanamsa) % 360 (see module docstring);
    speed is frame-independent (the ayanamsa drifts ~50"/year — negligible
    against planetary daily motion, and both zodiacs quote the same speeds).
    """
    sid = sidereal_positions(jd_ut)
    ay = ayanamsa_value(jd_ut)
    out: dict[str, dict] = {}
    for name, data in sid.items():
        out[_NODE_LABELS.get(name, name)] = {
            "lon": (data["lon"] + ay) % 360.0,
            "speed": data["speed"],
            "retrograde": data["retrograde"],
        }
    return out


def _separation(lon_a: float, lon_b: float) -> float:
    """Angular distance in [0, 180]."""
    diff = abs(lon_a - lon_b) % 360.0
    return 360.0 - diff if diff > 180.0 else diff


def western_aspects(positions: dict[str, dict]) -> list[dict]:
    """Major aspects between all pairs, with standard orbs.

    Orbs: conjunction/opposition 8°, trine/square 7°, sextile 4°; a pair
    involving a luminary (Sun/Moon) gets +2°. Each entry:
    {a, b, aspect, angle, orb (deviation from exact), applying (bool)}.

    Applying = the separation is currently moving TOWARD the exact angle,
    judged from the relative speed (the faster body closing the arc); an
    exact aspect (orb 0) is reported as not applying.
    """
    names = list(positions)
    out: list[dict] = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            pa, pb = positions[a], positions[b]
            sep = _separation(pa["lon"], pb["lon"])
            bonus = _LUMINARY_ORB_BONUS if (a in _LUMINARIES or b in _LUMINARIES) else 0.0
            best = None
            for aspect, angle, base_orb in MAJOR_ASPECTS:
                delta = abs(sep - angle)
                if delta <= base_orb + bonus and (best is None or delta < best[2]):
                    best = (aspect, angle, delta)
            if best is None:
                continue
            aspect, angle, delta = best
            # d(sep)/dt from relative speed: sep = raw if raw<180 else 360-raw.
            raw = (pa["lon"] - pb["lon"]) % 360.0
            rel = pa["speed"] - pb["speed"]
            sep_rate = rel if raw < 180.0 else -rel
            applying = (sep < angle and sep_rate > 0) or (sep > angle and sep_rate < 0)
            out.append({
                "a": a, "b": b, "aspect": aspect, "angle": angle,
                "orb": round(delta, 4), "applying": applying,
            })
    return out


def annual_profection(age: int, asc_sign: int) -> dict:
    """Hellenistic annual profection for a completed age in years.

    Age 0 (first year of life) profects to house 1 / the ascendant sign; each
    birthday advances one house/sign. Year lord = the TRADITIONAL ruler of the
    profected sign (constants.SIGN_LORD is exactly that table).
    """
    profected_sign = (asc_sign + age) % 12
    return {
        "age": age,
        "profected_house": (age % 12) + 1,
        "profected_sign": profected_sign,
        "profected_sign_name": SIGNS[profected_sign]["en"],
        "year_ruler": SIGN_LORD[profected_sign],
    }


def _house_of(lon: float, cusps: list[float]) -> int:
    """House (1-12) by cusp spans, wrap-aware: house i spans cusp i → cusp i+1."""
    for i in range(12):
        start = cusps[i]
        span = (cusps[(i + 1) % 12] - start) % 360.0
        if (lon - start) % 360.0 < span:
            return i + 1
    return 12  # unreachable for sane cusps; degenerate-span guard


def _tropical_houses(jd: float, lat: float, lng: float, ay: float,
                     house_system: str) -> dict:
    """Tropical asc/mc/cusps from the sidereal ephemeris.houses() output.

    ephemeris.houses() returns SIDEREAL cusps; the tropical frame is the same
    circle rotated by the ayanamsa, so tropical cusp = (sidereal + ay) % 360 —
    applied identically to ascendant, MC and every cusp so the whole set stays
    mutually consistent. Exception: whole_sign cusps must sit on TROPICAL sign
    boundaries, so they are rebuilt from the tropical ascendant's sign (the
    sidereal sign boundaries + ayanamsa would land mid-sign).
    """
    hd = houses(jd, lat, lng, system=house_system)
    asc = (hd["ascendant"] + ay) % 360.0
    mc = (hd["mc"] + ay) % 360.0
    if house_system == "whole_sign":
        cusps = [((int(asc // 30) + i) % 12) * 30.0 for i in range(12)]
    else:
        cusps = [(c + ay) % 360.0 for c in hd["cusps"]]
    return {"ascendant": asc, "mc": mc, "cusps": cusps, "system": hd["system"]}


def western_chart(birth_date: date, birth_time: time, lat: float, lng: float,
                  tz_name: str | None = None,
                  house_system: str = "placidus") -> dict:
    """Full tropical natal chart + annual profection + current transits."""
    instant = to_utc(birth_date, birth_time, tz_name=tz_name, lat=lat, lng=lng)
    jd = julian_day_ut(instant.utc)
    ay = ayanamsa_value(jd)

    positions = tropical_positions(jd)
    house_data = _tropical_houses(jd, lat, lng, ay, house_system)
    cusps = house_data["cusps"]
    asc_sign = int(house_data["ascendant"] // 30)

    planets: dict[str, dict] = {}
    for name, p in positions.items():
        sign = int(p["lon"] // 30)
        planets[name] = {
            "lon": round(p["lon"], 6),
            "speed": p["speed"],
            "sign": sign,
            "sign_name": SIGNS[sign]["en"],
            "degree_in_sign": _fmt_dms(p["lon"]),
            "house": _house_of(p["lon"], cusps),
            "retrograde": p["retrograde"],
        }

    # ── Annual profection (age in completed years, 365.25-day years) ─────────
    now = datetime.now(timezone.utc)
    now_jd = julian_day_ut(now)
    age = max(0, int((now_jd - jd) / _DAYS_PER_YEAR))
    profection = annual_profection(age, asc_sign)

    # ── Current transits: tropical positions now, located in NATAL houses,
    #    with exact-ish (orb ≤ 3°) contacts to natal planets ─────────────────
    transit_pos = tropical_positions(now_jd)
    transits: dict[str, dict] = {}
    for name, p in transit_pos.items():
        sign = int(p["lon"] // 30)
        contacts = []
        for natal_name, natal in positions.items():
            sep = _separation(p["lon"], natal["lon"])
            for aspect, angle, _orb in MAJOR_ASPECTS:
                delta = abs(sep - angle)
                if delta <= _TRANSIT_ORB:
                    contacts.append({"natal": natal_name, "aspect": aspect,
                                     "angle": angle, "orb": round(delta, 4)})
        transits[name] = {
            "lon": round(p["lon"], 6),
            "sign": sign,
            "sign_name": SIGNS[sign]["en"],
            "degree_in_sign": _fmt_dms(p["lon"]),
            "natal_house": _house_of(p["lon"], cusps),
            "retrograde": p["retrograde"],
            "aspects_to_natal": contacts,
        }

    return {
        "schema": "WesternV1",
        "zodiac": "tropical",
        "input": {
            "date": birth_date.isoformat(), "time": birth_time.isoformat(),
            "lat": lat, "lng": lng, "tz": instant.tz_name,
            "utc": instant.utc.isoformat(),
            "utc_offset_hours": instant.utc_offset_hours,
            "house_system": house_system,
        },
        "julian_day_ut": jd,
        "ayanamsa_value": round(ay, 6),
        "ascendant": {
            "lon": round(house_data["ascendant"], 6),
            "sign": asc_sign,
            "sign_name": SIGNS[asc_sign]["en"],
            "degree_in_sign": _fmt_dms(house_data["ascendant"]),
        },
        "mc": round(house_data["mc"], 6),
        "houses": {
            "system": house_data["system"],
            "cusps": [round(c, 6) for c in cusps],
        },
        "planets": planets,
        "aspects": western_aspects(positions),
        "profection": profection,
        "transits": {"as_of": now.isoformat(), "planets": transits},
    }

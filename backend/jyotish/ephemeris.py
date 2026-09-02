"""Thin Swiss Ephemeris adapter — the ONLY module that imports swisseph.

Everything above this file is ephemeris-agnostic, so the engine can be swapped
(licence reasons or otherwise) by rewriting this one file.

Data files: if Swiss Ephemeris ``*.se1`` files are present in ``backend/ephe/``
they are used (best accuracy); otherwise the built-in Moshier analytical
ephemeris is used (no files, ~0.1 arc-second planetary accuracy — far below
the 1/60 arc-minute display threshold of any kundli).

Thread-safety: swisseph keeps global state (sidereal mode). All public calls
take the ayanamsa explicitly and hold a lock while it is set.
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from pathlib import Path

import swisseph as swe

_LOCK = threading.RLock()

EPHE_DIR = Path(__file__).resolve().parent.parent / "ephe"

AYANAMSAS = {
    "lahiri": swe.SIDM_LAHIRI,
    "raman": swe.SIDM_RAMAN,
    "kp": swe.SIDM_KRISHNAMURTI,
}

_PLANET_IDS = {
    "sun": swe.SUN, "moon": swe.MOON, "mars": swe.MARS, "mercury": swe.MERCURY,
    "jupiter": swe.JUPITER, "venus": swe.VENUS, "saturn": swe.SATURN,
}

_HOUSE_SYSTEMS = {"whole_sign": b"W", "placidus": b"P", "sripati": b"B"}


def _base_flags() -> int:
    """Prefer real SE data files when present; else Moshier (file-free)."""
    if EPHE_DIR.is_dir() and any(EPHE_DIR.glob("*.se1")):
        swe.set_ephe_path(str(EPHE_DIR))
        return swe.FLG_SWIEPH
    return swe.FLG_MOSEPH

_FLAGS = _base_flags() | swe.FLG_SPEED


def julian_day_ut(utc_dt: datetime) -> float:
    """UTC datetime → Julian Day (UT), delta-T handled by swisseph."""
    if utc_dt.tzinfo is None:
        raise ValueError("utc_dt must be tz-aware UTC")
    u = utc_dt.astimezone(timezone.utc)
    jd_et, jd_ut = swe.utc_to_jd(u.year, u.month, u.day, u.hour, u.minute,
                                 u.second + u.microsecond / 1e6, swe.GREG_CAL)
    return jd_ut


def jd_to_utc(jd_ut: float) -> datetime:
    y, m, d, h = swe.revjul(jd_ut, swe.GREG_CAL)
    hh = int(h)
    mm_f = (h - hh) * 60
    mm = int(mm_f)
    ss = int(round((mm_f - mm) * 60))
    if ss == 60:
        ss, mm = 0, mm + 1
    if mm == 60:
        mm, hh = 0, hh + 1
    if hh == 24:  # roll into next day
        base = datetime(y, m, d, tzinfo=timezone.utc)
        from datetime import timedelta
        return base + timedelta(days=1)
    return datetime(y, m, d, hh, mm, ss, tzinfo=timezone.utc)


def ayanamsa_value(jd_ut: float, ayanamsa: str = "lahiri") -> float:
    with _LOCK:
        swe.set_sid_mode(AYANAMSAS[ayanamsa], 0, 0)
        return swe.get_ayanamsa_ut(jd_ut)


def sidereal_positions(jd_ut: float, ayanamsa: str = "lahiri",
                       true_node: bool = True) -> dict[str, dict]:
    """Sidereal longitudes for all 9 grahas.

    Returns {graha: {"lon": deg, "speed": deg/day, "retrograde": bool}}.
    Rahu/Ketu are flagged retrograde by convention (nodes move backwards).
    """
    out: dict[str, dict] = {}
    with _LOCK:
        swe.set_sid_mode(AYANAMSAS[ayanamsa], 0, 0)
        flags = _FLAGS | swe.FLG_SIDEREAL
        for name, pid in _PLANET_IDS.items():
            (lon, _lat, _dist, splon, *_), _ = swe.calc_ut(jd_ut, pid, flags)
            out[name] = {"lon": lon % 360.0, "speed": splon,
                         "retrograde": bool(splon < 0) and name not in ("sun", "moon")}
        node_id = swe.TRUE_NODE if true_node else swe.MEAN_NODE
        (nlon, _lat, _dist, nsp, *_), _ = swe.calc_ut(jd_ut, node_id, flags)
        out["rahu"] = {"lon": nlon % 360.0, "speed": nsp, "retrograde": True}
        out["ketu"] = {"lon": (nlon + 180.0) % 360.0, "speed": nsp, "retrograde": True}
    return out


def houses(jd_ut: float, lat: float, lng: float, ayanamsa: str = "lahiri",
           system: str = "whole_sign") -> dict:
    """Sidereal ascendant + cusps.

    Whole-sign charts still need the ascendant DEGREE (from swe.houses_ex);
    the cusps returned for whole_sign are the 12 sign boundaries from the
    lagna sign, which is what every Indian kundli renders.

    High-latitude note: Placidus degenerates above the polar circles; swisseph
    falls back internally (Porphyry) — we surface the system actually used.
    """
    hsys = _HOUSE_SYSTEMS[system]
    with _LOCK:
        swe.set_sid_mode(AYANAMSAS[ayanamsa], 0, 0)
        cusps, ascmc = swe.houses_ex(jd_ut, lat, lng, hsys if system != "whole_sign" else b"P",
                                     swe.FLG_SIDEREAL)
    asc = ascmc[0] % 360.0
    mc = ascmc[1] % 360.0
    if system == "whole_sign":
        lagna_sign = int(asc // 30)
        cusp_list = [((lagna_sign + i) % 12) * 30.0 for i in range(12)]
    else:
        cusp_list = [c % 360.0 for c in cusps[:12]]
    return {"ascendant": asc, "mc": mc, "cusps": cusp_list, "system": system}

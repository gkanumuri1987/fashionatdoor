"""Panchanga EVENT finding — the instant a tithi/nakshatra/yoga/karana ends,
sankrantis, new moons, the amanta masa, and planetary stations.

Everything reduces to one primitive: a bracketed bisection root-finder on the
SIGNED WRAPPED difference between a monotone angle function and a target
(``_find_crossing``). Bisection is slow but GUARANTEED — for a panchanga
"till hh:mm" a 1-second tolerance is far below display precision, and every
bracket used here keeps the angle change under 180° so the wrap is unambiguous.

All functions take jd_ut and use :func:`ephemeris.sidereal_positions` (Lahiri
by default), so tithi/nakshatra boundaries agree exactly with the rest of the
engine.
"""

from __future__ import annotations

from .constants import NAKSHATRAS, SIGNS, TITHIS, YOGAS_27, karana_name
from .ephemeris import jd_to_utc, sidereal_positions
from .nakshatra import SPAN as NAK_SPAN
from .panchanga import panchanga

# Mean motion estimates (deg/day) — used ONLY for bracketing/initial guesses,
# never for the returned instants (those come from the root-finder).
_MEAN_ELONGATION_RATE = 12.19   # Moon - Sun
_MEAN_SUN_RATE = 0.9856

MASA_NAMES = [
    # Indexed by the SIGN the Sun ENTERS during the amanta month:
    # Mesha entry -> Chaitra, Vrishabha -> Vaishakha, ... Meena -> Phalguna.
    "Chaitra", "Vaishakha", "Jyeshtha", "Ashadha", "Shravana", "Bhadrapada",
    "Ashwina", "Kartika", "Margashirsha", "Pausha", "Magha", "Phalguna",
]

_STATION_PLANETS = ("mars", "mercury", "jupiter", "venus", "saturn")


# ── The root-finding primitive ───────────────────────────────────────────────

def _find_crossing(f, jd_lo: float, jd_hi: float, target: float,
                   tol_jd: float = 1.0 / 86400.0) -> float:
    """Bisect for the instant a monotone-increasing WRAPPED angle f crosses
    ``target`` (degrees, mod 360) inside [jd_lo, jd_hi].

    Works on the signed wrapped difference ((f - target + 180) % 360 - 180),
    so a crossing of 0°/360° is handled identically to any other angle. The
    caller must guarantee exactly one crossing in the bracket AND that f
    changes by less than 180° across it (all brackets in this module do).
    Tolerance: 1 second of time.
    """
    def diff(jd: float) -> float:
        return ((f(jd) - target + 180.0) % 360.0) - 180.0

    d_lo, d_hi = diff(jd_lo), diff(jd_hi)
    if d_lo == 0.0:
        return jd_lo
    if d_hi == 0.0:
        return jd_hi
    if not (d_lo < 0.0 < d_hi):
        raise ValueError(
            f"crossing not bracketed: diff({jd_lo})={d_lo:.4f}, "
            f"diff({jd_hi})={d_hi:.4f}, target={target}")
    while jd_hi - jd_lo > tol_jd:
        mid = 0.5 * (jd_lo + jd_hi)
        if diff(mid) < 0.0:
            jd_lo = mid
        else:
            jd_hi = mid
    return 0.5 * (jd_lo + jd_hi)


def _expand_bracket(f, guess: float, target: float, step: float = 1.0,
                    max_steps: int = 20) -> tuple[float, float]:
    """Grow [guess-step, guess+step] until it brackets the target crossing
    (signed diff negative at lo, positive at hi). Used where the crossing
    time is only estimated (new moons) rather than structurally bounded."""
    def diff(jd: float) -> float:
        return ((f(jd) - target + 180.0) % 360.0) - 180.0

    lo, hi = guess - step, guess + step
    for _ in range(max_steps):
        if diff(lo) < 0.0:
            break
        lo -= step
    for _ in range(max_steps):
        if diff(hi) >= 0.0:
            break
        hi += step
    return lo, hi


# ── Angle functions ──────────────────────────────────────────────────────────

def _elongation(jd_ut: float, ayanamsa: str = "lahiri") -> float:
    """Moon - Sun sidereal elongation (the tithi/karana angle).

    Ayanamsa cancels in the difference, but we stay on sidereal_positions so
    every module reads the same ephemeris path."""
    pos = sidereal_positions(jd_ut, ayanamsa=ayanamsa)
    return (pos["moon"]["lon"] - pos["sun"]["lon"]) % 360.0


def _moon_lon(jd_ut: float, ayanamsa: str = "lahiri") -> float:
    return sidereal_positions(jd_ut, ayanamsa=ayanamsa)["moon"]["lon"]


def _sun_lon(jd_ut: float, ayanamsa: str = "lahiri") -> float:
    return sidereal_positions(jd_ut, ayanamsa=ayanamsa)["sun"]["lon"]


def _yoga_angle(jd_ut: float, ayanamsa: str = "lahiri") -> float:
    pos = sidereal_positions(jd_ut, ayanamsa=ayanamsa)
    return (pos["sun"]["lon"] + pos["moon"]["lon"]) % 360.0


# ── Limb endings ─────────────────────────────────────────────────────────────

def tithi_end(jd_ut: float, ayanamsa: str = "lahiri") -> dict:
    """When the CURRENT tithi ends (elongation reaches the next 12° multiple).

    tithi_index is 1-based (1..30) to match panchanga(). Elongation grows
    ~12.19°/day (never slower than ~10.9), so [jd, jd+1.5] always brackets."""
    elong = _elongation(jd_ut, ayanamsa)
    idx = min(29, int(elong // 12.0))
    target = ((idx + 1) * 12.0) % 360.0
    ends = _find_crossing(lambda jd: _elongation(jd, ayanamsa),
                          jd_ut, jd_ut + 1.5, target)
    return {"tithi_index": idx + 1, "name": TITHIS[idx],
            "ends_jd": ends, "ends_utc": jd_to_utc(ends).isoformat()}


def nakshatra_end(jd_ut: float, ayanamsa: str = "lahiri") -> dict:
    """When the Moon reaches the next 13°20' boundary. index is 0-based
    (matching nakshatra_of). Moon moves 11.8-15.4°/day → jd+1.5 brackets."""
    lon = _moon_lon(jd_ut, ayanamsa)
    idx = min(26, int(lon // NAK_SPAN))
    target = ((idx + 1) * NAK_SPAN) % 360.0
    ends = _find_crossing(lambda jd: _moon_lon(jd, ayanamsa),
                          jd_ut, jd_ut + 1.5, target)
    return {"index": idx, "name": NAKSHATRAS[idx],
            "ends_jd": ends, "ends_utc": jd_to_utc(ends).isoformat()}


def yoga_end(jd_ut: float, ayanamsa: str = "lahiri") -> dict:
    """When (Sun + Moon) reaches the next 13°20' multiple. index 1-based."""
    ang = _yoga_angle(jd_ut, ayanamsa)
    idx = min(26, int(ang // NAK_SPAN))
    target = ((idx + 1) * NAK_SPAN) % 360.0
    ends = _find_crossing(lambda jd: _yoga_angle(jd, ayanamsa),
                          jd_ut, jd_ut + 1.5, target)
    return {"index": idx + 1, "name": YOGAS_27[idx],
            "ends_jd": ends, "ends_utc": jd_to_utc(ends).isoformat()}


def karana_end(jd_ut: float, ayanamsa: str = "lahiri") -> dict:
    """When the elongation reaches the next 6° multiple (half-tithi).
    index 1-based (1..60). Max wait ≈ 6/10.9 ≈ 0.55 d → jd+0.8 brackets."""
    elong = _elongation(jd_ut, ayanamsa)
    idx = min(59, int(elong // 6.0))
    target = ((idx + 1) * 6.0) % 360.0
    ends = _find_crossing(lambda jd: _elongation(jd, ayanamsa),
                          jd_ut, jd_ut + 0.8, target)
    return {"index": idx + 1, "name": karana_name(idx),
            "ends_jd": ends, "ends_utc": jd_to_utc(ends).isoformat()}


# ── Sankranti ────────────────────────────────────────────────────────────────

def sankranti(jd_ut: float, direction: int = +1, ayanamsa: str = "lahiri") -> dict:
    """The NEXT (direction=+1) or PREVIOUS (direction=-1) instant the sidereal
    Sun crosses a sign boundary.

    The Sun spends 29.3-31.5 days per sign, so a 32-day bracket is structural
    (change ≈ 31.5° < 180°, exactly one crossing of the boundary angle)."""
    lon = _sun_lon(jd_ut, ayanamsa)
    sign = int(lon // 30)
    if direction >= 0:
        target = ((sign + 1) * 30.0) % 360.0
        entered = (sign + 1) % 12
        lo, hi = jd_ut, jd_ut + 32.0
    else:
        target = sign * 30.0
        entered = sign
        lo, hi = jd_ut - 32.0, jd_ut
    jd = _find_crossing(lambda j: _sun_lon(j, ayanamsa), lo, hi, target)
    return {"sign_entered": entered, "sign_name": SIGNS[entered]["name"],
            "jd": jd, "utc": jd_to_utc(jd).isoformat()}


# ── New moons + amanta masa ──────────────────────────────────────────────────

def new_moon_after(jd_ut: float, ayanamsa: str = "lahiri") -> float:
    """The next elongation crossing of 360° (=0°) strictly after jd_ut."""
    e = _elongation(jd_ut, ayanamsa)
    delta = 360.0 - e
    if delta <= 0.0:  # exactly at a new moon → the NEXT one
        delta = 360.0
    guess = jd_ut + delta / _MEAN_ELONGATION_RATE
    lo, hi = _expand_bracket(lambda jd: _elongation(jd, ayanamsa), guess, 0.0)
    return _find_crossing(lambda jd: _elongation(jd, ayanamsa), lo, hi, 0.0)


def new_moon_before(jd_ut: float, ayanamsa: str = "lahiri") -> float:
    """The most recent elongation crossing of 0°/360° at or before jd_ut."""
    e = _elongation(jd_ut, ayanamsa)
    guess = jd_ut - e / _MEAN_ELONGATION_RATE
    lo, hi = _expand_bracket(lambda jd: _elongation(jd, ayanamsa), guess, 0.0)
    return _find_crossing(lambda jd: _elongation(jd, ayanamsa), lo, hi, 0.0)


def masa(jd_ut: float, ayanamsa: str = "lahiri") -> dict:
    """The AMANTA lunar month containing jd_ut.

    Rule (mainstream computational amanta): the month runs new moon → new
    moon; its name comes from the sign the Sun ENTERS during the month
    (Mesha entry → Chaitra, Vrishabha → Vaishakha, ...).

    - NO sankranti inside the month → ADHIKA (intercalary) month, named for
      the FOLLOWING month (the sign the next sankranti enters) with the
      "Adhika" prefix — e.g. Adhika Shravana, Jul-Aug 2023.
    - TWO sankrantis inside one month → KSHAYA (expunged) month, very rare
      (Sun races through the short Sagittarius-Capricorn signs); named here
      for the FIRST sign entered with kshaya=True.
    """
    start_jd = new_moon_before(jd_ut, ayanamsa)
    end_jd = new_moon_after(jd_ut, ayanamsa)

    crossings: list[dict] = []
    t = start_jd
    while len(crossings) < 3:
        s = sankranti(t + 1e-6, direction=+1, ayanamsa=ayanamsa)
        if s["jd"] >= end_jd:
            break
        crossings.append(s)
        t = s["jd"]

    adhika = len(crossings) == 0
    kshaya = len(crossings) >= 2
    if adhika:
        following = sankranti(end_jd + 1e-6, direction=+1, ayanamsa=ayanamsa)
        name = f"Adhika {MASA_NAMES[following['sign_entered']]}"
    else:
        name = MASA_NAMES[crossings[0]["sign_entered"]]

    elong = _elongation(jd_ut, ayanamsa)
    return {
        "name": name,
        "adhika": adhika,
        "kshaya": kshaya,
        "start_jd": start_jd,
        "end_jd": end_jd,
        "paksha_at_jd": "shukla" if elong < 180.0 else "krishna",
    }


# ── Planetary stations ───────────────────────────────────────────────────────

def station_near(jd_ut: float, planet: str, window_days: int = 200,
                 ayanamsa: str = "lahiri") -> dict | None:
    """The nearest station (speed sign change) for a true planet within
    ±window_days, refined to the minute by bisection on the speed.

    Scans outward from jd_ut a day at a time (both directions) so it stops at
    the first — i.e. nearest — sign change. Returns None if none in window.
    """
    if planet not in _STATION_PLANETS:
        raise ValueError(f"station_near: planet must be one of {_STATION_PLANETS}")

    def speed(jd: float) -> float:
        return sidereal_positions(jd, ayanamsa=ayanamsa)[planet]["speed"]

    def refine(lo: float, hi: float) -> dict:
        s_lo = speed(lo)
        while hi - lo > 1.0 / 1440.0:  # to the minute
            mid = 0.5 * (lo + hi)
            if speed(mid) * s_lo > 0:
                lo = mid
                s_lo = speed(lo)
            else:
                hi = mid
        jd = 0.5 * (lo + hi)
        kind = "retrograde_begins" if speed(hi) < 0 else "direct_begins"
        return {"planet": planet, "jd": jd,
                "utc": jd_to_utc(jd).isoformat(), "type": kind}

    cache: dict[int, float] = {}

    def day_speed(d: int) -> float:
        if d not in cache:
            cache[d] = speed(jd_ut + d)
        return cache[d]

    for d in range(0, window_days):
        # forward interval [jd+d, jd+d+1], backward interval [jd-d-1, jd-d]
        if day_speed(d) * day_speed(d + 1) < 0:
            return refine(jd_ut + d, jd_ut + d + 1)
        if day_speed(-d - 1) * day_speed(-d) < 0:
            return refine(jd_ut - d - 1, jd_ut - d)
    return None


# ── Panchanga with endings ───────────────────────────────────────────────────

def panchanga_with_endings(jd_ut: float, local_date, vara_date=None,
                           ayanamsa: str = "lahiri") -> dict:
    """The panchanga() dict augmented with ends_jd/ends_utc on each of
    tithi/nakshatra/yoga/karana — the "till 14:32" every panchanga needs."""
    pos = sidereal_positions(jd_ut, ayanamsa=ayanamsa)
    p = panchanga(pos["sun"]["lon"], pos["moon"]["lon"], local_date,
                  vara_date=vara_date)
    for limb, finder in (("tithi", tithi_end), ("nakshatra", nakshatra_end),
                         ("yoga", yoga_end), ("karana", karana_end)):
        ev = finder(jd_ut, ayanamsa=ayanamsa)
        p[limb]["ends_jd"] = ev["ends_jd"]
        p[limb]["ends_utc"] = ev["ends_utc"]
    return p

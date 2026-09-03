"""Varshaphal (Tajika annual chart) — solar return, muntha, year lord, sahams,
mudda dasha, Tajika aspects.

The annual chart is cast for the exact instant the SIDEREAL Sun returns to its
natal longitude (varsha pravesh). Everything downstream is deterministic
arithmetic over that instant's positions.

Documented simplifications (this module states its conventions; see the
"disclaimer" field of :func:`varshaphal`):

* **Year lord** — of the five classical office-bearers (panchadhikaris) the
  tri-rashi pati is SKIPPED (its triplicity tables vary by tradition); the
  remaining four candidates are ranked by a simple documented criterion
  (Tajika aspect to / presence in the annual lagna, tie-break by highest
  degree-in-sign).
* **Sahams** — the standard six, with the classical "+30°" correction as
  implemented in open-source Maitreya: saham = A − B + C, add 30° unless the
  zodiacal arc from B forward to A contains C.
* **Mudda dasha** — Vimshottari proportions compressed into one 365.25-day
  year, seeded from the annual Moon's nakshatra lord with FULL periods (no
  balance deduction — the sequence starts at the pravesh instant).
* **Tajika aspects** — sign-agnostic degree aspects (0/60/90/120/180) with
  per-planet deeptamsa orbs; applying (ithasala) vs separating (ishrafa) is
  judged by linear projection of the two longitudes at their current speeds.
"""

from __future__ import annotations

from .constants import (DASHA_ORDER, DASHA_YEAR_DAYS, DASHA_YEARS, GRAHAS,
                        SIGN_LORD, SIGNS, VIMSHOTTARI_TOTAL_YEARS)
from .ephemeris import houses, jd_to_utc, sidereal_positions
from .nakshatra import nakshatra_of

# Mean sidereal year in days — the step between successive solar returns.
SIDEREAL_YEAR_DAYS = 365.2564

# Mean Sun speed (deg/day) — Newton fallback when the ephemeris speed is odd.
_MEAN_SUN_SPEED = 0.9856

# Deeptamsa (orb) per planet, degrees — classical Tajika values.
DEEPTAMSA = {
    "sun": 15.0, "moon": 12.0, "mars": 8.0, "mercury": 7.0,
    "jupiter": 9.0, "venus": 7.0, "saturn": 9.0,
}

_TAJIKA_PLANETS = list(DEEPTAMSA)  # the 7 classical planets (no nodes)

_ASPECT_ANGLES = (0.0, 60.0, 90.0, 120.0, 180.0)

# Tajika SIGN aspects (1-based count from a sign): 3/5/9/11 friendly,
# 1/4/7/10 hostile — 2/6/8/12 carry no aspect. Used only for the year-lord
# "aspects the annual lagna" test.
_TAJIKA_SIGN_ASPECT_COUNTS = {1, 3, 4, 5, 7, 9, 10, 11}

# Saham formulas: name -> (A, B, reverses_at_night). C is always the lagna.
# "lagna" as a body means the annual ascendant longitude itself (Roga saham).
_SAHAM_FORMULAS = [
    ("punya", "moon", "sun", True),
    ("vidya", "sun", "moon", True),
    ("yasas", "jupiter", "punya_saham", True),
    ("vivaha", "venus", "saturn", False),
    ("karma", "mars", "mercury", False),
    ("roga", "lagna", "moon", False),
]


def _signed_diff(a: float, b: float) -> float:
    """Wrap-aware signed difference a − b, in (−180, +180]."""
    d = (a - b) % 360.0
    return d - 360.0 if d > 180.0 else d


def _iso(jd: float) -> str:
    return jd_to_utc(jd).isoformat()


# ── Varsha pravesh (solar return) ────────────────────────────────────────────

def varsha_pravesh(natal_sun_lon: float, birth_jd_ut: float, year_number: int,
                   lat: float, lng: float, ayanamsa: str = "lahiri") -> dict:
    """Instant of the ``year_number``-th sidereal solar return.

    ``year_number`` 1 = first birthday. Newton iteration on the Sun's sidereal
    longitude, seeded ``year_number`` sidereal years after birth; converges to
    |Δlon| < 1e-6° in a handful of steps (Sun speed ≈ 0.9856°/day).

    ``lat``/``lng`` are accepted for API symmetry with the annual chart —
    the return INSTANT itself is location-independent.
    """
    natal_sun_lon = natal_sun_lon % 360.0
    jd = birth_jd_ut + year_number * SIDEREAL_YEAR_DAYS
    for _ in range(30):
        sun = sidereal_positions(jd, ayanamsa=ayanamsa)["sun"]
        diff = _signed_diff(sun["lon"], natal_sun_lon)
        if abs(diff) < 1e-6:
            break
        speed = sun["speed"] if abs(sun["speed"]) > 1e-3 else _MEAN_SUN_SPEED
        jd -= diff / speed
    return {"jd": jd, "utc": _iso(jd), "year_number": year_number}


# ── Muntha ───────────────────────────────────────────────────────────────────

def muntha_sign(natal_lagna_sign: int, year_number: int) -> int:
    """Muntha advances one sign per year from the natal lagna (year 0 = lagna)."""
    return (natal_lagna_sign + year_number) % 12


# ── Sahams ───────────────────────────────────────────────────────────────────

def compute_saham(a: float, b: float, c: float) -> float:
    """Saham point = A − B + C with the standard Tajika correction.

    Add 30° UNLESS the zodiacal arc going forward from B to A contains C —
    the classical rule as implemented in open-source Maitreya.
    """
    point = (a - b + c) % 360.0
    arc_b_to_a = (a - b) % 360.0
    arc_b_to_c = (c - b) % 360.0
    if arc_b_to_c > arc_b_to_a:  # C not on the B→A arc → correction applies
        point = (point + 30.0) % 360.0
    return point


def _sahams(positions: dict[str, dict], lagna_lon: float, is_day: bool) -> dict:
    """The standard six sahams. Day formulas are listed in _SAHAM_FORMULAS;
    for NIGHT births A and B are swapped where classical (Punya/Vidya/Yasas)."""
    def lon_of(body: str, computed: dict[str, float]) -> float:
        if body == "lagna":
            return lagna_lon
        if body == "punya_saham":
            return computed["punya"]
        return positions[body]["lon"]

    out: dict[str, dict] = {}
    computed: dict[str, float] = {}
    for name, a_body, b_body, reverses in _SAHAM_FORMULAS:
        a_b = (b_body, a_body) if (reverses and not is_day) else (a_body, b_body)
        a, b = (lon_of(a_b[0], computed), lon_of(a_b[1], computed))
        point = compute_saham(a, b, lagna_lon)
        computed[name] = point
        sign = int(point // 30)
        out[name] = {
            "lon": round(point, 6),
            "sign": sign,
            "sign_name": SIGNS[sign]["en"],
            "formula": f"{a_b[0]} - {a_b[1]} + lagna",
        }
    return out


# ── Year lord (varsheshvara) ─────────────────────────────────────────────────

def _year_lord(positions: dict[str, dict], annual_lagna_sign: int,
               natal_lagna_sign: int, m_sign: int, is_day_pravesh: bool) -> dict:
    """Simplified panchadhikari selection.

    Candidates: lord of muntha sign, lord of annual lagna, lord of natal lagna,
    dinaratri pati (Sun for a day pravesh, Moon for night). The tri-rashi pati
    is SKIPPED — its triplicity tables differ between Tajika texts.

    Selection: prefer a candidate that occupies the annual lagna sign or casts
    a Tajika SIGN aspect (1/3/4/5/7/9/10/11 counted from its sign) onto it;
    tie-break (and fallback when none qualifies) by highest degree-in-sign.
    """
    candidates = {
        "muntha_lord": SIGN_LORD[m_sign],
        "annual_lagna_lord": SIGN_LORD[annual_lagna_sign],
        "natal_lagna_lord": SIGN_LORD[natal_lagna_sign],
        "dinaratri_pati": "sun" if is_day_pravesh else "moon",
    }
    ranked = []
    for office, planet in candidates.items():
        lon = positions[planet]["lon"]
        sign = int(lon // 30)
        count = (annual_lagna_sign - sign) % 12 + 1
        aspects_lagna = count in _TAJIKA_SIGN_ASPECT_COUNTS
        ranked.append({
            "office": office, "planet": planet,
            "aspects_annual_lagna": aspects_lagna,
            "degree_in_sign": round(lon % 30.0, 6),
        })
    ranked.sort(key=lambda c: (c["aspects_annual_lagna"], c["degree_in_sign"]),
                reverse=True)
    winner = ranked[0]
    return {
        "planet": winner["planet"],
        "office": winner["office"],
        "candidates": ranked,
        "method": "simplified: Tajika aspect to / presence in annual lagna, "
                  "tie-break by highest degree-in-sign; tri-rashi pati skipped",
    }


# ── Mudda dasha ──────────────────────────────────────────────────────────────

def mudda_dasha(annual_moon_lon: float, pravesh_jd: float) -> dict:
    """Vimshottari-proportioned dasha over one 365.25-day year.

    Each lord gets years × 365.25 / 120 days. Seeded from the ANNUAL Moon's
    nakshatra lord; FULL periods starting at the pravesh instant (simplified —
    no elapsed-fraction balance deduction). Antardashas are proportional
    within each period, starting from the period lord.
    """
    nak = nakshatra_of(annual_moon_lon)
    start_idx = DASHA_ORDER.index(nak["lord"])
    periods = []
    cursor = pravesh_jd
    for i in range(9):
        lord = DASHA_ORDER[(start_idx + i) % 9]
        length = DASHA_YEARS[lord] * DASHA_YEAR_DAYS / VIMSHOTTARI_TOTAL_YEARS
        antars = []
        a_idx = DASHA_ORDER.index(lord)
        a_cursor = cursor
        for j in range(9):
            a_lord = DASHA_ORDER[(a_idx + j) % 9]
            a_len = length * DASHA_YEARS[a_lord] / VIMSHOTTARI_TOTAL_YEARS
            antars.append({
                "lord": a_lord,
                "start_jd": a_cursor, "end_jd": a_cursor + a_len,
                "start": _iso(a_cursor), "end": _iso(a_cursor + a_len),
                "days": round(a_len, 6),
            })
            a_cursor += a_len
        periods.append({
            "lord": lord,
            "start_jd": cursor, "end_jd": cursor + length,
            "start": _iso(cursor), "end": _iso(cursor + length),
            "days": round(length, 6),
            "antardashas": antars,
        })
        cursor += length
    return {
        "system": "mudda",
        "moon_nakshatra": nak["name"],
        "year_days": DASHA_YEAR_DAYS,
        "periods": periods,
    }


# ── Tajika aspects ───────────────────────────────────────────────────────────

def tajika_aspects(positions: dict[str, dict]) -> list[dict]:
    """Degree aspects (0/60/90/120/180) between the 7 classical planets.

    Orb allowance = mean of the two planets' deeptamsas. Applying (ithasala)
    vs separating (ishrafa) is decided by projecting both longitudes forward
    at their current speeds and checking whether the aspect offset closes —
    a sign-agnostic simplification of the classical yoga (which also demands
    the faster planet be behind and of lower degree in its sign).
    """
    out = []
    dt = 0.01  # days — linear projection step
    for i, p1 in enumerate(_TAJIKA_PLANETS):
        for p2 in _TAJIKA_PLANETS[i + 1:]:
            l1, s1 = positions[p1]["lon"], positions[p1]["speed"]
            l2, s2 = positions[p2]["lon"], positions[p2]["speed"]
            sep_now = abs(_signed_diff(l1, l2))
            sep_next = abs(_signed_diff(l1 + s1 * dt, l2 + s2 * dt))
            orb_allow = (DEEPTAMSA[p1] + DEEPTAMSA[p2]) / 2.0
            for angle in _ASPECT_ANGLES:
                off_now = abs(sep_now - angle)
                if off_now > orb_allow:
                    continue
                off_next = abs(sep_next - angle)
                out.append({
                    "planets": [p1, p2],
                    "angle": angle,
                    "type": "ithasala" if off_next < off_now else "ishrafa",
                    "orb": round(off_now, 6),
                })
                break  # one aspect per pair (angles never overlap within orb)
    return out


# ── Full annual chart ────────────────────────────────────────────────────────

def varshaphal(natal_chart: dict, year_number: int) -> dict:
    """Full Tajika annual chart from a natal ChartV1 dict."""
    inp = natal_chart["input"]
    lat, lng, ayanamsa = inp["lat"], inp["lng"], inp["ayanamsa"]
    natal_sun_lon = natal_chart["grahas"]["sun"]["lon"]
    natal_lagna_sign = natal_chart["lagna"]["sign"]
    birth_jd = natal_chart["julian_day_ut"]
    is_day_birth = bool(natal_chart.get("is_day_birth", True))

    pravesh = varsha_pravesh(natal_sun_lon, birth_jd, year_number, lat, lng,
                             ayanamsa=ayanamsa)
    jd = pravesh["jd"]

    positions = sidereal_positions(jd, ayanamsa=ayanamsa)
    house_data = houses(jd, lat, lng, ayanamsa=ayanamsa, system="whole_sign")
    lagna_lon = house_data["ascendant"]
    annual_lagna_sign = int(lagna_lon // 30)

    grahas: dict[str, dict] = {}
    for g in GRAHAS:
        lon = positions[g]["lon"]
        sign = int(lon // 30)
        grahas[g] = {
            "lon": round(lon, 6),
            "sign": sign,
            "sign_name": SIGNS[sign]["en"],
            "house": (sign - annual_lagna_sign) % 12 + 1,
            "speed": positions[g]["speed"],
            "retrograde": positions[g]["retrograde"],
            "nakshatra": nakshatra_of(lon)["name"],
        }

    # Day/night at the PRAVESH (for the dinaratri pati): approximated by the
    # Sun's ecliptic position relative to the ascendant-descendant axis —
    # above the horizon ≈ within 180° behind the ascendant degree.
    is_day_pravesh = ((lagna_lon - positions["sun"]["lon"]) % 360.0) < 180.0

    m_sign = muntha_sign(natal_lagna_sign, year_number)
    muntha = {
        "sign": m_sign,
        "sign_name": SIGNS[m_sign]["en"],
        "house": (m_sign - annual_lagna_sign) % 12 + 1,
        "lord": SIGN_LORD[m_sign],
    }

    return {
        "schema": "VarshaphalV1",
        "year_number": year_number,
        "varsha_pravesh": pravesh,
        "lagna": {
            "lon": round(lagna_lon, 6),
            "sign": annual_lagna_sign,
            "sign_name": SIGNS[annual_lagna_sign]["en"],
            "lord": SIGN_LORD[annual_lagna_sign],
            "nakshatra": nakshatra_of(lagna_lon)["name"],
        },
        "grahas": grahas,
        "muntha": muntha,
        "year_lord": _year_lord(positions, annual_lagna_sign, natal_lagna_sign,
                                m_sign, is_day_pravesh),
        "sahams": _sahams(positions, lagna_lon, is_day_birth),
        "mudda_dasha": mudda_dasha(positions["moon"]["lon"], jd),
        "tajika_aspects": tajika_aspects(positions),
        "is_day_pravesh": is_day_pravesh,
        "disclaimer": (
            "Simplified Tajika conventions: year lord chosen among four "
            "office-bearers (tri-rashi pati skipped) by Tajika sign-aspect to "
            "the annual lagna with degree tie-break; sahams use the standard "
            "Maitreya-style +30° correction; mudda dasha uses full periods "
            "(no balance deduction); aspects are degree-based with mean "
            "deeptamsa orbs."
        ),
    }


# ── Nakta & Yamaya (transfer/collection of light) — Tajika Nilakanthi ───────
def nakta_yamaya(positions: dict[str, dict]) -> list[dict]:
    """Beyond ithasala/ishrafa: NAKTA — a fast planet C separates from A and
    applies to B (transferring A's light to B) while A and B share no ithasala
    themselves; YAMAYA — a SLOWER planet C receives applications from both A
    and B (collecting their light). Both simplified to degree aspects within
    deeptamsa orbs, applying/separating judged by relative speed (documented
    simplification, same convention as the ithasala detector)."""
    grahas = [g for g in ("moon", "mercury", "venus", "sun", "mars",
                          "jupiter", "saturn") if g in positions]

    def _sep(a: str, b: str) -> float:
        d = abs((positions[a]["lon"] - positions[b]["lon"]) % 360.0)
        return min(d, 360.0 - d)

    def _orb(a: str, b: str) -> float:
        return (DEEPTAMSA[a] + DEEPTAMSA[b]) / 2.0

    def _applying(fast: str, slow: str) -> bool:
        # closing any major Tajika angle
        for angle in (0, 60, 90, 120, 180):
            sep = _sep(fast, slow)
            if abs(sep - angle) <= _orb(fast, slow):
                rel = positions[fast]["speed"] - positions[slow]["speed"]
                closing = (sep - angle) * (1 if rel > 0 else -1)
                return rel != 0 and abs(sep - angle) > 1e-9 and (
                    (sep > angle and rel > 0) or (sep < angle and rel < 0))
        return False

    def _in_aspect(a: str, b: str) -> bool:
        return any(abs(_sep(a, b) - ang) <= _orb(a, b) for ang in (0, 60, 90, 120, 180))

    out = []
    for c in grahas:
        others = [g for g in grahas if g != c]
        for i, a in enumerate(others):
            for b in others[i + 1:]:
                if _in_aspect(a, b):
                    continue  # direct ithasala possible — no transfer needed
                c_fastest = abs(positions[c]["speed"]) > max(
                    abs(positions[a]["speed"]), abs(positions[b]["speed"]))
                c_slowest = abs(positions[c]["speed"]) < min(
                    abs(positions[a]["speed"]), abs(positions[b]["speed"]))
                if c_fastest and _in_aspect(c, a) and _applying(c, b) and not _applying(c, a):
                    out.append({"type": "nakta", "transferer": c,
                                "from": a, "to": b,
                                "note": f"{c} carries {a}'s light to {b}"})
                elif c_slowest and _applying(a, c) and _applying(b, c):
                    out.append({"type": "yamaya", "collector": c,
                                "from": [a, b],
                                "note": f"{c} collects the light of {a} and {b}"})
    return out

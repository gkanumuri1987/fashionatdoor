"""Extra dasha systems — Yogini, Ashtottari, and deep Vimshottari levels.

Pure deterministic arithmetic (no AI, no swisseph). Follows the conventions of
``jyotish.dasha``: year length = 365.25 days (``DASHA_YEAR_DAYS``), the first
period is back-dated so the balance at birth equals
(1 - fraction_elapsed) * lord_years, and every period carries both Julian-day
and ISO timestamps.

JD→ISO here is a local datetime conversion (JD 2451545.0 == 2000-01-01T12:00
UTC) rather than ``ephemeris.jd_to_utc`` — that helper pulls in swisseph,
which this module must not import. Linear offsetting from the J2000 anchor is
exact for UTC timestamps in our range (sub-millisecond).
"""

from __future__ import annotations

from datetime import datetime, timedelta

from .constants import DASHA_ORDER, DASHA_YEARS, DASHA_YEAR_DAYS, VIMSHOTTARI_TOTAL_YEARS
from .nakshatra import SPAN, nakshatra_of

_J2000_JD = 2451545.0
_J2000_DT = datetime(2000, 1, 1, 12, 0, 0)


def _jd_to_iso(jd: float) -> str:
    """ISO-8601 UTC timestamp for a Julian day (local, swisseph-free)."""
    return (_J2000_DT + timedelta(days=jd - _J2000_JD)).isoformat()


# ── Yogini ───────────────────────────────────────────────────────────────────
# 8 yoginis cycling, 36 years total. (name, lord, years) in cycle order.
YOGINI_ORDER: list[tuple[str, str, int]] = [
    ("Mangala", "moon", 1),
    ("Pingala", "sun", 2),
    ("Dhanya", "jupiter", 3),
    ("Bhramari", "mars", 4),
    ("Bhadrika", "mercury", 5),
    ("Ulka", "saturn", 6),
    ("Siddha", "venus", 7),
    ("Sankata", "rahu", 8),
]
YOGINI_TOTAL_YEARS = 36
_YOGINI_CYCLES = 3  # 3 × 36y = 108y coverage


def yogini_dasha(moon_lon: float, birth_jd_ut: float) -> dict:
    """Yogini dasha: 3 full 36-year cycles (24 mahadashas) with antardashas.

    Starting yogini = cycle ordinal ``(nakshatra_index + 3) % 8`` (0 = Mangala,
    nakshatra index 0-based from Ashwini). The first maha is back-dated so the
    balance at birth is (1 - fraction_elapsed_in_nakshatra) × its years.
    """
    nak = nakshatra_of(moon_lon)
    start_ord = (nak["index"] + 3) % 8
    frac = nak["fraction_elapsed"]

    first_years = YOGINI_ORDER[start_ord][2]
    seq_start_jd = birth_jd_ut - frac * first_years * DASHA_YEAR_DAYS
    balance_years = (1.0 - frac) * first_years

    mahas = []
    cursor = seq_start_jd
    for i in range(_YOGINI_CYCLES * 8):
        name, lord, years = YOGINI_ORDER[(start_ord + i) % 8]
        length_days = years * DASHA_YEAR_DAYS
        mahas.append({
            "yogini": name,
            "lord": lord,
            "years": years,
            "start_jd": cursor,
            "end_jd": cursor + length_days,
            "start": _jd_to_iso(cursor),
            "end": _jd_to_iso(cursor + length_days),
            "antardashas": _yogini_subs((start_ord + i) % 8, cursor, length_days),
        })
        cursor += length_days

    return {
        "system": "yogini",
        "moon_nakshatra": nak["name"],
        "balance_at_birth_years": round(balance_years, 6),
        "mahadashas": mahas,
    }


def _yogini_subs(maha_ord: int, start_jd: float, maha_len_days: float) -> list[dict]:
    """Antardashas within a yogini maha: the 8-cycle starting from the maha
    yogini itself, each spanning maha_len × sub_years / 36."""
    out = []
    cursor = start_jd
    for i in range(8):
        name, lord, years = YOGINI_ORDER[(maha_ord + i) % 8]
        length = maha_len_days * years / YOGINI_TOTAL_YEARS
        out.append({
            "yogini": name,
            "lord": lord,
            "start_jd": cursor,
            "end_jd": cursor + length,
            "start": _jd_to_iso(cursor),
            "end": _jd_to_iso(cursor + length),
        })
        cursor += length
    return out


# ── Ashtottari ───────────────────────────────────────────────────────────────
# 8 lords, 108 years total, in fixed cycle order.
ASHTOTTARI_ORDER: list[str] = ["sun", "moon", "mars", "mercury",
                               "saturn", "jupiter", "rahu", "venus"]
ASHTOTTARI_YEARS: dict[str, int] = {
    "sun": 6, "moon": 15, "mars": 8, "mercury": 17,
    "saturn": 10, "jupiter": 19, "rahu": 12, "venus": 21,
}
ASHTOTTARI_TOTAL_YEARS = 108

# Nakshatra groups assigned from KRITTIKA (index 2), sizes 3,4,3,4,3,4,3,3
# → Krittika,Rohini,Mrigashira→Sun; Ardra..Ashlesha→Moon; Magha..UPhalguni→Mars;
#   Hasta..Vishakha→Mercury; Anuradha..Mula→Saturn; PAshadha..Dhanishta→Jupiter;
#   Shatabhisha..UBhadrapada→Rahu; Revati,Ashwini,Bharani→Venus.
_ASHTOTTARI_GROUP_SIZES = [3, 4, 3, 4, 3, 4, 3, 3]
_ASHTOTTARI_START_NAK = 2  # Krittika

# Explicit 27-entry table: nak index → (lord, group_start_nak, group_size).
ASHTOTTARI_NAK_TABLE: dict[int, tuple[str, int, int]] = {}
_cursor_nak = _ASHTOTTARI_START_NAK
for _lord, _size in zip(ASHTOTTARI_ORDER, _ASHTOTTARI_GROUP_SIZES):
    for _pos in range(_size):
        ASHTOTTARI_NAK_TABLE[(_cursor_nak + _pos) % 27] = (_lord, _cursor_nak, _size)
    _cursor_nak = (_cursor_nak + _size) % 27
del _cursor_nak, _lord, _size, _pos

# Convenience: nak index → lord only.
ASHTOTTARI_NAK_LORD: list[str] = [ASHTOTTARI_NAK_TABLE[i][0] for i in range(27)]


def ashtottari_dasha(moon_lon: float, sun_lon: float, birth_jd_ut: float,
                     rahu_sign: int | None = None,
                     lagna_lord_sign: int | None = None) -> dict:
    """Ashtottari dasha (108y, 8 lords) from the Moon's nakshatra group.

    Balance convention (documented simplification): progress is measured across
    the WHOLE nakshatra group's arc (group_size × 13°20'), and the balance at
    birth is (1 - fraction_elapsed_in_group) × lord_years. ``sun_lon`` is
    accepted for API symmetry with classical variants that condition the count
    on the Sun; it does not enter this computation.

    Applicability: Ashtottari classically applies when Rahu occupies a quadrant
    or trine from the lagna lord. Pass ``rahu_sign``/``lagna_lord_sign``
    (0-based sign indices) to evaluate it; leaving either None yields
    ``applicable: None``.
    """
    del sun_lon  # documented: unused in this (moon-group) computation
    nak = nakshatra_of(moon_lon)
    lord, group_start, group_size = ASHTOTTARI_NAK_TABLE[nak["index"]]

    # Elapsed arc within the group (nakshatras are consecutive mod 27).
    naks_before = (nak["index"] - group_start) % 27
    group_arc = group_size * SPAN
    elapsed_deg = naks_before * SPAN + nak["fraction_elapsed"] * SPAN
    frac_group = elapsed_deg / group_arc

    first_years = ASHTOTTARI_YEARS[lord]
    seq_start_jd = birth_jd_ut - frac_group * first_years * DASHA_YEAR_DAYS
    balance_years = (1.0 - frac_group) * first_years
    start_idx = ASHTOTTARI_ORDER.index(lord)

    mahas = []
    cursor = seq_start_jd
    for i in range(8):
        l = ASHTOTTARI_ORDER[(start_idx + i) % 8]
        length_days = ASHTOTTARI_YEARS[l] * DASHA_YEAR_DAYS
        mahas.append({
            "lord": l,
            "years": ASHTOTTARI_YEARS[l],
            "start_jd": cursor,
            "end_jd": cursor + length_days,
            "start": _jd_to_iso(cursor),
            "end": _jd_to_iso(cursor + length_days),
            "antardashas": _ashtottari_subs(l, cursor, length_days),
        })
        cursor += length_days

    if rahu_sign is None or lagna_lord_sign is None:
        applicable = None
    else:
        offset = (rahu_sign - lagna_lord_sign) % 12  # house 1 = offset 0
        applicable = offset in {0, 3, 6, 9, 4, 8}    # quadrants + trines

    return {
        "system": "ashtottari",
        "moon_nakshatra": nak["name"],
        "balance_at_birth_years": round(balance_years, 6),
        "mahadashas": mahas,
        "applicability": {
            "applicable": applicable,
            "condition": "Rahu in a quadrant (1/4/7/10) or trine (1/5/9) "
                         "from the lagna lord",
        },
    }


def _ashtottari_subs(parent_lord: str, start_jd: float, parent_len_days: float) -> list[dict]:
    """Antardashas: 8-cycle starting from the maha lord, proportional in 108."""
    out = []
    idx = ASHTOTTARI_ORDER.index(parent_lord)
    cursor = start_jd
    for i in range(8):
        lord = ASHTOTTARI_ORDER[(idx + i) % 8]
        length = parent_len_days * ASHTOTTARI_YEARS[lord] / ASHTOTTARI_TOTAL_YEARS
        out.append({
            "lord": lord,
            "start_jd": cursor,
            "end_jd": cursor + length,
            "start": _jd_to_iso(cursor),
            "end": _jd_to_iso(cursor + length),
        })
        cursor += length
    return out


# ── Vimshottari deep levels (sookshma / prana) ───────────────────────────────

def _vim_subs(parent_lord: str, start_jd: float, parent_len_days: float) -> list[dict]:
    """Proportional Vimshottari subdivision seeded from the parent lord
    (same convention as jyotish.dasha._sub_periods, swisseph-free ISO)."""
    out = []
    idx = DASHA_ORDER.index(parent_lord)
    cursor = start_jd
    for i in range(9):
        lord = DASHA_ORDER[(idx + i) % 9]
        length = parent_len_days * DASHA_YEARS[lord] / VIMSHOTTARI_TOTAL_YEARS
        out.append({
            "lord": lord,
            "start_jd": cursor,
            "end_jd": cursor + length,
            "start": _jd_to_iso(cursor),
            "end": _jd_to_iso(cursor + length),
        })
        cursor += length
    return out


def vimshottari_levels(antar: dict, depth: int = 2) -> dict:
    """Sookshma (level 4) and prana (level 5) breakdown of one antardasha.

    ``antar`` must carry ``lord``, ``start_jd``, ``end_jd`` (as produced by
    jyotish.dasha). Sookshmas seed from the ANTAR lord; each prana run seeds
    from its sookshma's lord. Pranas are included only when ``depth >= 2``.
    """
    antar_len = antar["end_jd"] - antar["start_jd"]
    sookshmas = _vim_subs(antar["lord"], antar["start_jd"], antar_len)
    if depth >= 2:
        for s in sookshmas:
            s["pranas"] = _vim_subs(s["lord"], s["start_jd"], s["end_jd"] - s["start_jd"])
    return {"sookshmas": sookshmas}

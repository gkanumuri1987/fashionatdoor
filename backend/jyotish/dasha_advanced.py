"""Advanced dasha engines — Kalachakra, Narayana, and year-length Vimshottari.

Pure deterministic arithmetic (no AI, no swisseph). Follows the conventions of
``jyotish.dasha`` / ``jyotish.dasha_extra``: year length defaults to 365.25
days (``DASHA_YEAR_DAYS``), the first period is back-dated so the balance at
birth equals the un-elapsed fraction, and every period carries both Julian-day
and ISO timestamps.

VARIANT NOTES (read before comparing against other software):

* KALACHAKRA — several traditional variants exist (the pada→sequence tables in
  BPHS commentaries, JHora, and Maitreya differ in detail). This module
  implements the compact "computational-standard" rule, flagged in the output
  as ``"variant": "computational-standard"``:

  - Savya/apasavya alternates every THREE nakshatras starting savya at
    Ashwini (naks 0-2 savya, 3-5 apasavya, 6-8 savya, ...).
  - The savya 36-sign walk across a nakshatra's 4 padas is the zodiacal order
    repeated three times (4 padas x 9 signs = 36 = 3 x 12): pada 1 starts at
    Aries and takes 9 signs, pada 2 continues from Capricorn, pada 3 from
    Libra, pada 4 from Cancer.
  - The apasavya walk is the savya walk REVERSED AS A WHOLE (so apasavya
    pada 1 runs Pisces, Aquarius, ... backward).
  - Paramayus of a pada = the sum of its 9 signs' years. Deha = first sign of
    the pada's sequence, Jeeva = last.
  - "Gati" step labels (krama / mandooka / simhavalokana / markati) are
    DESCRIPTIVE annotations of the step size between consecutive signs in the
    resulting sequence, not an independent input.

* NARAYANA — Jaimini sign dasha per the standard progression rules; the
  antardasha scheme is a documented simplification (12 equal subs walking the
  maha sequence from the sign after the maha sign).

JD→ISO is the same swisseph-free conversion as ``jyotish.dasha_extra``
(JD 2451545.0 == 2000-01-01T12:00 UTC; linear offsetting is exact for UTC
timestamps in our range).
"""

from __future__ import annotations

from datetime import datetime, timedelta

from .constants import (DASHA_ORDER, DASHA_YEARS, DASHA_YEAR_DAYS, SIGNS,
                        SIGN_LORD, VIMSHOTTARI_TOTAL_YEARS)
from .nakshatra import PADA_SPAN, nakshatra_of

_J2000_JD = 2451545.0
_J2000_DT = datetime(2000, 1, 1, 12, 0, 0)


def _jd_to_iso(jd: float) -> str:
    """ISO-8601 UTC timestamp for a Julian day (local, swisseph-free)."""
    return (_J2000_DT + timedelta(days=jd - _J2000_JD)).isoformat()


def _sign_name(sign: int) -> str:
    return SIGNS[sign]["name"]


# ── Kalachakra ───────────────────────────────────────────────────────────────

# Classical Kalachakra years per sign (Aries..Pisces).
KALACHAKRA_YEARS: list[int] = [7, 16, 9, 21, 5, 9, 16, 7, 10, 4, 4, 10]

# Full savya walk across one nakshatra's 4 padas: zodiacal order thrice.
_SAVYA_WALK: list[int] = [k % 12 for k in range(36)]
# Apasavya walk = the savya walk reversed as a whole.
_APASAVYA_WALK: list[int] = list(reversed(_SAVYA_WALK))

_GATI_BY_STEP = {1: "krama", 3: "mandooka", 5: "simhavalokana"}


def is_savya_nakshatra(nak_index: int) -> bool:
    """Savya/apasavya alternates every three nakshatras starting savya at
    Ashwini: naks 0-2 savya, 3-5 apasavya, 6-8 savya, ..."""
    return ((nak_index % 27) // 3) % 2 == 0


def kalachakra_sequence(nak_index: int, pada: int) -> list[int]:
    """The 9-sign amsa sequence for a nakshatra pada (pada 1-4)."""
    walk = _SAVYA_WALK if is_savya_nakshatra(nak_index) else _APASAVYA_WALK
    off = 9 * (pada - 1)
    return walk[off:off + 9]


def _gati(prev_sign: int, next_sign: int) -> str:
    """Descriptive step label: adjacent forward = krama; the classical jumps
    (mandooka = frog leap, simhavalokana = lion's glance / trine jump) label
    step sizes 3 and 5; anything else (incl. the reverse -1 step of apasavya
    walks) = markati (monkey walk)."""
    step = (next_sign - prev_sign) % 12
    return _GATI_BY_STEP.get(step, "markati")


def kalachakra(moon_lon: float, birth_jd_ut: float) -> dict:
    """Kalachakra dasha for one full paramayus cycle from the back-dated start.

    Balance convention: the fraction of the 3°20' pada the Moon has traversed
    is the fraction of the pada's paramayus already consumed from the start of
    its sequence; the sequence start is back-dated accordingly.

    See the module docstring — this is the "computational-standard" variant;
    other traditional pada→sequence tables exist.
    """
    nak = nakshatra_of(moon_lon)
    savya = is_savya_nakshatra(nak["index"])
    pada = nak["pada"]
    seq = kalachakra_sequence(nak["index"], pada)
    years = [KALACHAKRA_YEARS[s] for s in seq]
    paramayus = sum(years)

    # Fraction elapsed WITHIN the pada.
    within_pada = (moon_lon % 360.0) % PADA_SPAN
    frac = within_pada / PADA_SPAN
    elapsed_years = frac * paramayus
    seq_start_jd = birth_jd_ut - elapsed_years * DASHA_YEAR_DAYS
    balance_years = paramayus - elapsed_years

    mahas = []
    cursor = seq_start_jd
    prev_sign: int | None = None
    for sign, yrs in zip(seq, years):
        length_days = yrs * DASHA_YEAR_DAYS
        mahas.append({
            "sign": sign,
            "sign_name": _sign_name(sign),
            "years": yrs,
            "start_jd": cursor,
            "end_jd": cursor + length_days,
            "start": _jd_to_iso(cursor),
            "end": _jd_to_iso(cursor + length_days),
            "gati": None if prev_sign is None else _gati(prev_sign, sign),
        })
        cursor += length_days
        prev_sign = sign

    return {
        "system": "kalachakra",
        "variant": "computational-standard",
        "moon_nakshatra": nak["name"],
        "savya": savya,
        "pada": pada,
        "sequence": [_sign_name(s) for s in seq],
        "sequence_signs": seq,
        "years": years,
        "paramayus": paramayus,
        "deha": _sign_name(seq[0]),
        "jeeva": _sign_name(seq[-1]),
        "balance_years": round(balance_years, 6),
        "mahadashas": mahas,
    }


# ── Narayana ─────────────────────────────────────────────────────────────────

_CO_LORDS = {7: ("mars", "ketu"), 10: ("saturn", "rahu")}


def _graha_sign(positions: dict[str, dict], graha: str) -> int:
    return int((positions[graha]["lon"] % 360.0) // 30)


def _deg_in_sign(positions: dict[str, dict], graha: str) -> float:
    return (positions[graha]["lon"] % 360.0) % 30.0


def narayana_sign_lord(sign: int, positions: dict[str, dict]) -> str:
    """Working lord of a sign for Narayana purposes.

    Scorpio/Aquarius co-lord rule (BPHS convention, documented): Scorpio is
    co-ruled by Mars/Ketu, Aquarius by Saturn/Rahu. If exactly one co-lord
    occupies the sign itself, the OTHER is used; otherwise the co-lord at the
    higher degree within its sign wins. A co-lord absent from ``positions``
    cedes to the one present; both absent → the classical lord (Mars/Saturn).
    """
    co = _CO_LORDS.get(sign)
    if co is None:
        return SIGN_LORD[sign]
    present = [g for g in co if g in positions]
    if not present:
        return co[0]
    if len(present) == 1:
        return present[0]
    in_sign = [g for g in present if _graha_sign(positions, g) == sign]
    if len(in_sign) == 1:
        return co[1] if in_sign[0] == co[0] else co[0]
    return max(present, key=lambda g: _deg_in_sign(positions, g))


def _narayana_years(sign: int, positions: dict[str, dict]) -> int:
    """Years = count from the sign to its (working) lord's sign − 1, counting
    forward for odd signs and backward for even signs; lord in own sign = 12."""
    lord = narayana_sign_lord(sign, positions)
    if lord not in positions:
        return 12  # documented fallback: lord unplaced → full span
    lord_sign = _graha_sign(positions, lord)
    if lord_sign == sign:
        return 12
    if sign % 2 == 0:  # odd sign (Aries=0 is the 1st, odd) → count forward
        count = ((lord_sign - sign) % 12) + 1
    else:              # even sign → count backward
        count = ((sign - lord_sign) % 12) + 1
    return count - 1


def _mobility(sign: int) -> str:
    return ("movable", "fixed", "dual")[sign % 3]


def narayana_progression(start_sign: int, forward: bool = True) -> list[int]:
    """The 12-sign Narayana order from a starting sign, per its sign type:
    movable → every sign in order; fixed → every 6th (1st, 6th, 11th, ...);
    dual → trines then shift (1st, 5th, 9th; 2nd, 6th, 10th; ...).
    ``forward=False`` mirrors the offsets (even-footed start signs)."""
    mob = _mobility(start_sign)
    if mob == "movable":
        offsets = list(range(12))
    elif mob == "fixed":
        offsets = [(5 * k) % 12 for k in range(12)]
    else:  # dual
        offsets = [(shift + 4 * k) % 12 for shift in range(4) for k in range(3)]
    sgn = 1 if forward else -1
    return [(start_sign + sgn * o) % 12 for o in offsets]


def narayana_dasha(lagna_sign: int, positions: dict[str, dict],
                   birth_jd_ut: float) -> dict:
    """Narayana (Jaimini) sign dasha.

    ``positions`` maps graha → {"lon": sidereal longitude}; signs and degrees
    are derived from it.

    Start = the STRONGER of lagna and its 7th (more occupying grahas; tie →
    the sign whose working lord sits at the higher degree within its sign;
    still tied → the lagna sign). Direction: odd-footed starting sign →
    forward, even → reversed. Antardashas are a documented simplification:
    12 equal subs walking the same maha sequence starting from the sign after
    the maha sign.
    """
    lagna_sign %= 12
    seventh = (lagna_sign + 6) % 12
    occ = {lagna_sign: 0, seventh: 0}
    for g in positions:
        s = _graha_sign(positions, g)
        if s in occ:
            occ[s] += 1

    if occ[lagna_sign] > occ[seventh]:
        start = lagna_sign
    elif occ[seventh] > occ[lagna_sign]:
        start = seventh
    else:
        def _lord_deg(sign: int) -> float:
            lord = narayana_sign_lord(sign, positions)
            return _deg_in_sign(positions, lord) if lord in positions else -1.0
        start = seventh if _lord_deg(seventh) > _lord_deg(lagna_sign) else lagna_sign

    forward = start % 2 == 0  # odd-footed sign (Aries=0, ...) → forward
    seq = narayana_progression(start, forward)

    mahas = []
    cursor = birth_jd_ut
    for pos, sign in enumerate(seq):
        yrs = _narayana_years(sign, positions)
        length_days = yrs * DASHA_YEAR_DAYS
        sub_seq = seq[pos + 1:] + seq[:pos + 1]  # walk on, from the next sign
        sub_len = length_days / 12.0
        antars = []
        sub_cursor = cursor
        for sub_sign in sub_seq:
            antars.append({
                "sign": sub_sign,
                "sign_name": _sign_name(sub_sign),
                "start_jd": sub_cursor,
                "end_jd": sub_cursor + sub_len,
                "start": _jd_to_iso(sub_cursor),
                "end": _jd_to_iso(sub_cursor + sub_len),
            })
            sub_cursor += sub_len
        mahas.append({
            "sign": sign,
            "sign_name": _sign_name(sign),
            "years": yrs,
            "start_jd": cursor,
            "end_jd": cursor + length_days,
            "start": _jd_to_iso(cursor),
            "end": _jd_to_iso(cursor + length_days),
            "antardashas": antars,
        })
        cursor += length_days

    return {
        "system": "narayana",
        "start_sign": start,
        "start_sign_name": _sign_name(start),
        "start_mobility": _mobility(start),
        "forward": forward,
        "sequence": [_sign_name(s) for s in seq],
        "sequence_signs": seq,
        "mahadashas": mahas,
        "note": "antardashas simplified: 12 equal subs walking the maha "
                "sequence from the sign after the maha sign",
    }


# ── Vimshottari with selectable year length ──────────────────────────────────

def vimshottari_with_year(moon_lon: float, birth_jd_ut: float,
                          year_days: float = 365.25) -> dict:
    """Vimshottari maha/antar sequence with a selectable year length.

    Same shape and conventions as ``jyotish.dasha.vimshottari`` (back-dated
    first maha, antars proportional in 120) plus a ``year_days`` key. Use
    360.0 for the savana year or 365.25 (default) for the traditional solar
    year. Re-implemented locally (rather than reusing jyotish.dasha) to stay
    swisseph-free and to thread ``year_days`` through.
    """
    nak = nakshatra_of(moon_lon)
    first_lord = nak["lord"]
    frac = nak["fraction_elapsed"]
    start_idx = DASHA_ORDER.index(first_lord)

    first_len_days = DASHA_YEARS[first_lord] * year_days
    seq_start_jd = birth_jd_ut - frac * first_len_days
    balance_years = (1.0 - frac) * DASHA_YEARS[first_lord]

    mahas = []
    cursor = seq_start_jd
    for i in range(9):
        lord = DASHA_ORDER[(start_idx + i) % 9]
        length_days = DASHA_YEARS[lord] * year_days
        mahas.append({
            "lord": lord,
            "years": DASHA_YEARS[lord],
            "start_jd": cursor,
            "end_jd": cursor + length_days,
            "start": _jd_to_iso(cursor),
            "end": _jd_to_iso(cursor + length_days),
            "antardashas": _vim_subs(lord, cursor, length_days),
        })
        cursor += length_days

    return {
        "system": "vimshottari",
        "year_days": year_days,
        "moon_nakshatra": nak["name"],
        "balance_at_birth_years": round(balance_years, 6),
        "mahadashas": mahas,
    }


def _vim_subs(parent_lord: str, start_jd: float, parent_len_days: float) -> list[dict]:
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

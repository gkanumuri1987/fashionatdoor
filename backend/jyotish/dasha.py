"""Vimshottari dasha — maha/antar (+ pratyantar on demand) with exact datetimes.

Every predictive claim in the AI layer hangs off these dates, so this module is
pure arithmetic with heavy tests. Year length = 365.25 days (traditional,
matches Jagannatha Hora's default).
"""

from __future__ import annotations

from .constants import DASHA_ORDER, DASHA_YEARS, DASHA_YEAR_DAYS, VIMSHOTTARI_TOTAL_YEARS
from .ephemeris import jd_to_utc
from .nakshatra import nakshatra_of


def _iso(jd: float) -> str:
    return jd_to_utc(jd).isoformat()


def vimshottari(moon_lon: float, birth_jd_ut: float, cycles: int = 2) -> dict:
    """Full maha-dasha sequence (with antardashas).

    The first maha began BEFORE birth: its start is back-dated so that the
    balance remaining at birth equals (1 - fraction_elapsed) * lord_years.

    ``cycles`` maha-dasha cycles are generated (default 2 = 18 mahadashas ≈ 240
    years). One cycle only covers ``120 - elapsed_first_lord`` years AFTER birth,
    so a single cycle runs out for elderly charts or any future-dated query and
    ``current_period`` would return None — the vimshottari cycle repeats, so we
    generate a second cycle to keep the active period resolvable across a full
    lifetime and beyond.
    """
    nak = nakshatra_of(moon_lon)
    first_lord = nak["lord"]
    frac = nak["fraction_elapsed"]
    start_idx = DASHA_ORDER.index(first_lord)

    first_len_days = DASHA_YEARS[first_lord] * DASHA_YEAR_DAYS
    seq_start_jd = birth_jd_ut - frac * first_len_days
    balance_years = (1.0 - frac) * DASHA_YEARS[first_lord]

    mahas = []
    cursor = seq_start_jd
    for i in range(9 * max(1, cycles)):
        lord = DASHA_ORDER[(start_idx + i) % 9]
        length_days = DASHA_YEARS[lord] * DASHA_YEAR_DAYS
        maha = {
            "lord": lord,
            "years": DASHA_YEARS[lord],
            "start_jd": cursor,
            "end_jd": cursor + length_days,
            "start": _iso(cursor),
            "end": _iso(cursor + length_days),
            "antardashas": _sub_periods(lord, cursor, length_days),
        }
        mahas.append(maha)
        cursor += length_days

    return {
        "system": "vimshottari",
        "moon_nakshatra": nak["name"],
        "balance_at_birth_years": round(balance_years, 6),
        "mahadashas": mahas,
    }


def _sub_periods(parent_lord: str, parent_start_jd: float, parent_len_days: float) -> list[dict]:
    """Sub-periods within a period: vimshottari order starting from the parent lord,
    each spanning parent_len * sub_years / 120."""
    out = []
    idx = DASHA_ORDER.index(parent_lord)
    cursor = parent_start_jd
    for i in range(9):
        lord = DASHA_ORDER[(idx + i) % 9]
        length = parent_len_days * DASHA_YEARS[lord] / VIMSHOTTARI_TOTAL_YEARS
        out.append({
            "lord": lord,
            "start_jd": cursor,
            "end_jd": cursor + length,
            "start": _iso(cursor),
            "end": _iso(cursor + length),
        })
        cursor += length
    return out


def pratyantardashas(maha_lord: str, antar: dict) -> list[dict]:
    """Pratyantar breakdown of one antardasha (computed on demand).

    Note: sub-periods seed from the ANTAR lord (correct convention);
    ``maha_lord`` is kept only for call-site/API stability."""
    return _sub_periods(antar["lord"], antar["start_jd"], antar["end_jd"] - antar["start_jd"])


def current_period(dasha: dict, as_of_jd: float) -> dict | None:
    """Locate the maha/antar/pratyantar active at a Julian day."""
    for maha in dasha["mahadashas"]:
        if maha["start_jd"] <= as_of_jd < maha["end_jd"]:
            for antar in maha["antardashas"]:
                if antar["start_jd"] <= as_of_jd < antar["end_jd"]:
                    for prat in pratyantardashas(maha["lord"], antar):
                        if prat["start_jd"] <= as_of_jd < prat["end_jd"]:
                            return {"maha": maha["lord"], "antar": antar["lord"],
                                    "pratyantar": prat["lord"],
                                    "maha_end": maha["end"], "antar_end": antar["end"],
                                    "pratyantar_end": prat["end"]}
    return None

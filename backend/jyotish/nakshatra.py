"""Nakshatra + pada from a sidereal longitude."""

from __future__ import annotations

from .constants import NAKSHATRAS, nakshatra_lord

SPAN = 360.0 / 27.0        # 13°20'
PADA_SPAN = SPAN / 4.0     # 3°20'


def nakshatra_of(lon: float) -> dict:
    lon = lon % 360.0
    idx = min(26, int(lon // SPAN))
    within = lon - idx * SPAN
    pada = min(4, int(within // PADA_SPAN) + 1)
    return {
        "index": idx,
        "name": NAKSHATRAS[idx],
        "pada": pada,
        "lord": nakshatra_lord(idx),
        "fraction_elapsed": within / SPAN,
    }

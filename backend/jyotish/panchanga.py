"""Panchanga (five limbs) at the birth instant.

v1 limitation, documented: vara is taken from the LOCAL CIVIL date, while the
traditional vara runs sunrise-to-sunrise. A birth between midnight and sunrise
is labelled with the civil weekday; a sunrise-based vara (swe.rise_trans) is a
tracked follow-up. Tithi/yoga/karana/nakshatra are exact.
"""

from __future__ import annotations

from datetime import date

from .constants import TITHIS, YOGAS_27, VARAS, VARA_LORDS, karana_name
from .nakshatra import nakshatra_of


def panchanga(sun_lon: float, moon_lon: float, local_date: date) -> dict:
    elong = (moon_lon - sun_lon) % 360.0
    tithi_idx = min(29, int(elong // 12.0))
    yoga_idx = min(26, int(((sun_lon + moon_lon) % 360.0) // (360.0 / 27.0)))
    karana_idx = min(59, int(elong // 6.0))
    wd = local_date.weekday()
    return {
        "tithi": {"index": tithi_idx + 1, "name": TITHIS[tithi_idx],
                  "paksha": "shukla" if tithi_idx < 15 else "krishna"},
        "vara": {"name": VARAS[wd], "lord": VARA_LORDS[wd], "basis": "civil_date"},
        "nakshatra": nakshatra_of(moon_lon),
        "yoga": {"index": yoga_idx + 1, "name": YOGAS_27[yoga_idx]},
        "karana": {"index": karana_idx + 1, "name": karana_name(karana_idx)},
    }

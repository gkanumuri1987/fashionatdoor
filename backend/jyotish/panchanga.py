"""Panchanga (five limbs) at the birth instant.

Vara runs sunrise-to-sunrise (traditional): chart.py passes the
sunrise-adjusted vara_date, so a birth between midnight and sunrise correctly
takes the PREVIOUS vara. Tithi/yoga/karana/nakshatra are exact.
"""

from __future__ import annotations

from datetime import date

from .constants import TITHIS, YOGAS_27, VARAS, VARA_LORDS, karana_name
from .nakshatra import nakshatra_of


def panchanga(sun_lon: float, moon_lon: float, local_date: date,
              vara_date: date | None = None) -> dict:
    """vara_date: the sunrise-adjusted civil date (a birth before sunrise
    belongs to the PREVIOUS vara). When omitted, falls back to local_date."""
    elong = (moon_lon - sun_lon) % 360.0
    tithi_idx = min(29, int(elong // 12.0))
    yoga_idx = min(26, int(((sun_lon + moon_lon) % 360.0) // (360.0 / 27.0)))
    karana_idx = min(59, int(elong // 6.0))
    basis = "sunrise" if vara_date is not None else "civil_date"
    wd = (vara_date or local_date).weekday()
    return {
        "tithi": {"index": tithi_idx + 1, "name": TITHIS[tithi_idx],
                  "paksha": "shukla" if tithi_idx < 15 else "krishna"},
        "vara": {"name": VARAS[wd], "lord": VARA_LORDS[wd], "basis": basis},
        "nakshatra": nakshatra_of(moon_lon),
        "yoga": {"index": yoga_idx + 1, "name": YOGAS_27[yoga_idx]},
        "karana": {"index": karana_idx + 1, "name": karana_name(karana_idx)},
    }

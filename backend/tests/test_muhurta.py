"""Muhurta scanner tests — real ephemeris, deterministic dates."""

from datetime import date

from jyotish.muhurta import scan_days


def test_scan_shape_and_verdicts():
    days = scan_days(date(2026, 9, 1), 7, lat=17.385, lng=78.4867)
    assert len(days) == 7
    for d in days:
        assert d["verdict"] in ("good", "mixed", "avoid")
        assert d["vara"] and d["tithi"] and d["nakshatra"]
        assert d["sunrise_utc"] is not None


def test_personal_tarabala_included():
    days = scan_days(date(2026, 9, 1), 3, lat=17.385, lng=78.4867,
                     natal_moon_nak=20, natal_moon_sign=8)
    for d in days:
        assert d["tarabala"] is not None and 1 <= d["tarabala"]["count"] <= 9
        assert d["chandrabala"] is not None and 1 <= d["chandrabala"]["count"] <= 12


def test_cap_at_60_days():
    days = scan_days(date(2026, 1, 1), 90, lat=17.385, lng=78.4867)
    assert len(days) == 60

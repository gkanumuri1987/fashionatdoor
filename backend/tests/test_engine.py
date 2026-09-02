"""Engine integration tests — real ephemeris anchors + full-chart invariants.

Astronomical anchors are events whose configuration is a public fact (eclipses,
full moons, published ayanamsa values), so they validate the ephemeris + sidereal
pipeline without trusting our own output. The full-chart snapshot pins engine
output for regression; its values are additionally cross-checked manually against
Jagannatha Hora (see scripts/verify_chart.py).
"""

from datetime import date, datetime, time, timezone

import pytest

from jyotish.chart import compute_chart, transit_report
from jyotish.ephemeris import ayanamsa_value, julian_day_ut, sidereal_positions
from jyotish.panchanga import panchanga
from jyotish.schema import ChartV1


def _jd(y, m, d, hh=0, mm=0):
    return julian_day_ut(datetime(y, m, d, hh, mm, tzinfo=timezone.utc))


# ── Astronomical anchors ─────────────────────────────────────────────────────

def test_lahiri_ayanamsa_2000():
    # Published Lahiri value near J2000 ≈ 23°51' (23.85°).
    ay = ayanamsa_value(_jd(2000, 1, 1, 12), "lahiri")
    assert 23.7 < ay < 24.0


def test_lahiri_ayanamsa_2024():
    # ≈ 24°12' in 2024.
    ay = ayanamsa_value(_jd(2024, 1, 1), "lahiri")
    assert 24.0 < ay < 24.4


def test_solar_eclipse_2020_is_amavasya():
    # Annular eclipse peak 2020-06-21 ~06:40 UTC — Sun/Moon conjunct.
    jd = _jd(2020, 6, 21, 6, 40)
    pos = sidereal_positions(jd)
    sep = abs((pos["moon"]["lon"] - pos["sun"]["lon"]) % 360.0)
    sep = min(sep, 360.0 - sep)
    assert sep < 1.0
    p = panchanga(pos["sun"]["lon"], pos["moon"]["lon"], date(2020, 6, 21))
    assert p["tithi"]["name"] == "Amavasya"


def test_full_moon_2024_04_23():
    # Purnima (Hanuman Jayanti) 2024-04-23; full moon ~23:49 IST.
    jd = _jd(2024, 4, 23, 12, 0)
    pos = sidereal_positions(jd)
    p = panchanga(pos["sun"]["lon"], pos["moon"]["lon"], date(2024, 4, 23))
    assert p["tithi"]["name"] == "Purnima"


def test_saturn_slow_moon_fast():
    jd = _jd(2000, 6, 1)
    pos = sidereal_positions(jd)
    assert abs(pos["saturn"]["speed"]) < 0.15
    assert 11.0 < abs(pos["moon"]["speed"]) < 16.0


# ── Full chart invariants ────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def chart():
    return compute_chart(date(1990, 5, 15), time(10, 30),
                         lat=17.385, lng=78.4867, tz_name="Asia/Kolkata")


def test_chart_validates_against_schema(chart):
    ChartV1.model_validate(chart)


def test_chart_basic_invariants(chart):
    assert len(chart["grahas"]) == 9
    assert all(0 <= g["lon"] < 360 for g in chart["grahas"].values())
    assert all(1 <= g["house"] <= 12 for g in chart["grahas"].values())
    assert len(chart["bhavas"]) == 12
    # Whole-sign: each bhava sign advances by one from lagna.
    lagna = chart["lagna"]["sign"]
    for b in chart["bhavas"]:
        assert b["sign"] == (lagna + b["house"] - 1) % 12
    # Rahu/Ketu exactly opposite.
    sep = abs(chart["grahas"]["rahu"]["lon"] - chart["grahas"]["ketu"]["lon"])
    assert min(sep, 360 - sep) == pytest.approx(180.0, abs=1e-6)
    # Occupants agree with graha houses.
    for b in chart["bhavas"]:
        for g in b["occupants"]:
            assert chart["grahas"][g]["house"] == b["house"]


def test_chart_utc_conversion(chart):
    assert chart["input"]["utc"].startswith("1990-05-15T05:00:00")
    assert chart["input"]["utc_offset_hours"] == 5.5


def test_dasha_first_lord_matches_moon_nakshatra(chart):
    from jyotish.constants import nakshatra_lord
    nak = chart["grahas"]["moon"]["nakshatra"]
    assert chart["vimshottari"]["mahadashas"][0]["lord"] == nakshatra_lord(nak["index"])
    assert chart["vimshottari"]["moon_nakshatra"] == nak["name"]


def test_transit_report_shape(chart):
    rep = transit_report(chart, datetime(2026, 8, 25, tzinfo=timezone.utc))
    assert len(rep["transits"]) == 9
    sat = rep["transits"]["saturn"]["house_from_moon"]
    assert rep["sade_sati"]["active"] == (sat in (12, 1, 2))


def test_determinism(chart):
    again = compute_chart(date(1990, 5, 15), time(10, 30),
                          lat=17.385, lng=78.4867, tz_name="Asia/Kolkata")
    # current_dasha depends on "now" — exclude it, everything else identical.
    a = {k: v for k, v in chart.items() if k != "current_dasha"}
    b = {k: v for k, v in again.items() if k != "current_dasha"}
    assert a == b


def test_ayanamsa_changes_positions():
    kwargs = dict(lat=17.385, lng=78.4867, tz_name="Asia/Kolkata")
    lahiri = compute_chart(date(1990, 5, 15), time(10, 30), ayanamsa="lahiri", **kwargs)
    kp = compute_chart(date(1990, 5, 15), time(10, 30), ayanamsa="kp", **kwargs)
    assert lahiri["grahas"]["sun"]["lon"] != kp["grahas"]["sun"]["lon"]
    # KP ayanamsa differs from Lahiri by a few arc-minutes only.
    diff = abs(lahiri["ayanamsa_value"] - kp["ayanamsa_value"])
    assert 0.0 < diff < 0.3


def test_pre_1900_birth_computes():
    # Gandhi's birth data (1869) — exercises the pre-1900 + LMT-era path.
    c = compute_chart(date(1869, 10, 2), time(7, 12),
                      lat=21.6417, lng=69.6293, tz_name="Asia/Kolkata")
    ChartV1.model_validate(c)
    assert len(c["grahas"]) == 9

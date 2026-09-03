"""Varshaphal (Tajika annual chart) — real-ephemeris convergence + invariants."""

from datetime import date, datetime, time, timezone

import pytest

from jyotish.chart import compute_chart
from jyotish.constants import DASHA_YEAR_DAYS, SIGN_LORD
from jyotish.ephemeris import julian_day_ut, sidereal_positions
from jyotish.nakshatra import nakshatra_of
from jyotish.varshaphal import (DEEPTAMSA, compute_saham, mudda_dasha,
                                muntha_sign, tajika_aspects, varsha_pravesh,
                                varshaphal)

BIRTH_UTC = datetime(1990, 5, 15, 5, 0, tzinfo=timezone.utc)  # 10:30 IST
LAT, LNG = 17.385, 78.4867


@pytest.fixture(scope="module")
def birth_jd():
    return julian_day_ut(BIRTH_UTC)


@pytest.fixture(scope="module")
def natal_sun(birth_jd):
    return sidereal_positions(birth_jd)["sun"]["lon"]


@pytest.fixture(scope="module")
def natal_chart():
    return compute_chart(date(1990, 5, 15), time(10, 30),
                         lat=LAT, lng=LNG, tz_name="Asia/Kolkata")


@pytest.fixture(scope="module")
def annual(natal_chart):
    return varshaphal(natal_chart, 34)


# ── varsha_pravesh ───────────────────────────────────────────────────────────

def test_varsha_pravesh_converges(birth_jd, natal_sun):
    vp = varsha_pravesh(natal_sun, birth_jd, 34, LAT, LNG)
    sun_at_pravesh = sidereal_positions(vp["jd"])["sun"]["lon"]
    diff = abs((sun_at_pravesh - natal_sun + 180.0) % 360.0 - 180.0)
    assert diff < 1e-4
    assert vp["year_number"] == 34


def test_varsha_pravesh_near_birthday(birth_jd, natal_sun):
    # The 34th sidereal return lands within ±2 days of the 2024 birthday.
    vp = varsha_pravesh(natal_sun, birth_jd, 34, LAT, LNG)
    target = datetime(2024, 5, 15, 5, 0, tzinfo=timezone.utc)
    pravesh_dt = datetime.fromisoformat(vp["utc"])
    assert abs((pravesh_dt - target).total_seconds()) < 2 * 86400


# ── muntha ───────────────────────────────────────────────────────────────────

def test_muntha_advances_one_sign_per_year():
    assert muntha_sign(3, 0) == 3          # year 0 = natal lagna
    assert muntha_sign(3, 1) == 4          # advances one sign per year
    assert muntha_sign(3, 12) == 3         # full cycle returns
    assert muntha_sign(11, 2) == 1         # wraps past Pisces


def test_muntha_block_in_annual_chart(annual, natal_chart):
    m = annual["muntha"]
    assert m["sign"] == muntha_sign(natal_chart["lagna"]["sign"], 34)
    assert 1 <= m["house"] <= 12
    assert m["lord"] == SIGN_LORD[m["sign"]]


# ── sahams ───────────────────────────────────────────────────────────────────

def test_sahams_in_range_and_complete(annual):
    sahams = annual["sahams"]
    assert set(sahams) == {"punya", "vidya", "yasas", "vivaha", "karma", "roga"}
    for s in sahams.values():
        assert 0.0 <= s["lon"] < 360.0
        assert 0 <= s["sign"] <= 11


def test_saham_correction_rule():
    # C on the B→A arc: B=350, A=10, C=0 → no correction.
    assert compute_saham(10.0, 350.0, 0.0) == pytest.approx(20.0)
    # C NOT on the B→A arc: B=350, A=10, C=100 → +30°.
    assert compute_saham(10.0, 350.0, 100.0) == pytest.approx(150.0)


# ── mudda dasha ──────────────────────────────────────────────────────────────

def test_mudda_spans_and_seed(annual):
    md = annual["mudda_dasha"]
    total = sum(p["end_jd"] - p["start_jd"] for p in md["periods"])
    assert total == pytest.approx(DASHA_YEAR_DAYS, abs=1e-6)
    moon_lon = annual["grahas"]["moon"]["lon"]
    assert md["periods"][0]["lord"] == nakshatra_of(moon_lon)["lord"]
    assert md["periods"][0]["start_jd"] == pytest.approx(annual["varsha_pravesh"]["jd"])


def test_mudda_antardashas_tile_period():
    md = mudda_dasha(annual_moon_lon=100.0, pravesh_jd=2451545.0)
    for p in md["periods"]:
        assert p["antardashas"][0]["lord"] == p["lord"]
        assert p["antardashas"][-1]["end_jd"] == pytest.approx(p["end_jd"], abs=1e-6)


# ── tajika aspects ───────────────────────────────────────────────────────────

def test_tajika_aspects_well_formed(annual):
    for asp in annual["tajika_aspects"]:
        assert len(asp["planets"]) == 2
        assert all(p in DEEPTAMSA for p in asp["planets"])
        assert asp["angle"] in (0.0, 60.0, 90.0, 120.0, 180.0)
        assert asp["type"] in ("ithasala", "ishrafa")
        max_orb = (DEEPTAMSA[asp["planets"][0]] + DEEPTAMSA[asp["planets"][1]]) / 2
        assert 0.0 <= asp["orb"] <= max_orb


def test_tajika_aspects_synthetic_ithasala():
    # Moon 5° behind Mars and faster → applying trine somewhere is closing.
    positions = {p: {"lon": 0.0, "speed": 0.1, "retrograde": False} for p in DEEPTAMSA}
    positions["mars"] = {"lon": 100.0, "speed": 0.5, "retrograde": False}
    positions["moon"] = {"lon": 95.0, "speed": 13.0, "retrograde": False}
    out = tajika_aspects(positions)
    pair = next(a for a in out if set(a["planets"]) == {"moon", "mars"})
    assert pair["angle"] == 0.0
    assert pair["type"] == "ithasala"


# ── full varshaphal ──────────────────────────────────────────────────────────

def test_varshaphal_has_all_blocks(annual):
    for key in ("varsha_pravesh", "lagna", "grahas", "muntha", "year_lord",
                "sahams", "mudda_dasha", "tajika_aspects", "disclaimer"):
        assert key in annual
    assert annual["year_number"] == 34
    assert len(annual["grahas"]) == 9
    assert all(1 <= g["house"] <= 12 for g in annual["grahas"].values())


def test_year_lord_is_a_candidate(annual):
    yl = annual["year_lord"]
    assert yl["planet"] in DEEPTAMSA or yl["planet"] in ("moon", "sun")
    assert yl["planet"] in {c["planet"] for c in yl["candidates"]}
    assert len(yl["candidates"]) == 4  # tri-rashi pati skipped (documented)

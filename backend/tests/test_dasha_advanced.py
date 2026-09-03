"""Kalachakra, Narayana, and year-length Vimshottari — pure unit tests."""

import pytest

from jyotish.constants import DASHA_YEAR_DAYS, DASHA_YEARS
from jyotish.dasha_advanced import (
    KALACHAKRA_YEARS,
    is_savya_nakshatra,
    kalachakra,
    kalachakra_sequence,
    narayana_dasha,
    narayana_progression,
    narayana_sign_lord,
    vimshottari_with_year,
)
from jyotish.nakshatra import PADA_SPAN, SPAN

JD0 = 2451545.0  # J2000 anchor, arbitrary for synthetic tests


# ── Kalachakra ───────────────────────────────────────────────────────────────

def test_kalachakra_savya_apasavya_grouping():
    # Alternates every three nakshatras starting savya at Ashwini.
    assert is_savya_nakshatra(0)      # Ashwini
    assert is_savya_nakshatra(2)      # Krittika
    assert not is_savya_nakshatra(3)  # Rohini
    assert not is_savya_nakshatra(5)  # Ardra
    assert is_savya_nakshatra(6)      # Punarvasu
    assert is_savya_nakshatra(26)     # Revati (group 24-26, savya)


def test_kalachakra_savya_pada1_sequence_and_paramayus():
    d = kalachakra(moon_lon=0.0, birth_jd_ut=JD0)  # Ashwini pada 1, savya
    assert d["savya"] is True
    assert d["pada"] == 1
    assert d["sequence_signs"] == [0, 1, 2, 3, 4, 5, 6, 7, 8]  # Aries..Sag
    assert d["years"] == [7, 16, 9, 21, 5, 9, 16, 7, 10]
    assert d["paramayus"] == 100
    assert d["deha"] == "Mesha"
    assert d["jeeva"] == "Dhanu"


def test_kalachakra_paramayus_equals_sum_of_sequence_years():
    for lon in [0.0, 5.0, 41.0, 100.0, 200.0, 359.0]:
        d = kalachakra(moon_lon=lon, birth_jd_ut=JD0)
        assert d["paramayus"] == sum(d["years"])
        assert d["years"] == [KALACHAKRA_YEARS[s] for s in d["sequence_signs"]]
        # Mahadashas span exactly one paramayus cycle.
        span = d["mahadashas"][-1]["end_jd"] - d["mahadashas"][0]["start_jd"]
        assert span == pytest.approx(d["paramayus"] * DASHA_YEAR_DAYS, rel=1e-9)


def test_kalachakra_savya_pada2_continues_walk_from_capricorn():
    # Moon in Ashwini pada 2 → savya walk continues at sign index 9.
    d = kalachakra(moon_lon=PADA_SPAN * 1.5, birth_jd_ut=JD0)
    assert d["pada"] == 2
    assert d["sequence_signs"] == [9, 10, 11, 0, 1, 2, 3, 4, 5]
    assert d["paramayus"] == 85


def test_kalachakra_apasavya_pada1_is_reversed_walk():
    # Rohini (nak 3) is apasavya: pada 1 runs Pisces backward.
    d = kalachakra(moon_lon=3 * SPAN + 0.01, birth_jd_ut=JD0)
    assert d["savya"] is False
    assert d["sequence_signs"] == [11, 10, 9, 8, 7, 6, 5, 4, 3]
    assert d["paramayus"] == 86
    assert d["deha"] == "Meena"
    assert d["jeeva"] == "Karka"


def test_kalachakra_balance_full_at_pada_start():
    d = kalachakra(moon_lon=0.0, birth_jd_ut=JD0)
    assert d["balance_years"] == pytest.approx(d["paramayus"])
    assert d["mahadashas"][0]["start_jd"] == pytest.approx(JD0)


def test_kalachakra_balance_mid_pada_backdates_start():
    # Halfway through the pada → half the paramayus consumed.
    d = kalachakra(moon_lon=PADA_SPAN / 2.0, birth_jd_ut=JD0)
    assert d["paramayus"] == 100
    assert d["balance_years"] == pytest.approx(50.0)
    assert d["mahadashas"][0]["start_jd"] == pytest.approx(
        JD0 - 50.0 * DASHA_YEAR_DAYS)


def test_kalachakra_gati_annotations():
    savya = kalachakra(moon_lon=0.0, birth_jd_ut=JD0)
    assert savya["mahadashas"][0]["gati"] is None
    assert all(m["gati"] == "krama" for m in savya["mahadashas"][1:])
    apas = kalachakra(moon_lon=3 * SPAN + 0.01, birth_jd_ut=JD0)
    # Reverse (-1) steps are labelled markati (monkey walk).
    assert all(m["gati"] == "markati" for m in apas["mahadashas"][1:])
    # Sequence helper agrees with the full computation.
    assert kalachakra_sequence(0, 1) == savya["sequence_signs"]


# ── Narayana ─────────────────────────────────────────────────────────────────

def test_narayana_movable_progression_forward():
    # Aries lagna, Mars in Aries → Aries stronger than Libra; odd sign → forward.
    pos = {"mars": {"lon": 10.0}, "sun": {"lon": 130.0}}
    d = narayana_dasha(0, pos, JD0)
    assert d["start_sign"] == 0
    assert d["forward"] is True
    assert d["sequence_signs"] == list(range(12))
    # Mars (lord) in own sign → 12 years for the Aries maha.
    assert d["mahadashas"][0]["years"] == 12


def test_narayana_fixed_progression_every_sixth():
    # Leo lagna, Sun in Leo → Leo stronger; fixed odd sign → 1st,6th,11th...
    pos = {"sun": {"lon": 125.0}}
    d = narayana_dasha(4, pos, JD0)
    assert d["start_sign"] == 4
    assert d["sequence_signs"] == [4, 9, 2, 7, 0, 5, 10, 3, 8, 1, 6, 11]


def test_narayana_dual_progression_trines_then_shift():
    # Gemini lagna, Mercury in Gemini → Gemini stronger; dual odd sign.
    pos = {"mercury": {"lon": 70.0}}
    d = narayana_dasha(2, pos, JD0)
    assert d["sequence_signs"] == [2, 6, 10, 3, 7, 11, 4, 8, 0, 5, 9, 1]


def test_narayana_even_start_sign_reversed():
    # Taurus lagna, Venus in Taurus → Taurus stronger; even sign → reversed.
    pos = {"venus": {"lon": 40.0}}
    d = narayana_dasha(1, pos, JD0)
    assert d["forward"] is False
    # Fixed reversed: 1st, then 6th counted backward → Sagittarius (8).
    assert d["sequence_signs"][:3] == [1, 8, 3]
    assert narayana_progression(1, forward=False) == d["sequence_signs"]


def test_narayana_years_counting():
    from jyotish.dasha_advanced import _narayana_years
    # Odd sign, forward: Aries → lord Mars in Leo = 5th sign → 4 years.
    assert _narayana_years(0, {"mars": {"lon": 135.0}}) == 4
    # Even sign, backward: Taurus → Venus in Capricorn = 5 back → 4 years.
    assert _narayana_years(1, {"venus": {"lon": 285.0}}) == 4
    # Lord in own sign → 12.
    assert _narayana_years(0, {"mars": {"lon": 5.0}}) == 12


def test_narayana_scorpio_colord_rule():
    # Mars sits IN Scorpio → the OTHER co-lord (Ketu) is used.
    pos = {"mars": {"lon": 220.0}, "ketu": {"lon": 100.0}}
    assert narayana_sign_lord(7, pos) == "ketu"
    # Both outside: higher degree-in-sign wins (Ketu 20° > Mars 15°).
    pos2 = {"mars": {"lon": 135.0}, "ketu": {"lon": 110.0}}
    assert narayana_sign_lord(7, pos2) == "ketu"
    pos3 = {"mars": {"lon": 145.0}, "ketu": {"lon": 110.0}}
    assert narayana_sign_lord(7, pos3) == "mars"
    # Only one co-lord placed → it is used; ordinary signs → classical lord.
    assert narayana_sign_lord(7, {"mars": {"lon": 10.0}}) == "mars"
    assert narayana_sign_lord(0, {"mars": {"lon": 10.0}}) == "mars"


def test_narayana_antardashas_walk_on_from_next_sign():
    pos = {"mars": {"lon": 10.0}}
    d = narayana_dasha(0, pos, JD0)
    maha = d["mahadashas"][0]
    antars = maha["antardashas"]
    assert len(antars) == 12
    assert antars[0]["sign"] == d["sequence_signs"][1]
    assert antars[-1]["sign"] == maha["sign"]
    length = maha["end_jd"] - maha["start_jd"]
    for a in antars:
        assert a["end_jd"] - a["start_jd"] == pytest.approx(length / 12.0)


# ── Vimshottari year-length option ───────────────────────────────────────────

def test_vimshottari_year_length_scales_dates_proportionally():
    v365 = vimshottari_with_year(0.0, JD0)               # default 365.25
    v360 = vimshottari_with_year(0.0, JD0, year_days=360.0)
    assert v365["year_days"] == 365.25
    assert v360["year_days"] == 360.0
    # Same lords/years, same balance in YEARS...
    assert [m["lord"] for m in v365["mahadashas"]] == \
           [m["lord"] for m in v360["mahadashas"]]
    assert v365["balance_at_birth_years"] == v360["balance_at_birth_years"]
    # ...but every period's day-span scales by 360/365.25.
    for a, b in zip(v365["mahadashas"], v360["mahadashas"]):
        la = a["end_jd"] - a["start_jd"]
        lb = b["end_jd"] - b["start_jd"]
        assert lb == pytest.approx(la * 360.0 / 365.25, rel=1e-12)
        assert la == pytest.approx(DASHA_YEARS[a["lord"]] * DASHA_YEAR_DAYS)


def test_vimshottari_with_year_matches_savana_arithmetic():
    # Moon at Ashwini start → Ketu maha begins at birth; 7y × 360d = 2520d.
    v = vimshottari_with_year(0.0, JD0, year_days=360.0)
    first = v["mahadashas"][0]
    assert first["lord"] == "ketu"
    assert first["start_jd"] == pytest.approx(JD0)
    assert first["end_jd"] - first["start_jd"] == pytest.approx(7 * 360.0)
    assert len(first["antardashas"]) == 9

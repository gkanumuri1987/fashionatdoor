"""Jaimini module unit tests — synthetic longitudes/signs, no ephemeris."""

import pytest

from jyotish import varga
from jyotish.jaimini import (KARAKA_ORDER, arudha_pada, arudha_padas,
                             chara_dasha, chara_karakas, ishta_devata,
                             karakamsa, rasi_drishti)

JD0 = 2451545.0  # J2000 — arbitrary anchor for synthetic tests


def _pos(**lons):
    return {g: {"lon": lon} for g, lon in lons.items()}


# ── Chara karakas ────────────────────────────────────────────────────────────

def test_karaka_ranking_descending_degree():
    # Degrees in sign: sun 29 > moon 27 > mars 25 > mercury 23 > jupiter 21
    # > venus 19 > saturn 17 > rahu effective 30-15=15.
    positions = _pos(sun=29.0, moon=57.0, mars=85.0, mercury=113.0,
                     jupiter=141.0, venus=169.0, saturn=197.0, rahu=225.0)
    result = chara_karakas(positions)
    assert result["scheme"] == "8"
    order = [result["karakas"][k]["graha"] for k in KARAKA_ORDER]
    assert order == ["sun", "moon", "mars", "mercury", "jupiter",
                     "venus", "saturn", "rahu"]
    assert result["karakas"]["AK"]["deg_in_sign"] == pytest.approx(29.0)
    assert [r["karaka"] for r in result["ranked"]] == KARAKA_ORDER


def test_karaka_rahu_reversal():
    # Rahu at 2° in sign → effective 28°, beating everyone else → AK.
    positions = _pos(sun=25.0, moon=52.0, mars=80.0, mercury=108.0,
                     jupiter=136.0, venus=164.0, saturn=192.0, rahu=32.0)
    result = chara_karakas(positions)
    assert result["karakas"]["AK"]["graha"] == "rahu"
    # Reported degree stays the actual degree in sign, not the effective one.
    assert result["karakas"]["AK"]["deg_in_sign"] == pytest.approx(2.0)
    assert result["karakas"]["AmK"]["graha"] == "sun"  # 25° is next


# ── Arudha padas ─────────────────────────────────────────────────────────────

def test_arudha_basic_count():
    # Lagna Aries, house 1; Mars (lord) in Gemini: Aries→Gemini is 3 signs,
    # so the arudha is the 3rd from Gemini = Leo.
    assert arudha_pada(1, 0, {"mars": 2}) == 4


def test_arudha_same_sign_exception():
    # Lord in the house's own sign → arudha would be the house itself →
    # take the 10th from it: Aries → Capricorn.
    assert arudha_pada(1, 0, {"mars": 0}) == 9


def test_arudha_seventh_exception():
    # Lagna Aries, Mars in Cancer: arudha computes to Libra (7th from Aries)
    # → take the 10th from Libra = Cancer.
    assert arudha_pada(1, 0, {"mars": 3}) == 3


def test_upapada_is_arudha_of_12th():
    graha_signs = {"sun": 4, "moon": 1, "mars": 6, "mercury": 2,
                   "jupiter": 10, "venus": 8, "saturn": 3}
    padas = arudha_padas(0, graha_signs)
    assert padas["UL"] == padas["A12"] == arudha_pada(12, 0, graha_signs)
    assert padas["AL"] == padas["A1"]
    assert set(f"A{h}" for h in range(1, 13)) <= set(padas)


# ── Karakamsa & Ishta Devata ─────────────────────────────────────────────────

def test_karakamsa_is_ak_navamsa():
    positions = _pos(jupiter=100.0)  # Cancer 10° → 4th navamsa → Libra
    result = karakamsa("jupiter", positions)
    assert result["sign"] == varga.d9(100.0) == 6
    assert result["sign_name"] == "Libra"


def test_ishta_devata_occupant():
    # Karakamsa Virgo (5) → 12th from it is Leo (4); Jupiter occupies Leo.
    result = ishta_devata(5, {"jupiter": 4, "moon": 0, "sun": 7})
    assert result["house_examined"] == 4
    assert result["indicator_graha"] == "jupiter"
    assert result["basis"] == "occupant"
    assert result["deity"] == "Vishnu/Dattatreya"


def test_ishta_devata_lord_fallback():
    # Karakamsa Aries (0) → 12th is Pisces (11); empty → its lord Jupiter.
    result = ishta_devata(0, {"sun": 0, "moon": 4, "mars": 7})
    assert result["house_examined"] == 11
    assert result["indicator_graha"] == "jupiter"
    assert result["basis"] == "lord"
    assert result["deity"] == "Vishnu/Dattatreya"


# ── Rasi drishti ─────────────────────────────────────────────────────────────

def test_rasi_drishti_movable():
    # Aries (movable) aspects Leo, Scorpio, Aquarius — not adjacent Taurus.
    assert rasi_drishti(0, 4) and rasi_drishti(0, 7) and rasi_drishti(0, 10)
    assert not rasi_drishti(0, 1)
    assert not rasi_drishti(0, 2)   # never a dual sign
    assert not rasi_drishti(0, 0)   # no self-aspect


def test_rasi_drishti_fixed():
    # Taurus (fixed) aspects Cancer, Libra, Capricorn — not adjacent Aries.
    assert rasi_drishti(1, 3) and rasi_drishti(1, 6) and rasi_drishti(1, 9)
    assert not rasi_drishti(1, 0)
    assert not rasi_drishti(1, 4)   # never another fixed sign


def test_rasi_drishti_dual_and_mutuality():
    # Gemini (dual) aspects the other duals: Virgo, Sagittarius, Pisces.
    assert rasi_drishti(2, 5) and rasi_drishti(2, 8) and rasi_drishti(2, 11)
    assert not rasi_drishti(2, 0) and not rasi_drishti(2, 4)
    # Jaimini aspects are mutual: spot-check symmetry over all pairs.
    for a in range(12):
        for b in range(12):
            assert rasi_drishti(a, b) == rasi_drishti(b, a)


# ── Chara dasha ──────────────────────────────────────────────────────────────

_GRAHA_SIGNS = {"sun": 4, "moon": 1, "mars": 6, "mercury": 2,
                "jupiter": 10, "venus": 8, "saturn": 3}


def test_chara_dasha_twelve_contiguous_periods():
    periods = chara_dasha(0, _GRAHA_SIGNS, JD0)
    assert len(periods) == 12
    assert sum(p["years"] for p in periods) > 0
    assert all(1 <= p["years"] <= 12 for p in periods)
    for prev, nxt in zip(periods, periods[1:]):
        assert prev["end"] == nxt["start"]
    assert periods[0]["start"] == "2000-01-01T12:00:00+00:00"


def test_chara_dasha_direction_by_lagna_parity():
    # Odd lagna sign (Aries) → forward: Aries, Taurus, Gemini...
    forward = chara_dasha(0, _GRAHA_SIGNS, JD0)
    assert [p["sign"] for p in forward[:3]] == [0, 1, 2]
    # Even lagna sign (Taurus) → backward: Taurus, Aries, Pisces...
    backward = chara_dasha(1, _GRAHA_SIGNS, JD0)
    assert [p["sign"] for p in backward[:3]] == [1, 0, 11]


def test_chara_dasha_lord_in_own_sign_is_12_years():
    graha_signs = dict(_GRAHA_SIGNS, mars=0)  # Mars in Aries, lagna Aries
    periods = chara_dasha(0, graha_signs, JD0)
    assert periods[0]["sign"] == 0
    assert periods[0]["years"] == 12


def test_chara_dasha_span_counts():
    # Gemini (odd): Mercury in Libra → forward count 5 → 4 years.
    periods = chara_dasha(2, dict(_GRAHA_SIGNS, mercury=6), JD0)
    gemini = next(p for p in periods if p["sign"] == 2)
    assert gemini["years"] == 4
    # Taurus (even): Venus in Aquarius (10) → backward count (1-10)%12+1=4 → 3y.
    taurus_periods = chara_dasha(1, dict(_GRAHA_SIGNS, venus=10), JD0)
    taurus = next(p for p in taurus_periods if p["sign"] == 1)
    assert taurus["years"] == 3

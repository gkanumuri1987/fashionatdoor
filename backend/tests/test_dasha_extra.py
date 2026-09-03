"""Yogini, Ashtottari, and Vimshottari deep-level arithmetic — pure unit tests."""

import pytest

from jyotish.constants import DASHA_ORDER, DASHA_YEARS, DASHA_YEAR_DAYS, NAKSHATRAS
from jyotish.dasha_extra import (
    ASHTOTTARI_NAK_LORD,
    ASHTOTTARI_ORDER,
    ASHTOTTARI_TOTAL_YEARS,
    ASHTOTTARI_YEARS,
    YOGINI_ORDER,
    YOGINI_TOTAL_YEARS,
    _jd_to_iso,
    ashtottari_dasha,
    vimshottari_levels,
    yogini_dasha,
)

JD0 = 2451545.0  # J2000 anchor, arbitrary for synthetic tests
SPAN = 360.0 / 27.0


# ── Yogini ───────────────────────────────────────────────────────────────────

def test_yogini_cycle_totals_36_years():
    assert sum(y for _, _, y in YOGINI_ORDER) == YOGINI_TOTAL_YEARS
    d = yogini_dasha(moon_lon=0.0, birth_jd_ut=JD0)
    one_cycle = d["mahadashas"][:8]
    span_days = one_cycle[-1]["end_jd"] - one_cycle[0]["start_jd"]
    assert span_days == pytest.approx(36 * DASHA_YEAR_DAYS, abs=1e-6)
    assert len(d["mahadashas"]) == 24  # 3 full cycles


def test_yogini_start_ashwini_is_bhramari_mars():
    # Ashwini (nak 0) → (0+3)%8 = 3 → Bhramari / Mars, 4 years.
    d = yogini_dasha(moon_lon=0.0, birth_jd_ut=JD0)
    first = d["mahadashas"][0]
    assert first["yogini"] == "Bhramari"
    assert first["lord"] == "mars"
    assert first["years"] == 4


def test_yogini_start_rohini_is_siddha_venus():
    # Rohini (nak 3) → (3+3)%8 = 6 → Siddha / Venus.
    d = yogini_dasha(moon_lon=3 * SPAN + 1.0, birth_jd_ut=JD0)
    assert d["mahadashas"][0]["yogini"] == "Siddha"
    assert d["mahadashas"][0]["lord"] == "venus"


def test_yogini_balance_full_at_nakshatra_start():
    # At the very start of Ashwini the whole 4y Bhramari period remains.
    d = yogini_dasha(moon_lon=0.0, birth_jd_ut=JD0)
    assert d["balance_at_birth_years"] == pytest.approx(4.0)
    assert d["mahadashas"][0]["start_jd"] == pytest.approx(JD0)
    # Halfway through Ashwini → half the period remains, start back-dated 2y.
    h = yogini_dasha(moon_lon=SPAN / 2.0, birth_jd_ut=JD0)
    assert h["balance_at_birth_years"] == pytest.approx(2.0)
    assert h["mahadashas"][0]["start_jd"] == pytest.approx(JD0 - 2.0 * DASHA_YEAR_DAYS)


def test_yogini_antars_tile_the_maha():
    d = yogini_dasha(moon_lon=50.0, birth_jd_ut=JD0)
    for maha in d["mahadashas"][:8]:
        antars = maha["antardashas"]
        assert len(antars) == 8
        assert antars[0]["yogini"] == maha["yogini"]  # sub-cycle seeds from maha
        assert antars[0]["start_jd"] == pytest.approx(maha["start_jd"])
        assert antars[-1]["end_jd"] == pytest.approx(maha["end_jd"])
        for a, b in zip(antars, antars[1:]):
            assert a["end_jd"] == pytest.approx(b["start_jd"])


# ── Ashtottari ───────────────────────────────────────────────────────────────

def test_ashtottari_table_covers_27_with_stated_groups():
    assert len(ASHTOTTARI_NAK_LORD) == 27
    # Group sizes 3,4,3,4,3,4,3,3 from Krittika → per-lord nakshatra counts.
    counts = {lord: ASHTOTTARI_NAK_LORD.count(lord) for lord in ASHTOTTARI_ORDER}
    assert counts == {"sun": 3, "moon": 4, "mars": 3, "mercury": 4,
                      "saturn": 3, "jupiter": 4, "rahu": 3, "venus": 3}
    idx = {name: i for i, name in enumerate(NAKSHATRAS)}
    assert ASHTOTTARI_NAK_LORD[idx["Krittika"]] == "sun"
    assert ASHTOTTARI_NAK_LORD[idx["Ashwini"]] == "venus"
    assert ASHTOTTARI_NAK_LORD[idx["Revati"]] == "venus"
    assert ASHTOTTARI_NAK_LORD[idx["Magha"]] == "mars"
    assert ASHTOTTARI_NAK_LORD[idx["Ardra"]] == "moon"
    assert ASHTOTTARI_NAK_LORD[idx["Anuradha"]] == "saturn"


def test_ashtottari_total_is_108_years():
    assert sum(ASHTOTTARI_YEARS.values()) == ASHTOTTARI_TOTAL_YEARS
    d = ashtottari_dasha(moon_lon=2 * SPAN, sun_lon=0.0, birth_jd_ut=JD0)
    span_days = d["mahadashas"][-1]["end_jd"] - d["mahadashas"][0]["start_jd"]
    assert span_days == pytest.approx(108 * DASHA_YEAR_DAYS, abs=1e-6)
    assert len(d["mahadashas"]) == 8


def test_ashtottari_balance_full_at_group_start():
    # Moon at 0° Krittika = the very start of the Sun group → full 6y balance.
    d = ashtottari_dasha(moon_lon=2 * SPAN, sun_lon=0.0, birth_jd_ut=JD0)
    assert d["moon_nakshatra"] == "Krittika"
    assert d["mahadashas"][0]["lord"] == "sun"
    assert d["balance_at_birth_years"] == pytest.approx(6.0)
    assert d["mahadashas"][0]["start_jd"] == pytest.approx(JD0)


def test_ashtottari_group_fraction_balance():
    # Moon at the start of Rohini = 1 nakshatra into the 3-nak Sun group
    # → 1/3 elapsed → balance = 2/3 × 6y = 4y.
    d = ashtottari_dasha(moon_lon=3 * SPAN, sun_lon=0.0, birth_jd_ut=JD0)
    assert d["mahadashas"][0]["lord"] == "sun"
    assert d["balance_at_birth_years"] == pytest.approx(4.0)


def test_ashtottari_antars_tile_and_seed_from_maha():
    d = ashtottari_dasha(moon_lon=100.0, sun_lon=0.0, birth_jd_ut=JD0)
    for maha in d["mahadashas"]:
        antars = maha["antardashas"]
        assert len(antars) == 8
        assert antars[0]["lord"] == maha["lord"]
        assert antars[0]["start_jd"] == pytest.approx(maha["start_jd"])
        assert antars[-1]["end_jd"] == pytest.approx(maha["end_jd"])
        for a, b in zip(antars, antars[1:]):
            assert a["end_jd"] == pytest.approx(b["start_jd"])


def test_ashtottari_applicability_flag():
    # Rahu 4th from lagna lord (quadrant) → applicable.
    d = ashtottari_dasha(0.0, 0.0, JD0, rahu_sign=3, lagna_lord_sign=0)
    assert d["applicability"]["applicable"] is True
    # 5th (trine, offset 4) → applicable.
    d = ashtottari_dasha(0.0, 0.0, JD0, rahu_sign=4, lagna_lord_sign=0)
    assert d["applicability"]["applicable"] is True
    # 2nd (offset 1) → not applicable.
    d = ashtottari_dasha(0.0, 0.0, JD0, rahu_sign=1, lagna_lord_sign=0)
    assert d["applicability"]["applicable"] is False
    # Missing inputs → null.
    d = ashtottari_dasha(0.0, 0.0, JD0)
    assert d["applicability"]["applicable"] is None
    assert "condition" in d["applicability"]


# ── Vimshottari deep levels ──────────────────────────────────────────────────

def _synthetic_antar(lord="sun", years=6.0):
    return {"lord": lord, "start_jd": JD0, "end_jd": JD0 + years * DASHA_YEAR_DAYS}


def test_levels_sookshmas_seed_from_antar_lord_and_tile():
    antar = _synthetic_antar("mars", 7.0)
    levels = vimshottari_levels(antar)
    sooks = levels["sookshmas"]
    assert len(sooks) == 9
    assert sooks[0]["lord"] == "mars"
    idx = DASHA_ORDER.index("mars")
    assert [s["lord"] for s in sooks] == [DASHA_ORDER[(idx + i) % 9] for i in range(9)]
    assert sooks[0]["start_jd"] == pytest.approx(antar["start_jd"])
    assert sooks[-1]["end_jd"] == pytest.approx(antar["end_jd"])
    for a, b in zip(sooks, sooks[1:]):
        assert a["end_jd"] == pytest.approx(b["start_jd"])
    # Proportional lengths: first sookshma = antar_len × mars_years / 120.
    antar_len = antar["end_jd"] - antar["start_jd"]
    assert sooks[0]["end_jd"] - sooks[0]["start_jd"] == pytest.approx(
        antar_len * DASHA_YEARS["mars"] / 120.0)


def test_levels_pranas_tile_their_sookshma():
    levels = vimshottari_levels(_synthetic_antar("venus", 20.0), depth=2)
    for s in levels["sookshmas"]:
        pranas = s["pranas"]
        assert len(pranas) == 9
        assert pranas[0]["lord"] == s["lord"]  # prana run seeds from sookshma lord
        assert pranas[0]["start_jd"] == pytest.approx(s["start_jd"])
        assert pranas[-1]["end_jd"] == pytest.approx(s["end_jd"])
        for a, b in zip(pranas, pranas[1:]):
            assert a["end_jd"] == pytest.approx(b["start_jd"])


def test_levels_depth_1_omits_pranas():
    levels = vimshottari_levels(_synthetic_antar(), depth=1)
    assert all("pranas" not in s for s in levels["sookshmas"])


# ── ISO conversion ───────────────────────────────────────────────────────────

def test_jd_to_iso_j2000_anchor():
    assert _jd_to_iso(2451545.0).startswith("2000-01-01T12:00:00")
    assert _jd_to_iso(2451545.5).startswith("2000-01-02T00:00:00")
    assert _jd_to_iso(2451544.0).startswith("1999-12-31T12:00:00")

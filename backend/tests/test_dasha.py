"""Vimshottari arithmetic — pure unit tests with synthetic moon longitudes."""

import pytest

from jyotish.constants import DASHA_ORDER, DASHA_YEARS, DASHA_YEAR_DAYS
from jyotish.dasha import current_period, pratyantardashas, vimshottari

JD0 = 2451545.0  # J2000 — arbitrary anchor for synthetic tests


def test_first_cycle_is_120_years():
    d = vimshottari(moon_lon=100.0, birth_jd_ut=JD0)
    # First full vimshottari cycle = 9 mahadashas = 120 years.
    first_cycle = d["mahadashas"][:9]
    total_days = first_cycle[-1]["end_jd"] - first_cycle[0]["start_jd"]
    assert total_days == pytest.approx(120 * DASHA_YEAR_DAYS, abs=1e-6)


def test_two_cycles_generated_by_default():
    d = vimshottari(moon_lon=100.0, birth_jd_ut=JD0)
    assert len(d["mahadashas"]) == 18  # two repeating cycles ≈ 240 years
    # The cycle repeats: maha 9 has the same lord as maha 0.
    assert d["mahadashas"][9]["lord"] == d["mahadashas"][0]["lord"]


def test_current_period_resolves_for_elderly_and_future():
    from jyotish.dasha import current_period
    d = vimshottari(moon_lon=0.0, birth_jd_ut=JD0)  # 0° Aries → full 7y Ketu balance
    # 100 years after birth would fall outside a single 120y-from-back-dated-start
    # sequence for many charts; with two cycles it always resolves.
    at = JD0 + 100 * DASHA_YEAR_DAYS
    assert current_period(d, at) is not None


def test_ashwini_start_is_ketu():
    # Moon at 0° Aries = start of Ashwini → full 7-year Ketu balance.
    d = vimshottari(moon_lon=0.0, birth_jd_ut=JD0)
    assert d["moon_nakshatra"] == "Ashwini"
    assert d["mahadashas"][0]["lord"] == "ketu"
    assert d["balance_at_birth_years"] == pytest.approx(7.0)
    assert d["mahadashas"][0]["start_jd"] == pytest.approx(JD0)


def test_half_elapsed_nakshatra_balance():
    # Moon at 6°40' Aries = exactly half of Ashwini → 3.5y Ketu balance,
    # and the maha started 3.5y before birth.
    d = vimshottari(moon_lon=360.0 / 27.0 / 2.0, birth_jd_ut=JD0)
    assert d["balance_at_birth_years"] == pytest.approx(3.5)
    assert d["mahadashas"][0]["start_jd"] == pytest.approx(JD0 - 3.5 * DASHA_YEAR_DAYS)


def test_order_follows_vimshottari_cycle():
    # Moon in Rohini (4th nakshatra, lord Moon) → sequence starts moon, mars, rahu...
    rohini_mid = 3 * (360.0 / 27.0) + 5.0
    d = vimshottari(moon_lon=rohini_mid, birth_jd_ut=JD0)
    lords = [m["lord"] for m in d["mahadashas"][:9]]  # first cycle
    start = DASHA_ORDER.index("moon")
    assert lords == [DASHA_ORDER[(start + i) % 9] for i in range(9)]


def test_antardasha_proportions():
    d = vimshottari(moon_lon=0.0, birth_jd_ut=JD0)
    ketu_maha = d["mahadashas"][0]
    antars = ketu_maha["antardashas"]
    assert antars[0]["lord"] == "ketu"          # first antar = maha lord itself
    maha_days = ketu_maha["end_jd"] - ketu_maha["start_jd"]
    for a in antars:
        expected = maha_days * DASHA_YEARS[a["lord"]] / 120.0
        assert (a["end_jd"] - a["start_jd"]) == pytest.approx(expected, rel=1e-9)
    # Antars tile the maha exactly.
    assert antars[-1]["end_jd"] == pytest.approx(ketu_maha["end_jd"], abs=1e-6)


def test_pratyantar_tiles_antar():
    d = vimshottari(moon_lon=0.0, birth_jd_ut=JD0)
    antar = d["mahadashas"][0]["antardashas"][1]  # ketu-venus
    prats = pratyantardashas("ketu", antar)
    assert prats[0]["lord"] == "venus"
    assert prats[-1]["end_jd"] == pytest.approx(antar["end_jd"], abs=1e-6)


def test_current_period_lookup():
    d = vimshottari(moon_lon=0.0, birth_jd_ut=JD0)
    # 10 years after birth: past 7y Ketu → inside Venus maha.
    p = current_period(d, JD0 + 10 * DASHA_YEAR_DAYS)
    assert p is not None and p["maha"] == "venus"
    # Before the sequence begins → None.
    assert current_period(d, JD0 - 8 * DASHA_YEAR_DAYS) is None

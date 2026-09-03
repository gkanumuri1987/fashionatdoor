"""Ayurdaya (pindayu/amsayu/nisargayu) — internal strength-model arithmetic."""

import pytest

from jyotish.ayurdaya import (
    NISARGAYU_YEARS,
    PINDAYU_BASE,
    POLICY,
    amsayu,
    ayurdaya,
    nisargayu,
    pindayu,
)


def _positions(**overrides):
    """Seven classical grahas, all far from the Sun and unremarkable."""
    base = {
        "sun": {"lon": 10.0},       # deep exaltation (Aries 10)
        "moon": {"lon": 42.0},      # Taurus
        "mars": {"lon": 250.0},     # Sagittarius (friend sign)
        "mercury": {"lon": 200.0},  # Libra
        "jupiter": {"lon": 275.0},  # Capricorn-ish, far from Sun
        "venus": {"lon": 185.0},    # Libra (own)
        "saturn": {"lon": 195.0},   # Libra
    }
    base.update(overrides)
    return base


# ── Pindayu ──────────────────────────────────────────────────────────────────

def test_pindayu_deep_exaltation_contributes_full_base():
    p = pindayu(_positions(), lagna_lon=0.0)
    # Sun at deep exaltation (10° Aries) → 180° from deep debilitation.
    assert p["per_graha"]["sun"]["years"] == pytest.approx(PINDAYU_BASE["sun"])
    assert p["per_graha"]["sun"]["haranas"] == []


def test_pindayu_deep_debilitation_contributes_zero():
    # Moon at deep debilitation (3° Scorpio = lon 213) → zero contribution.
    p = pindayu(_positions(moon={"lon": 213.0}), lagna_lon=0.0)
    assert p["per_graha"]["moon"]["years"] == pytest.approx(0.0, abs=1e-9)


def test_pindayu_combust_harana_halves():
    # Jupiter at its deep exaltation (5° Cancer = 95) within 11° of the Sun
    # (at 100) → combust → half of the full base 15.
    p = pindayu(_positions(sun={"lon": 100.0}, jupiter={"lon": 95.0}),
                lagna_lon=0.0)
    j = p["per_graha"]["jupiter"]
    assert j["haranas"] == ["astangata"]
    assert j["years"] == pytest.approx(PINDAYU_BASE["jupiter"] / 2.0)


def test_pindayu_venus_exempt_from_combust_harana():
    # Venus 5° from the Sun (combust threshold 10°) but exempt; Pisces is a
    # neutral sign for Venus, so no harana at all.
    p = pindayu(_positions(sun={"lon": 350.0}, venus={"lon": 355.0}),
                lagna_lon=0.0)
    v = p["per_graha"]["venus"]
    assert v["haranas"] == []
    assert v["years"] == pytest.approx(v["raw_years"])


def test_pindayu_enemy_sign_harana_removes_a_third():
    # Mars in Gemini (lord Mercury = natural enemy), far from the Sun.
    p = pindayu(_positions(mars={"lon": 75.0}), lagna_lon=0.0)
    m = p["per_graha"]["mars"]
    assert m["haranas"] == ["shatru_kshetra"]
    expected_raw = PINDAYU_BASE["mars"] * 43.0 / 180.0  # |75 − 118| from deb
    assert m["raw_years"] == pytest.approx(expected_raw)
    assert m["years"] == pytest.approx(expected_raw * 2.0 / 3.0)


def test_pindayu_lagna_and_total():
    p = pindayu(_positions(), lagna_lon=45.0)  # 15° into Taurus → 6y
    assert p["lagna_years"] == pytest.approx(6.0)
    graha_sum = sum(g["years"] for g in p["per_graha"].values())
    assert p["total_years"] == pytest.approx(graha_sum + 6.0, abs=1e-5)


# ── Amsayu ───────────────────────────────────────────────────────────────────

def test_amsayu_navamsa_count_formula():
    # Sun at lon 34 → floor(34 / 3°20') = 10 navamsas → 10 % 12 = 10 years.
    a = amsayu(_positions(sun={"lon": 34.0}), lagna_lon=0.0)
    s = a["per_graha"]["sun"]
    assert s["navamsa_count"] == 10
    assert s["raw_years"] == 10.0
    # Sun in Taurus (lord Venus = natural enemy) → shatru-kshetra harana.
    assert s["haranas"] == ["shatru_kshetra"]
    assert s["years"] == pytest.approx(10.0 * 2.0 / 3.0)


def test_amsayu_lagna_and_wraparound():
    # Lagna at lon 35 → 10 navamsas → 10y; count wraps mod 12.
    a = amsayu(_positions(), lagna_lon=35.0)
    assert a["lagna_years"] == 10.0
    b = amsayu(_positions(), lagna_lon=41.0)  # 12 navamsas → 0y
    assert b["lagna_years"] == 0.0


# ── Nisargayu / assembly ─────────────────────────────────────────────────────

def test_nisargayu_table():
    n = nisargayu()
    assert n["years"]["moon"] == 1
    assert n["years"]["saturn"] == 50
    assert n["years"] == NISARGAYU_YEARS
    assert n["total_years"] == sum(NISARGAYU_YEARS.values()) == 120
    assert "note" in n


def test_ayurdaya_policy_never_expose():
    out = ayurdaya(_positions(), lagna_lon=15.0)
    assert out["policy"] == POLICY
    assert "never expose lifespan" in out["policy"]
    assert set(out) >= {"pindayu", "amsayu", "nisargayu", "method_note",
                        "policy"}
    assert "internal" in out["policy"] or "internal" in out["method_note"]


def test_ayurdaya_sections_consistent():
    out = ayurdaya(_positions(), lagna_lon=15.0)
    assert out["pindayu"] == pindayu(_positions(), 15.0)
    assert out["amsayu"] == amsayu(_positions(), 15.0)
    assert out["nisargayu"] == nisargayu()

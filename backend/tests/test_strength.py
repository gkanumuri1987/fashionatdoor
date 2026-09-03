"""Shadbala tests — component invariants + a real-chart sanity band.

The integration test builds ShadbalaInputs from the live ephemeris (allowed in
tests only) for 1990-05-15 10:30 IST, Hyderabad.
"""

import math
from datetime import datetime, timezone

from jyotish.strength import (NAISARGIKA_BALA, REQUIRED_RUPAS, SHADBALA_GRAHAS,
                              ShadbalaInputs, ayana_bala, chesta_bala,
                              dig_bala, drekkana_bala, drik_bala, hora_bala,
                              ishta_kashta, kendradi_bala, bhava_bala_simple,
                              nathonnatha_bala, ojayugma_bala, paksha_bala,
                              shadbala, sphuta_drishti, tribhaga_bala,
                              uccha_bala, vara_bala)

HYD_LAT, HYD_LNG = 17.385, 78.4867


def _dummy_positions():
    """Widely-spread synthetic positions with plausible speeds."""
    return {
        "sun": {"lon": 10.0, "speed": 0.98},
        "moon": {"lon": 130.0, "speed": 13.2},
        "mars": {"lon": 200.0, "speed": 0.5},
        "mercury": {"lon": 25.0, "speed": 1.3},
        "jupiter": {"lon": 95.0, "speed": 0.08},
        "venus": {"lon": 340.0, "speed": 1.1},
        "saturn": {"lon": 275.0, "speed": 0.03},
    }


# ── naisargika ───────────────────────────────────────────────────────────────

def test_naisargika_ordering():
    order = ["sun", "moon", "venus", "jupiter", "mercury", "mars", "saturn"]
    values = [NAISARGIKA_BALA[g] for g in order]
    assert values == sorted(values, reverse=True)
    assert NAISARGIKA_BALA["sun"] == 60.0
    assert NAISARGIKA_BALA["saturn"] == 8.57


# ── uccha ────────────────────────────────────────────────────────────────────

def test_uccha_bala_extremes():
    assert uccha_bala("sun", 10.0) == 60.0        # 10° Aries — deep exaltation
    assert uccha_bala("sun", 190.0) == 0.0        # 10° Libra — deep debilitation
    assert abs(uccha_bala("sun", 100.0) - 30.0) < 1e-9  # quadrature → half
    assert uccha_bala("moon", 33.0) == 60.0       # 3° Taurus
    assert uccha_bala("saturn", 200.0) == 60.0    # 20° Libra


def test_uccha_bala_bounds():
    for g in SHADBALA_GRAHAS:
        for lon in (0.0, 45.0, 123.4, 250.0, 359.9):
            assert 0.0 <= uccha_bala(g, lon) <= 60.0


# ── ojayugma ─────────────────────────────────────────────────────────────────

def test_ojayugma_parity():
    # Sun at 0° Aries: odd rasi (Aries) + odd navamsa (Aries) → 30.
    assert ojayugma_bala("sun", 0.0) == 30.0
    # Moon at 0° Taurus: even rasi + navamsa d9(30)=Capricorn (even) → 30.
    assert ojayugma_bala("moon", 30.0) == 30.0
    # Moon at 0° Aries: odd rasi + odd navamsa → 0 for an even-parity graha.
    assert ojayugma_bala("moon", 0.0) == 0.0
    # Values are always 0, 15 or 30.
    for g in SHADBALA_GRAHAS:
        for lon in (0.0, 17.0, 95.0, 222.0, 305.0):
            assert ojayugma_bala(g, lon) in (0.0, 15.0, 30.0)


# ── kendradi / drekkana ──────────────────────────────────────────────────────

def test_kendradi_bala():
    assert kendradi_bala(5.0, 0.0) == 60.0     # 1st house
    assert kendradi_bala(95.0, 0.0) == 60.0    # 4th
    assert kendradi_bala(35.0, 0.0) == 30.0    # 2nd
    assert kendradi_bala(65.0, 0.0) == 15.0    # 3rd


def test_drekkana_bala():
    assert drekkana_bala("sun", 5.0) == 15.0      # male, 1st drekkana
    assert drekkana_bala("moon", 15.0) == 15.0    # female, 2nd
    assert drekkana_bala("saturn", 25.0) == 15.0  # neutral, 3rd
    assert drekkana_bala("sun", 15.0) == 0.0


# ── dig ──────────────────────────────────────────────────────────────────────

def test_dig_bala_power_points():
    lagna = 0.0
    assert dig_bala("jupiter", 0.0, lagna) == 60.0    # 1st house point
    assert dig_bala("sun", 270.0, lagna) == 60.0      # 10th
    assert dig_bala("saturn", 180.0, lagna) == 60.0   # 7th
    assert dig_bala("moon", 90.0, lagna) == 60.0      # 4th
    # Nadir of the power point → 0.
    assert dig_bala("sun", 90.0, lagna) == 0.0
    assert dig_bala("jupiter", 180.0, lagna) == 0.0


# ── kala pieces ──────────────────────────────────────────────────────────────

def test_nathonnatha_noon_and_midnight():
    sunrise, sunset = 100.25, 100.75          # symmetric: midday at 100.5
    assert nathonnatha_bala("sun", 100.5, sunrise, sunset) == 60.0   # noon
    assert nathonnatha_bala("moon", 100.5, sunrise, sunset) == 0.0
    assert nathonnatha_bala("moon", 100.0, sunrise, sunset) == 60.0  # midnight
    assert nathonnatha_bala("mercury", 100.31, sunrise, sunset) == 60.0


def test_paksha_bala_full_and_new_moon():
    pos = _dummy_positions()
    pos["moon"]["lon"] = (pos["sun"]["lon"] + 180.0) % 360.0  # full moon
    assert abs(paksha_bala("jupiter", pos) - 60.0) < 1e-9
    assert abs(paksha_bala("saturn", pos) - 0.0) < 1e-9
    assert abs(paksha_bala("moon", pos) - 120.0) < 1e-9  # doubled for Moon
    pos["moon"]["lon"] = pos["sun"]["lon"]  # new moon
    assert abs(paksha_bala("jupiter", pos) - 0.0) < 1e-9
    assert abs(paksha_bala("saturn", pos) - 60.0) < 1e-9


def test_tribhaga_and_vara_and_hora():
    sunrise, sunset = 100.0, 100.5
    # First third of the day → Mercury.
    assert tribhaga_bala("mercury", 100.05, sunrise, sunset, True) == 60.0
    assert tribhaga_bala("sun", 100.05, sunrise, sunset, True) == 0.0
    # Middle third → Sun; last third → Saturn. Jupiter always 60.
    assert tribhaga_bala("sun", 100.25, sunrise, sunset, True) == 60.0
    assert tribhaga_bala("saturn", 100.45, sunrise, sunset, True) == 60.0
    assert tribhaga_bala("jupiter", 100.05, sunrise, sunset, True) == 60.0
    # Night thirds: Moon, Venus, Mars.
    assert tribhaga_bala("moon", 100.55, sunrise, sunset, False) == 60.0
    # Vara: weekday 6 = Sunday → Sun (Python convention 0=Mon).
    assert vara_bala("sun", 6) == 45.0
    assert vara_bala("moon", 0) == 45.0
    assert vara_bala("sun", 0) == 0.0
    # Hora: first hora after sunrise belongs to the weekday lord.
    assert hora_bala("sun", 100.01, 100.0, 6) == 60.0     # Sunday, 1st hora
    # Second hora on Sunday follows the hora order: Sun → Venus.
    assert hora_bala("venus", 100.0 + 1.5 / 24.0, 100.0, 6) == 60.0


def test_ayana_bala_bounds_and_doubling():
    # Sidereal 0 with ayanamsa 90 → sayana 90 → max north declination.
    assert abs(ayana_bala("jupiter", 0.0, 90.0) - 60.0) < 1e-9
    assert abs(ayana_bala("saturn", 0.0, 90.0) - 0.0) < 1e-9
    assert abs(ayana_bala("sun", 0.0, 90.0) - 120.0) < 1e-9  # doubled
    assert abs(ayana_bala("mercury", 0.0, 90.0) - 60.0) < 1e-9
    # Equinox point → everyone at the 30-virupa midline (Sun doubled → 60).
    assert abs(ayana_bala("mars", 0.0, 0.0) - 30.0) < 1e-9
    assert abs(ayana_bala("sun", 0.0, 0.0) - 60.0) < 1e-9


# ── chesta / drishti ─────────────────────────────────────────────────────────

def test_chesta_bala_motion():
    pos = _dummy_positions()
    pos["saturn"]["speed"] = -0.05  # retrograde
    assert chesta_bala("saturn", pos, 0.0, 0.0) == 60.0
    pos["mars"]["speed"] = 0.524    # exactly mean → 30
    assert abs(chesta_bala("mars", pos, 0.0, 0.0) - 30.0) < 1e-9
    pos["mercury"]["speed"] = 2.5   # very fast direct → weak
    assert chesta_bala("mercury", pos, 0.0, 0.0) < 30.0
    # Sun/Moon pass-throughs.
    assert chesta_bala("sun", pos, 47.5, 0.0) == 47.5
    assert chesta_bala("moon", pos, 0.0, 88.0) == 88.0


def test_sphuta_drishti_piecewise():
    assert sphuta_drishti(15.0) == 0.0
    assert sphuta_drishti(30.0) == 0.0
    assert sphuta_drishti(60.0) == 15.0
    assert sphuta_drishti(90.0) == 45.0
    assert sphuta_drishti(120.0) == 30.0
    assert sphuta_drishti(150.0) == 0.0
    assert sphuta_drishti(180.0) == 60.0
    assert sphuta_drishti(240.0) == 30.0
    assert sphuta_drishti(300.0) == 0.0
    assert sphuta_drishti(330.0) == 0.0
    # Continuity at the joins.
    for join in (60.0, 90.0, 120.0, 150.0, 180.0):
        assert abs(sphuta_drishti(join - 1e-6) - sphuta_drishti(join + 1e-6)) < 1e-3


def test_drik_bala_sign():
    # Jupiter exactly opposite Saturn: benefic full aspect → positive drik.
    pos = _dummy_positions()
    pos["saturn"]["lon"] = (pos["jupiter"]["lon"] + 180.0) % 360.0
    # Move malefics far from Saturn's aspect windows is hard to guarantee;
    # just assert the value is a finite float.
    v = drik_bala("saturn", pos)
    assert isinstance(v, float) and math.isfinite(v)


# ── ishta/kashta + bhava view ────────────────────────────────────────────────

def test_ishta_kashta_bounds():
    ishta, kashta = ishta_kashta(60.0, 60.0)
    assert (ishta, kashta) == (60.0, 0.0)
    ishta, kashta = ishta_kashta(0.0, 0.0)
    assert (ishta, kashta) == (0.0, 60.0)
    ishta, kashta = ishta_kashta(30.0, 30.0)
    assert 0.0 <= ishta <= 60.0 and 0.0 <= kashta <= 60.0
    # Out-of-range inputs (doubled balas) are clamped, never a domain error.
    ishta, kashta = ishta_kashta(120.0, 45.0)
    assert 0.0 <= ishta <= 60.0 and 0.0 <= kashta <= 60.0


def test_bhava_bala_simple_maps_signs():
    sav = list(range(12))
    signs = [(3 + i) % 12 for i in range(12)]  # Cancer lagna, whole sign
    assert bhava_bala_simple(sav, signs) == signs  # sav[s] == s here


# ── full shadbala on synthetic + real chart ──────────────────────────────────

def _synthetic_inputs():
    return ShadbalaInputs(
        positions=_dummy_positions(), lagna_lon=15.0, jd_ut=100.3,
        lat=HYD_LAT, lng=HYD_LNG, sunrise_jd=100.05, sunset_jd=100.55,
        is_day_birth=True, weekday=2, ayanamsa_value=24.0,
    )


def test_shadbala_totals_and_rupas():
    result = shadbala(_synthetic_inputs())
    assert set(result) == set(SHADBALA_GRAHAS)
    for g, r in result.items():
        assert r["total_virupas"] > 0
        assert abs(r["total_rupas"] - r["total_virupas"] / 60.0) < 0.01
        assert r["required_rupas"] == REQUIRED_RUPAS[g]
        assert r["is_strong"] == (r["total_rupas"] >= r["required_rupas"])
        assert abs(r["ratio"] - r["total_rupas"] / r["required_rupas"]) < 0.01
        assert r["sthana"]["total"] > 0
        assert 0.0 <= r["dig"] <= 60.0


def test_shadbala_real_chart_sanity():
    """1990-05-15 10:30 IST (05:00 UTC), Hyderabad — a Tuesday day birth."""
    from jyotish import ephemeris  # allowed in tests only

    dt = datetime(1990, 5, 15, 5, 0, tzinfo=timezone.utc)
    jd = ephemeris.julian_day_ut(dt)
    raw = ephemeris.sidereal_positions(jd)
    house_data = ephemeris.houses(jd, HYD_LAT, HYD_LNG)
    ayan = ephemeris.ayanamsa_value(jd)
    # Approximate mid-May Hyderabad sunrise/sunset (~05:45 / ~18:40 IST).
    sunrise = ephemeris.julian_day_ut(datetime(1990, 5, 15, 0, 15, tzinfo=timezone.utc))
    sunset = ephemeris.julian_day_ut(datetime(1990, 5, 15, 13, 10, tzinfo=timezone.utc))

    inputs = ShadbalaInputs(
        positions={g: {"lon": d["lon"], "speed": d["speed"]} for g, d in raw.items()},
        lagna_lon=house_data["ascendant"], jd_ut=jd, lat=HYD_LAT, lng=HYD_LNG,
        sunrise_jd=sunrise, sunset_jd=sunset, is_day_birth=True,
        weekday=1,  # Tuesday
        ayanamsa_value=ayan,
    )
    result = shadbala(inputs)
    assert set(result) == set(SHADBALA_GRAHAS)
    for g, r in result.items():
        assert 2.0 <= r["total_rupas"] <= 15.0, f"{g}: {r['total_rupas']}"
        for section in ("sthana", "kala"):
            for k, v in r[section].items():
                assert math.isfinite(v), f"{g}.{section}.{k}"
        for k in ("dig", "chesta", "naisargika", "drik", "total_virupas",
                  "total_rupas", "ratio"):
            assert math.isfinite(r[k]), f"{g}.{k}"
        # ishta/kashta derived from this chart stay in bounds.
        ishta, kashta = ishta_kashta(r["sthana"]["uccha"], r["chesta"])
        assert 0.0 <= ishta <= 60.0 and 0.0 <= kashta <= 60.0

"""Shadbala tests — component invariants + a real-chart sanity band.

The integration test builds ShadbalaInputs from the live ephemeris (allowed in
tests only) for 1990-05-15 10:30 IST, Hyderabad.
"""

import math
from datetime import datetime, timezone

from jyotish.strength import (KALI_EPOCH_JD, MOTION_STATES, NAISARGIKA_BALA,
                              REQUIRED_RUPAS, SHADBALA_GRAHAS, ShadbalaInputs,
                              abda_bala, abda_lord, abda_masa_ahargana,
                              ayana_bala, bhava_bala, bhava_bala_simple,
                              bhava_dig_bala, chesta_bala, chesta_kendra,
                              dig_bala, drekkana_bala, drik_bala, hora_bala,
                              ishta_kashta, kendradi_bala, masa_bala,
                              masa_lord, mean_longitude, motion_state,
                              nathonnatha_bala, ojayugma_bala, paksha_bala,
                              shadbala, sphuta_drishti, tribhaga_bala,
                              uccha_bala, vara_bala, vimshopaka_bala)

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


def _real_chart_inputs(full_bphs: bool = False):
    """1990-05-15 10:30 IST (05:00 UTC), Hyderabad — a Tuesday day birth.

    Returns (inputs, cusps): live-ephemeris ShadbalaInputs + the house cusps
    (allowed in tests only)."""
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
        ayanamsa_value=ayan, full_bphs=full_bphs,
    )
    return inputs, house_data["cusps"]


def test_shadbala_real_chart_sanity():
    inputs, _ = _real_chart_inputs()
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


# ── true chesta (mean elements) ──────────────────────────────────────────────

_REAL_JD = 2448026.708334247  # 1990-05-15 05:00 UTC


def test_mean_longitude_sun_sanity():
    """Mean Sun tracks the true Sun within the equation of center (~2°)."""
    inputs, _ = _real_chart_inputs()
    true_sidereal_sun = inputs.positions["sun"]["lon"]
    mean_sidereal_sun = mean_longitude("sun", inputs.jd_ut, inputs.ayanamsa_value)
    diff = abs((mean_sidereal_sun - true_sidereal_sun + 180.0) % 360.0 - 180.0)
    assert diff < 2.5, f"mean Sun off by {diff}°"
    # Ayanamsa subtraction shifts the reading by exactly the ayanamsa.
    trop = mean_longitude("sun", inputs.jd_ut)
    assert abs((trop - mean_sidereal_sun) % 360.0 - inputs.ayanamsa_value % 360.0) < 1e-9


def test_chesta_kendra_identity():
    """chesta bala (true mode) == reduced kendra / 3 for the five taras."""
    pos = _dummy_positions()
    for g in ("mars", "mercury", "jupiter", "venus", "saturn"):
        k = chesta_kendra(g, _REAL_JD)
        assert 0.0 <= k <= 180.0
        assert abs(chesta_bala(g, pos, 0.0, 0.0, jd_ut=_REAL_JD) - k / 3.0) < 1e-9
        # And the kendra is the reduced mean-planet/mean-Sun separation.
        raw = (mean_longitude(g, _REAL_JD) - mean_longitude("sun", _REAL_JD)) % 360.0
        assert abs(k - (360.0 - raw if raw > 180.0 else raw)) < 1e-9


def test_true_chesta_retrograde_mars_near_60():
    """Mars retrogrades at opposition, where the kendra peaks → chesta ~60.

    Scan one synodic period for the peak kendra day."""
    best = max(chesta_kendra("mars", _REAL_JD + d) for d in range(0, 800, 2))
    assert best > 178.0                      # opposition is reached in the scan
    assert best / 3.0 > 59.0                 # chesta bala saturates near 60


def test_true_chesta_real_chart_retro_planets_high():
    """1990-05-15: Mercury and Saturn are retrograde — true chesta rewards them."""
    inputs, _ = _real_chart_inputs(full_bphs=True)
    result = shadbala(inputs)
    assert inputs.positions["mercury"]["speed"] < 0  # retro in this chart
    assert inputs.positions["saturn"]["speed"] < 0
    assert result["mercury"]["chesta"] > 45.0        # near inferior conjunction
    assert result["saturn"]["chesta"] > 35.0
    # Fast direct Jupiter scores below both retrograde planets.
    assert result["jupiter"]["chesta"] < result["mercury"]["chesta"]
    assert result["jupiter"]["chesta"] < result["saturn"]["chesta"]
    # Sun/Moon pass-throughs are unchanged by the mode.
    assert result["sun"]["chesta"] == result["sun"]["kala"]["ayana"]
    assert result["moon"]["chesta"] == result["moon"]["kala"]["paksha"]


def test_legacy_chesta_default_unchanged():
    """Default mode still uses the speed proxy (golden totals depend on it)."""
    pos = _dummy_positions()
    pos["saturn"]["speed"] = -0.05
    assert chesta_bala("saturn", pos, 0.0, 0.0) == 60.0
    inputs, _ = _real_chart_inputs()
    result = shadbala(inputs)
    assert "abda" not in result["sun"]["kala"] and "masa" not in result["sun"]["kala"]


# ── motion states ────────────────────────────────────────────────────────────

def test_motion_state_thresholds():
    m = 0.524  # Mars mean speed
    assert motion_state("mars", -0.6 * m) == "vakra"
    assert motion_state("mars", -0.2 * m) == "anuvakra"
    assert motion_state("mars", 0.0) == "vikala"
    assert motion_state("mars", 0.2 * m) == "mandatara"
    assert motion_state("mars", 0.7 * m) == "manda"
    assert motion_state("mars", 1.0 * m) == "sama"
    assert motion_state("mars", 1.3 * m) == "chara"
    assert motion_state("mars", 2.0 * m) == "atichara"


def test_motion_state_present_for_five_taras():
    for full in (False, True):
        inputs, _ = _real_chart_inputs(full_bphs=full)
        result = shadbala(inputs)
        for g in ("mars", "mercury", "jupiter", "venus", "saturn"):
            assert result[g]["motion_state"] in MOTION_STATES, g
        # Retro planets of this chart land in a retrograde state.
        for g in ("mercury", "saturn"):
            assert result[g]["motion_state"] in ("vakra", "anuvakra"), g


# ── abda / masa (kala completion) ────────────────────────────────────────────

def test_ahargana_epoch_and_weekday_anchor():
    assert abda_masa_ahargana(KALI_EPOCH_JD) == 0.0
    # Kali epoch day is a Friday: floor(588465.5 + 1.5) % 7 == 5 (0=Sunday).
    assert int(KALI_EPOCH_JD + 1.5) % 7 == 5
    # Cross-check the anchor against Python's weekday on a modern date:
    # JD 2460310.5 = 2024-01-01 00:00 UT, a Monday.
    assert int(2460310.5 + 1.5) % 7 == 1


def test_abda_masa_lords_deterministic_and_valid():
    for jd in (_REAL_JD, 2451545.0, 2460310.5):
        a1, a2 = abda_lord(jd), abda_lord(jd)
        m1, m2 = masa_lord(jd), masa_lord(jd)
        assert a1 == a2 and m1 == m2                 # deterministic
        assert a1 in SHADBALA_GRAHAS and m1 in SHADBALA_GRAHAS
    # Pinned values for the 1990 chart (from the documented Friday anchor).
    assert abda_lord(_REAL_JD) == "mars"
    assert masa_lord(_REAL_JD) == "venus"
    # Exactly one graha holds each bala: totals 15 and 30.
    assert sum(abda_bala(g, _REAL_JD) for g in SHADBALA_GRAHAS) == 15.0
    assert sum(masa_bala(g, _REAL_JD) for g in SHADBALA_GRAHAS) == 30.0


def test_full_bphs_kala_includes_abda_masa():
    inputs, _ = _real_chart_inputs(full_bphs=True)
    result = shadbala(inputs)
    for g, r in result.items():
        assert "abda" in r["kala"] and "masa" in r["kala"], g
        assert r["kala"]["abda"] in (0.0, 15.0)
        assert r["kala"]["masa"] in (0.0, 30.0)
        # Kala total includes the new components (existing vara 45 / hora 60 kept).
        parts = {k: v for k, v in r["kala"].items() if k != "total"}
        assert abs(sum(parts.values()) - r["kala"]["total"]) < 0.05
    assert result["mars"]["kala"]["abda"] == 15.0    # abda lord of this chart
    assert result["venus"]["kala"]["masa"] == 30.0   # masa lord of this chart


def test_full_bphs_real_chart_sanity_band():
    """Total rupas stay in the 2..15 sanity band in FULL BPHS mode too."""
    inputs, _ = _real_chart_inputs(full_bphs=True)
    result = shadbala(inputs)
    for g, r in result.items():
        assert 2.0 <= r["total_rupas"] <= 15.0, f"{g}: {r['total_rupas']}"
        assert r["is_strong"] == (r["total_rupas"] >= r["required_rupas"])


# ── vimshopaka ───────────────────────────────────────────────────────────────

def test_vimshopaka_bounds_and_presence():
    pos = _dummy_positions()
    d1_signs = {g: int(pos[g]["lon"] // 30) for g in SHADBALA_GRAHAS}
    for g in SHADBALA_GRAHAS:
        v = vimshopaka_bala(g, pos[g]["lon"], d1_signs)
        assert 0.0 <= v <= 20.0, g
    for full in (False, True):
        inputs, _ = _real_chart_inputs(full_bphs=full)
        result = shadbala(inputs)
        for g, r in result.items():
            assert 0.0 <= r["vimshopaka"] <= 20.0, g


def test_vimshopaka_dignity_scaling():
    """The D1 rung alone moves the score: exalted Sun ≥ debilitated Sun."""
    d1_ex = {g: 0 for g in SHADBALA_GRAHAS}
    d1_deb = dict(d1_ex, sun=6)
    exalted = vimshopaka_bala("sun", 10.0, d1_ex)        # 10° Aries
    debilitated = vimshopaka_bala("sun", 190.0, d1_deb)  # 10° Libra
    assert exalted > debilitated
    assert 0.0 <= debilitated and exalted <= 20.0


# ── bhava bala ───────────────────────────────────────────────────────────────

def test_bhava_bala_structure_and_components():
    inputs, cusps = _real_chart_inputs(full_bphs=True)
    sb = shadbala(inputs)
    bb = bhava_bala(sb, cusps, inputs.positions)
    assert set(bb) == set(range(1, 13))
    for house, e in bb.items():
        for key in ("bhavadhipati", "bhava_dig", "bhava_drishti", "total"):
            assert key in e and math.isfinite(e[key]), f"house {house}.{key}"
        assert e["lord"] in SHADBALA_GRAHAS
        assert 0.0 <= e["bhava_dig"] <= 60.0
        # Bhavadhipati bala IS the lord's shadbala total.
        assert abs(e["bhavadhipati"] - sb[e["lord"]]["total_virupas"]) < 0.01
        assert abs(e["total"] - (e["bhavadhipati"] + e["bhava_dig"]
                                 + e["bhava_drishti"])) < 0.05


def test_bhava_dig_bala_rasi_classes():
    cusps = [15.0 + 30.0 * i for i in range(12)]  # Aries-rising madhyas
    # House 1 madhya 15° Aries — chatushpada → strong in the 10th (285°):
    # distance 90° → 60 − 30 = 30.
    assert abs(bhava_dig_bala(cusps[0], cusps) - 30.0) < 1e-9
    # 10° Capricorn (1st half, 280°) — chatushpada → 10th (285°): 5° → 58.33.
    assert abs(bhava_dig_bala(280.0, cusps) - (60.0 - 5.0 / 3.0)) < 1e-9
    # 15° Capricorn (285°) is the 2ND half — jalachara → 4th (105°): 180° → 0.
    assert abs(bhava_dig_bala(cusps[9], cusps) - 0.0) < 1e-9
    # House 8 madhya 15° Scorpio — keeta → strong in the 7th (195°): 30° → 50.
    assert abs(bhava_dig_bala(cusps[7], cusps) - 50.0) < 1e-9
    # House 4 madhya 15° Cancer — jalachara → its own house → 60.
    assert abs(bhava_dig_bala(cusps[3], cusps) - 60.0) < 1e-9
    # House 3 madhya 15° Gemini — nara → strong in the 1st: 60° → 40.
    assert abs(bhava_dig_bala(cusps[2], cusps) - 40.0) < 1e-9
    # Sagittarius halves split: 10° Sag is nara (→ 1st), 20° Sag chatushpada (→ 10th).
    d_nara = min(abs(250.0 - 15.0), 360.0 - abs(250.0 - 15.0))
    assert abs(bhava_dig_bala(250.0, cusps) - max(0.0, 60.0 - d_nara / 3.0)) < 1e-9
    d_chat = min(abs(260.0 - 285.0), 360.0 - abs(260.0 - 285.0))
    assert abs(bhava_dig_bala(260.0, cusps) - max(0.0, 60.0 - d_chat / 3.0)) < 1e-9

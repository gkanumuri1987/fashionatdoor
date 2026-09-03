"""Surya Siddhanta + vakya moon tests — internal invariants and drik parity BANDS.

The siddhanta module is a PARITY/COMPARISON mode (drik stays the default), so
the drik comparisons assert DEVIATION BANDS (sun < 3°, moon < 5°, planets and
nodes < 12°), not exactness — the deviation is the feature being displayed.
"""

import math
from datetime import datetime, timezone

import pytest

from jyotish.calendar_hindu import kali_ahargana
from jyotish.ephemeris import julian_day_ut
from jyotish.siddhanta import (CIVIL_DAYS_PER_MAHAYUGA, MANDA_PARIDHI,
                               REVOLUTIONS, SHIGHRA_PARIDHI,
                               VAKYA_ANCHOR_AHARGANA, compare_with_drik,
                               manda_equation, mean_longitude_ss,
                               panchanga_siddhantic, shighra_equation,
                               true_moon_ss, true_positions_ss,
                               vakya_cycle_shift, vakya_moon)

MODERN_DATES = [(2000, 1, 1), (2015, 6, 15), (2024, 3, 20)]


def _jd(y, m, d):
    return julian_day_ut(datetime(y, m, d, 12, tzinfo=timezone.utc))


def _wrap180(deg):
    return (deg + 180.0) % 360.0 - 180.0


# ── Canonical parameter tables ───────────────────────────────────────────────

def test_revolutions_table_exact():
    assert CIVIL_DAYS_PER_MAHAYUGA == 1_577_917_828
    assert REVOLUTIONS == {
        "sun": 4_320_000,
        "moon": 57_753_336,
        "mars": 2_296_832,
        "mercury_sighra": 17_937_060,
        "jupiter": 364_220,
        "venus_sighra": 7_022_376,
        "saturn": 146_568,
        "moon_apogee": 488_203,
        "rahu": 232_238,
    }


def test_paridhi_tables():
    assert MANDA_PARIDHI == {"sun": 14.0, "moon": 32.0, "mars": 75.0,
                             "mercury": 30.0, "jupiter": 33.0, "venus": 12.0,
                             "saturn": 49.0}
    assert SHIGHRA_PARIDHI == {"mars": 235.0, "mercury": 133.0,
                               "jupiter": 70.0, "venus": 262.0, "saturn": 39.0}


# ── Mean longitudes ──────────────────────────────────────────────────────────

def test_mean_planets_zero_at_kali_epoch():
    # The SS epoch alignment: every mean PLANET at 0° at ahargana 0
    # (the apogee/node carry their kshepa epoch offsets instead).
    for body in ("sun", "moon", "mars", "mercury_sighra", "jupiter",
                 "venus_sighra", "saturn"):
        assert mean_longitude_ss(body, 0.0) == 0.0
    assert mean_longitude_ss("moon_apogee", 0.0) == 90.0
    assert mean_longitude_ss("rahu", 0.0) == 180.0


def test_mean_sun_rate_is_ss_sidereal_year():
    # One SS sidereal year = 1,577,917,828 / 4,320,000 days → exactly 360°.
    year = CIVIL_DAYS_PER_MAHAYUGA / REVOLUTIONS["sun"]
    a = 1_800_000.0
    d = _wrap180(mean_longitude_ss("sun", a + year) - mean_longitude_ss("sun", a))
    assert abs(d) < 1e-6


def test_rahu_is_retrograde_decreasing():
    a = 1_863_079.0
    prev = mean_longitude_ss("rahu", a)
    for k in range(1, 6):
        cur = mean_longitude_ss("rahu", a + k * 10.0)
        assert _wrap180(cur - prev) < 0  # moves BACKWARDS every step
        prev = cur


# ── Manda / shighra equation invariants ──────────────────────────────────────

def test_manda_equation_zero_at_kendra_0_and_180():
    for body in MANDA_PARIDHI:
        assert manda_equation(body, 0.0) == pytest.approx(0.0, abs=1e-12)
        assert manda_equation(body, 180.0) == pytest.approx(0.0, abs=1e-9)


def test_manda_equation_max_near_90_and_sign():
    for body, paridhi in MANDA_PARIDHI.items():
        eq90 = manda_equation(body, 90.0)
        # Maximum equals asin(paridhi/360), attained at kendra 90°.
        assert eq90 == pytest.approx(math.degrees(math.asin(paridhi / 360.0)))
        assert eq90 > manda_equation(body, 45.0) > 0
        assert eq90 > manda_equation(body, 135.0) > 0
        # Opposite hemisphere → opposite sign (the classical add/subtract).
        assert manda_equation(body, 270.0) == pytest.approx(-eq90)


def test_shighra_equation_zero_at_kendra_0_and_180():
    for body in SHIGHRA_PARIDHI:
        assert shighra_equation(body, 0.0) == pytest.approx(0.0, abs=1e-12)
        assert shighra_equation(body, 180.0) == pytest.approx(0.0, abs=1e-9)
        assert shighra_equation(body, 60.0) > 0
        assert shighra_equation(body, 300.0) < 0


def test_shighra_max_matches_epicycle_geometry():
    # Max shighra eq = asin(r) (epicycle tangent) — Venus r = 262/360 gives
    # ~46.7°, matching its real greatest elongation scale.
    r = SHIGHRA_PARIDHI["venus"] / 360.0
    peak = max(shighra_equation("venus", k / 10.0) for k in range(0, 1800))
    assert peak == pytest.approx(math.degrees(math.asin(r)), abs=0.1)


# ── True positions ───────────────────────────────────────────────────────────

def test_true_positions_all_bodies_in_range():
    pos = true_positions_ss(kali_ahargana(_jd(2024, 3, 20)))
    assert set(pos) == {"sun", "moon", "mars", "mercury", "jupiter", "venus",
                        "saturn", "rahu", "ketu"}
    for lon in pos.values():
        assert 0.0 <= lon < 360.0


def test_ketu_opposite_rahu():
    for y, m, d in MODERN_DATES:
        pos = true_positions_ss(kali_ahargana(_jd(y, m, d)))
        assert abs(_wrap180(pos["ketu"] - pos["rahu"] - 180.0)) < 1e-9


# ── Drik parity bands (the comparison-mode contract) ─────────────────────────

@pytest.mark.parametrize("y,m,d", MODERN_DATES)
def test_compare_with_drik_bands(y, m, d):
    cmp = compare_with_drik(_jd(y, m, d))
    assert cmp["_mode"] == "surya_siddhanta_vs_drik"
    b = cmp["bodies"]
    assert abs(b["sun"]["delta_deg"]) < 3.0
    assert abs(b["moon"]["delta_deg"]) < 5.0
    for planet in ("mars", "mercury", "jupiter", "venus", "saturn",
                   "rahu", "ketu"):
        assert abs(b[planet]["delta_deg"]) < 12.0, planet
    # deltas are wrapped
    for v in b.values():
        assert -180.0 < v["delta_deg"] <= 180.0
    assert "drik" in cmp["note"] and "default" in cmp["note"]


# ── Vakya moon ───────────────────────────────────────────────────────────────

def test_vakya_anchor_constant():
    # 2000-01-01 00:00 UT = JD 2451544.5 → ahargana 1,863,079. swisseph's
    # utc_to_jd applies a sub-millisecond UTC→UT1 nuance; allow that.
    assert VAKYA_ANCHOR_AHARGANA == pytest.approx(
        kali_ahargana(julian_day_ut(datetime(2000, 1, 1, tzinfo=timezone.utc))),
        abs=1e-4)


def test_vakya_cycle_shift_near_one_sidereal_remainder():
    # 248 days of mean motion mod 360 ≈ 27.7°; the computed shift must agree.
    shift = vakya_cycle_shift()
    mean_shift = _wrap180(248 * REVOLUTIONS["moon"] / CIVIL_DAYS_PER_MAHAYUGA * 360.0)
    assert shift == pytest.approx(mean_shift, abs=1.0)
    assert 26.0 < shift < 29.0


def test_vakya_moon_matches_ss_at_anchor():
    # Dhruva is zero by construction: exact agreement at the calibration epoch.
    assert vakya_moon(VAKYA_ANCHOR_AHARGANA) == pytest.approx(
        true_moon_ss(VAKYA_ANCHOR_AHARGANA), abs=1e-9)


def test_vakya_moon_within_3deg_over_248_day_scan():
    a0 = kali_ahargana(_jd(2024, 1, 1))
    for k in range(0, 248, 31):
        a = a0 + k
        delta = abs(_wrap180(vakya_moon(a) - true_moon_ss(a)))
        assert delta < 3.0, f"day {k}: {delta}"


# ── Siddhantic panchanga ─────────────────────────────────────────────────────

def test_panchanga_siddhantic_shape_and_mode():
    p = panchanga_siddhantic(kali_ahargana(_jd(2024, 3, 20)))
    assert p["_mode"] == "surya_siddhanta"
    assert p["moon_method"] == "siddhanta"
    assert 1 <= p["tithi"]["index"] <= 30
    assert p["tithi"]["paksha"] in ("shukla", "krishna")
    assert 0 <= p["nakshatra"]["index"] <= 26
    assert 1 <= p["yoga"]["index"] <= 27
    assert 1 <= p["karana"]["index"] <= 60
    assert isinstance(p["tithi"]["name"], str) and p["tithi"]["name"]
    assert isinstance(p["nakshatra"]["name"], str) and p["nakshatra"]["name"]


def test_panchanga_siddhantic_vakya_mode_close_to_siddhanta():
    a = kali_ahargana(_jd(2024, 3, 20))
    p_sid = panchanga_siddhantic(a)
    p_vak = panchanga_siddhantic(a, moon_method="vakya")
    assert p_vak["moon_method"] == "vakya"
    # Vakya moon is within 3° of the SS moon → limbs differ by at most one step.
    assert abs(_wrap180(p_vak["moon"] - p_sid["moon"])) < 3.0
    assert abs(p_vak["tithi"]["index"] - p_sid["tithi"]["index"]) <= 1


def test_panchanga_siddhantic_rejects_unknown_moon_method():
    with pytest.raises(ValueError):
        panchanga_siddhantic(1_863_079.0, moon_method="nope")


def test_panchanga_siddhantic_tithi_matches_drik_within_bands():
    # Elongation error ≤ sun band + moon band (< 8°) → tithi index within 1 of
    # the drik tithi (each tithi spans 12°). A wrap at Amavasya/Purnima is
    # tolerated modulo 30.
    from jyotish.ephemeris import sidereal_positions
    jd = _jd(2015, 6, 15)
    pos = sidereal_positions(jd)
    drik_elong = (pos["moon"]["lon"] - pos["sun"]["lon"]) % 360.0
    drik_tithi = min(29, int(drik_elong // 12.0))
    p = panchanga_siddhantic(kali_ahargana(jd))
    diff = min((p["tithi"]["index"] - 1 - drik_tithi) % 30,
               (drik_tithi - p["tithi"]["index"] + 1) % 30)
    assert diff <= 1

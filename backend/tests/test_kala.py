"""Time-primitive tests — ishta kala, kala velas, horas, special lagnas, upagrahas."""

import pytest

from jyotish.kala import (formula_upagrahas, hora_at, ishta_kala, kala_velas,
                          special_lagnas)

RISE, SET, NEXT_RISE = 2451545.0, 2451545.5, 2451546.0  # symmetric 12h/12h day


def test_ishta_kala_linear():
    ik = ishta_kala(RISE + 0.25, RISE)   # 6 hours after sunrise
    assert ik["ghatis"] == pytest.approx(15.0)
    assert ik["vighatis"] == pytest.approx(900.0)


def test_kala_velas_structure_and_periods():
    # Tuesday (weekday_mon0=1): Sunday-first index 2.
    v = kala_velas(RISE, SET, NEXT_RISE, weekday_mon0=1)
    assert len(v["day_segments"]) == 8 and len(v["night_segments"]) == 8
    assert v["day_segments"][0]["lord"] == "mars"       # Tuesday's vara lord
    assert v["day_segments"][7]["lord"] is None         # 8th lordless
    # Saturn's day segment exists and Gulika = its start, Mandi = its middle.
    sat = next(s for s in v["day_segments"] if s["lord"] == "saturn")
    assert v["gulika_day_jd"] == sat["start_jd"]
    assert v["mandi_day_jd"] == pytest.approx((sat["start_jd"] + sat["end_jd"]) / 2)
    # Tuesday Rahu kala = 7th part of the day.
    assert v["rahu_kala"]["start_utc"] < v["rahu_kala"]["end_utc"]


def test_rahu_kala_monday_second_part():
    v = kala_velas(RISE, SET, NEXT_RISE, weekday_mon0=0)  # Monday
    seg = v["day_segments"][1]  # 2nd part
    from jyotish.ephemeris import jd_to_utc
    assert v["rahu_kala"]["start_utc"] == jd_to_utc(seg["start_jd"]).isoformat()


def test_hora_progression():
    # Sunday (mon0=6): first hora lord = Sun; 2nd = Venus (hora order).
    h1 = hora_at(RISE + 0.001, RISE, SET, NEXT_RISE, weekday_mon0=6)
    h2 = hora_at(RISE + (SET - RISE) / 12 + 0.001, RISE, SET, NEXT_RISE, weekday_mon0=6)
    assert h1["lord"] == "sun" and h2["lord"] == "venus"
    hn = hora_at(SET + 0.001, RISE, SET, NEXT_RISE, weekday_mon0=6)
    assert hn["hora_number"] == 13


def test_special_lagnas_rates():
    # After 5 ghatis: Bhava +30°, Hora +60°, Ghati +150°.
    sl = special_lagnas(10.0, 100.0, ghatis=5.0)
    assert sl["bhava_lagna"]["lon"] == pytest.approx(40.0)
    assert sl["hora_lagna"]["lon"] == pytest.approx(70.0)
    assert sl["ghati_lagna"]["lon"] == pytest.approx(160.0)
    # Pranapada: sun 100° (Cancer, movable) + (300 palas/15)*30° = 100+600 → 340.
    assert sl["pranapada"]["lon"] == pytest.approx(340.0)


def test_pranapada_sign_type_offsets():
    # Fixed Sun sign (Taurus 40°): +240 extra.
    sl = special_lagnas(0.0, 40.0, ghatis=0.0)
    assert sl["pranapada"]["lon"] == pytest.approx((40.0 + 240.0) % 360.0)
    # Dual (Gemini 70°): +120.
    sl = special_lagnas(0.0, 70.0, ghatis=0.0)
    assert sl["pranapada"]["lon"] == pytest.approx((70.0 + 120.0) % 360.0)


def test_upagraha_chain_closes():
    for sun in (0.0, 45.5, 133.33, 359.9):
        u = formula_upagrahas(sun)
        # BPHS identity: Upaketu + 30° = Sun.
        assert (u["upaketu"]["lon"] + 30.0) % 360.0 == pytest.approx(sun % 360.0, abs=1e-6)
        assert u["dhuma"]["lon"] == pytest.approx((sun + 133.0 + 1 / 3) % 360.0, abs=1e-6)

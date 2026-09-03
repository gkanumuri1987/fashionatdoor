"""Event-finding tests — real ephemeris, deterministic dates, known anchors."""

from datetime import date, datetime, timezone

from jyotish.constants import NAKSHATRAS
from jyotish.ephemeris import julian_day_ut, sidereal_positions
from jyotish.events import (karana_end, masa, nakshatra_end, new_moon_after,
                            new_moon_before, panchanga_with_endings,
                            sankranti, station_near, tithi_end, yoga_end)

NAK_SPAN = 360.0 / 27.0


def _jd(y, m, d, hh=0, mm=0):
    return julian_day_ut(datetime(y, m, d, hh, mm, tzinfo=timezone.utc))


def _elong(jd):
    pos = sidereal_positions(jd)
    return (pos["moon"]["lon"] - pos["sun"]["lon"]) % 360.0


def _dist_to_multiple(angle, step):
    r = angle % step
    return min(r, step - r)


def test_tithi_end_bracket_and_boundary():
    jd = _jd(2024, 6, 1, 12, 0)
    r = tithi_end(jd)
    assert jd < r["ends_jd"] <= jd + 1.5
    # elongation at the returned instant is a 12° multiple
    assert _dist_to_multiple(_elong(r["ends_jd"]), 12.0) < 1e-3
    assert 1 <= r["tithi_index"] <= 30
    assert r["ends_utc"].startswith("2024-06-0")


def test_tithi_end_eclipse_day_into_shukla_pratipada():
    # 2020-06-21 annular solar eclipse: Amavasya ends ~06:40 UTC,
    # rolling into Shukla Pratipada.
    jd = _jd(2020, 6, 21, 0, 0)
    r = tithi_end(jd)
    assert r["name"] == "Amavasya"
    assert jd < r["ends_jd"] < jd + 0.5  # ends that morning (UTC)
    elong_after = _elong(r["ends_jd"] + 1e-3)
    assert int(elong_after // 12.0) == 0  # Shukla Pratipada


def test_nakshatra_end_boundary():
    jd = _jd(2024, 6, 1, 12, 0)
    r = nakshatra_end(jd)
    assert jd < r["ends_jd"] <= jd + 1.5
    moon = sidereal_positions(r["ends_jd"])["moon"]["lon"]
    assert _dist_to_multiple(moon, NAK_SPAN) < 1e-3
    assert r["name"] == NAKSHATRAS[r["index"]]


def test_yoga_end_boundary():
    jd = _jd(2024, 6, 1, 12, 0)
    r = yoga_end(jd)
    assert jd < r["ends_jd"] <= jd + 1.5
    pos = sidereal_positions(r["ends_jd"])
    total = (pos["sun"]["lon"] + pos["moon"]["lon"]) % 360.0
    assert _dist_to_multiple(total, NAK_SPAN) < 1e-3


def test_karana_end_boundary():
    jd = _jd(2024, 6, 1, 12, 0)
    r = karana_end(jd)
    assert jd < r["ends_jd"] <= jd + 0.8
    assert _dist_to_multiple(_elong(r["ends_jd"]), 6.0) < 1e-3


def test_sankranti_mesha_2024():
    # From 2024-04-10 the next crossing is the Mesha sankranti (Lahiri),
    # falling Apr 13-14 2024.
    jd = _jd(2024, 4, 10)
    s = sankranti(jd)
    assert s["sign_entered"] == 0 and s["sign_name"] == "Mesha"
    assert _jd(2024, 4, 12) < s["jd"] < _jd(2024, 4, 15)
    sun = sidereal_positions(s["jd"])["sun"]["lon"]
    assert min(sun, 360.0 - sun) < 1e-3  # sidereal Sun at 0° (wrapped)


def test_sankranti_previous():
    jd = _jd(2024, 4, 10)
    s = sankranti(jd, direction=-1)
    assert s["sign_entered"] == 11 and s["sign_name"] == "Meena"
    assert jd - 32 < s["jd"] < jd


def test_new_moons_bracket_masa_length():
    jd = _jd(2024, 6, 1)
    before, after = new_moon_before(jd), new_moon_after(jd)
    assert before <= jd <= after
    assert 29.2 <= after - before <= 29.9
    assert _elong(before) % 360.0 < 1e-2 or _elong(before) > 359.99
    m = masa(jd)
    assert m["start_jd"] == before and m["end_jd"] == after
    assert m["paksha_at_jd"] in ("shukla", "krishna")


def test_masa_adhika_shravana_2023():
    # 2023 had Adhika Shravana (amanta: ~Jul 18 - Aug 16 2023).
    m = masa(_jd(2023, 7, 25))
    assert m["adhika"] is True
    assert m["kshaya"] is False
    assert "Shravana" in m["name"] and m["name"].startswith("Adhika")


def test_masa_regular_month_not_adhika():
    m = masa(_jd(2024, 6, 1))
    assert m["adhika"] is False


def test_station_mercury_retrograde_april_2024():
    # Mercury stationed retrograde ~Apr 1-2 2024.
    r = station_near(_jd(2024, 3, 25), "mercury")
    assert r is not None
    assert r["type"] == "retrograde_begins"
    assert _jd(2024, 3, 30) < r["jd"] < _jd(2024, 4, 4)
    # station means speed ~0 at the instant
    assert abs(sidereal_positions(r["jd"])["mercury"]["speed"]) < 0.02


def test_station_rejects_luminaries():
    import pytest
    with pytest.raises(ValueError):
        station_near(_jd(2024, 3, 25), "sun")


def test_panchanga_with_endings_shape():
    jd = _jd(2024, 6, 1, 6, 0)
    p = panchanga_with_endings(jd, date(2024, 6, 1))
    for limb in ("tithi", "nakshatra", "yoga", "karana"):
        assert p[limb]["ends_jd"] > jd
        assert "ends_utc" in p[limb] and p[limb]["ends_utc"].endswith("+00:00")
    assert p["vara"]["name"]  # untouched panchanga fields survive

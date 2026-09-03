"""Western/tropical layer regression suite.

The tropical frame is derived from the sidereal ephemeris via
tropical = (sidereal + ayanamsa) % 360, so the identity test gates everything;
solstice/equinox pins verify the tropical zodiac against the seasons (Sun at
0° Cancer / 0° Aries by DEFINITION of the tropical zodiac).
"""

from datetime import date, datetime, time, timezone

from jyotish.ephemeris import ayanamsa_value, julian_day_ut, sidereal_positions
from jyotish.western import (annual_profection, tropical_positions,
                             western_aspects, western_chart)


def _p(lon, speed=0.0):
    return {"lon": float(lon), "speed": float(speed), "retrograde": speed < 0}


def test_tropical_is_sidereal_plus_ayanamsa():
    jd = julian_day_ut(datetime(2000, 1, 1, 12, 0, tzinfo=timezone.utc))
    sid = sidereal_positions(jd)
    ay = ayanamsa_value(jd)
    trop = tropical_positions(jd)
    label = {"rahu": "north_node", "ketu": "south_node"}
    for name, data in sid.items():
        expect = (data["lon"] + ay) % 360.0
        got = trop[label.get(name, name)]["lon"]
        assert abs(got - expect) < 1e-9
        assert trop[label.get(name, name)]["speed"] == data["speed"]


def test_solstice_sun_at_cancer_boundary():
    # June solstice 2000 (2000-06-21 ~01:48 UTC): tropical Sun at 90° = 0° Cancer.
    jd = julian_day_ut(datetime(2000, 6, 21, 1, 48, tzinfo=timezone.utc))
    sun = tropical_positions(jd)["sun"]["lon"]
    assert abs(sun - 90.0) < 0.2  # sign 3 boundary


def test_equinox_sun_at_aries_zero():
    # March equinox 2000 (2000-03-20 ~07:35 UTC): tropical Sun at 0° Aries.
    jd = julian_day_ut(datetime(2000, 3, 20, 7, 35, tzinfo=timezone.utc))
    sun = tropical_positions(jd)["sun"]["lon"]
    assert min(sun, 360.0 - sun) < 0.2


def test_exact_trine_detected():
    aspects = western_aspects({"venus": _p(10, 1.2), "saturn": _p(130, 0.1)})
    assert len(aspects) == 1
    a = aspects[0]
    assert a["aspect"] == "trine" and a["angle"] == 120.0 and a["orb"] == 0.0


def test_out_of_orb_square_missed():
    # 98° separation: 8° from square — beyond the 7° non-luminary orb.
    aspects = western_aspects({"mars": _p(0, 0.5), "venus": _p(98, 1.2)})
    assert aspects == []


def test_luminary_orb_bonus():
    # Same 98° separation but with the Sun: orb 7+2=9 → square detected.
    aspects = western_aspects({"sun": _p(0, 1.0), "mars": _p(98, 0.5)})
    assert len(aspects) == 1
    assert aspects[0]["aspect"] == "square"
    assert abs(aspects[0]["orb"] - 8.0) < 1e-9


def test_applying_vs_separating():
    # Moon at 85° behind the 90° square to the Sun, moving faster → applying.
    applying = western_aspects({"sun": _p(0, 1.0), "moon": _p(85, 13.0)})
    assert applying[0]["aspect"] == "square" and applying[0]["applying"] is True
    # Moon past exact at 95°, still gaining separation → separating.
    separating = western_aspects({"sun": _p(0, 1.0), "moon": _p(95, 13.0)})
    assert separating[0]["aspect"] == "square" and separating[0]["applying"] is False


def test_profection_arithmetic():
    # Age 0 → house 1, ascendant sign itself; age 13 → house 2, next sign.
    p0 = annual_profection(0, asc_sign=4)  # Leo rising
    assert p0["profected_house"] == 1
    assert p0["profected_sign"] == 4 and p0["year_ruler"] == "sun"
    p13 = annual_profection(13, asc_sign=4)
    assert p13["profected_house"] == 2
    assert p13["profected_sign"] == 5 and p13["year_ruler"] == "mercury"
    # Traditional rulership spot-checks.
    assert annual_profection(0, 0)["year_ruler"] == "mars"      # Aries
    assert annual_profection(0, 9)["year_ruler"] == "saturn"    # Capricorn
    assert annual_profection(0, 11)["year_ruler"] == "jupiter"  # Pisces


def test_western_chart_end_to_end():
    # 1990-05-15 10:30 IST, Kolkata. Sidereal Sun ~0°23' Taurus + ayanamsa
    # ~23.72 → tropical Sun ≈ 24.1° Taurus.
    chart = western_chart(date(1990, 5, 15), time(10, 30),
                          lat=22.5726, lng=88.3639, tz_name="Asia/Kolkata")
    assert chart["schema"] == "WesternV1" and chart["zodiac"] == "tropical"
    sun = chart["planets"]["sun"]
    assert sun["sign"] == 1  # Taurus (tropical, 0=Aries)
    assert abs((sun["lon"] % 30) - 24.1) < 0.5
    # Nodes carry western labels.
    assert "north_node" in chart["planets"] and "south_node" in chart["planets"]
    assert "rahu" not in chart["planets"]
    # Profection + transits blocks present and well-formed.
    assert chart["profection"]["profected_house"] in range(1, 13)
    assert chart["profection"]["year_ruler"] in (
        "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn")
    assert set(chart["transits"]["planets"]) == set(chart["planets"])
    for t in chart["transits"]["planets"].values():
        assert 1 <= t["natal_house"] <= 12
        for c in t["aspects_to_natal"]:
            assert c["orb"] <= 3.0


def test_western_chart_houses_assigned():
    chart = western_chart(date(1990, 5, 15), time(10, 30),
                          lat=22.5726, lng=88.3639, tz_name="Asia/Kolkata")
    assert len(chart["houses"]["cusps"]) == 12
    assert chart["houses"]["system"] == "placidus"
    for p in chart["planets"].values():
        assert 1 <= p["house"] <= 12
    # Ascendant sits in house 1 by construction (cusp 1 = ascendant in Placidus).
    asc_lon = chart["ascendant"]["lon"]
    assert abs((asc_lon - chart["houses"]["cusps"][0]) % 360.0) < 1e-6

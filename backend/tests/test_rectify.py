"""Rectification screening tests — real ephemeris."""

from datetime import date, time

from jyotish.rectify import rectify


def test_rectify_shape_and_scoring():
    r = rectify(date(1990, 5, 15), time(10, 30), lat=17.385, lng=78.4867,
                tz_name="Asia/Kolkata", band_minutes=10, step_minutes=5)
    assert r["schema"] == "RectifyV1"
    assert len(r["candidates"]) == 5           # -10,-5,0,5,10
    for c in r["candidates"]:
        assert 0 <= c["score"] <= 4
        assert c["local_time"]
    assert r["best_times"]
    assert "Screening aid" in r["note"]


def test_rectify_band_capped():
    r = rectify(date(1990, 5, 15), time(10, 30), lat=17.385, lng=78.4867,
                tz_name="Asia/Kolkata", band_minutes=500, step_minutes=30)
    assert r["band_minutes"] == 120

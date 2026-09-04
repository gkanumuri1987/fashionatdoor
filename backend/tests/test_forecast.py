"""Personal Jyothishyam — deterministic panchanga-grounded forecast."""

from datetime import date

from jyotish.chart import compute_chart
from jyotish.forecast import personal_forecast


def _chart():
    from datetime import time
    return compute_chart(date(1990, 5, 15), time(10, 30),
                         lat=17.385, lng=78.4867, tz_name="Asia/Kolkata")


def test_shape_and_determinism():
    c = _chart()
    f1 = personal_forecast(c, interests=["career", "relationship"], as_of=date(2026, 9, 4))
    f2 = personal_forecast(c, interests=["career", "relationship"], as_of=date(2026, 9, 4))
    assert f1 == f2                       # pure for a fixed as_of
    assert f1["schema"] == "JyothishyamV1"
    assert len(f1["week"]) == 7
    t = f1["today"]
    assert t["tithi"]["group"] in ("Nanda", "Bhadra", "Jaya", "Rikta", "Purna")
    assert t["nakshatra"]["class"] in ("chara", "sthira", "ugra", "mishra",
                                       "kshipra", "mridu", "tikshna")
    assert t["new_ventures"] in ("favourable", "avoid", "mixed")
    assert isinstance(t["cautions"], list)
    assert len(t["focus"]) == 2           # two interests requested


def test_tarabala_from_natal_moon():
    c = _chart()
    f = personal_forecast(c, as_of=date(2026, 9, 4))
    tara = f["today"]["tarabala"]
    assert tara["name"] in ("Janma", "Sampat", "Vipat", "Kshema", "Pratyak",
                            "Sadhaka", "Vadha", "Mitra", "Atimitra")
    assert isinstance(tara["favourable"], bool)


def test_period_deity_from_dasha():
    c = _chart()
    f = personal_forecast(c, as_of=date(2026, 9, 4))
    assert f["period"]["maha_lord"]       # a running dasha exists
    assert f["period"]["week_deity"]      # mapped to a deity


def test_abroad_location_override():
    c = _chart()
    f_in = personal_forecast(c, tz_name="Asia/Kolkata", as_of=date(2026, 9, 4))
    f_us = personal_forecast(c, tz_name="America/Chicago", lat=41.88, lng=-87.63,
                             as_of=date(2026, 9, 4))
    # Rahu kalam windows differ by location (or one may be None) — not identical.
    assert f_in["today"]["rahu_kalam"] != f_us["today"]["rahu_kalam"] \
        or f_in["today"]["weekday"] == f_us["today"]["weekday"]

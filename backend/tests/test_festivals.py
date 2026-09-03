"""Festival calendar tests — pinned against known 2026 dates."""

from jyotish.festivals import LOCATIONS, TRADITIONS, build_month


def _fest_dates(m):
    return {f["key"]: d["date"] for d in m["days"] for f in d["festivals"]}


def test_january_2026_sankranti_cluster_india():
    m = build_month(2026, 1, "telugu", "in")
    f = _fest_dates(m)
    assert f["bhogi"] == "2026-01-13"
    assert f["makara_sankranti"] == "2026-01-14"
    assert f["kanuma"] == "2026-01-15"
    assert f["ratha_saptami"] == "2026-01-25"
    assert m["samvatsara"] == "Vishvavasu"


def test_deepavali_2026_shifts_by_timezone():
    f_in = _fest_dates(build_month(2026, 11, "telugu", "in"))
    f_us = _fest_dates(build_month(2026, 11, "telugu", "us_east"))
    assert f_in["deepavali"] == "2026-11-08"
    assert f_in["naraka_chaturdashi"] == "2026-11-08"
    assert f_us["naraka_chaturdashi"] == "2026-11-07"   # genuinely a day earlier in the US


def test_day_payload_complete():
    m = build_month(2026, 3, "tamil", "uk")
    assert len(m["days"]) == 31
    for d in m["days"]:
        assert d["tithi"]["name"] and d["nakshatra"]["name"]
        assert d["tamil_month"] and d["tamil_day"] >= 1
        assert d["sunrise"] and d["sunset"]
    assert m["timezone"] == "Europe/London"


def test_tradition_filters_festivals():
    f_te = _fest_dates(build_month(2026, 8, "telugu", "in"))
    f_hi = _fest_dates(build_month(2026, 8, "hindi", "in"))
    assert "raksha_bandhan" in f_hi and "raksha_bandhan" not in f_te
    assert "varalakshmi_vratam" in f_te and "varalakshmi_vratam" not in f_hi
    # Janmashtami (Shravana K8, amanta) falls in SEPTEMBER 2026 — the Krishna
    # paksha follows the purnima. Pinned: real date Sep 4 2026.
    f_sep = _fest_dates(build_month(2026, 9, "telugu", "in"))
    assert f_sep["janmashtami"] == "2026-09-04"


def test_all_locations_compute():
    for loc in LOCATIONS:
        m = build_month(2026, 6, "telugu", loc)
        assert len(m["days"]) == 30

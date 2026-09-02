"""Timezone regression suite — the classic source of wrong charts.

These pin the historically-correct UTC offsets through zoneinfo. If any fail,
the system tzdata is broken or the resolution path regressed — either way,
every chart would be wrong, so this suite gates everything.
"""

from datetime import date, time

from jyotish.geo import to_utc


def test_india_wartime_dst_1943():
    # India ran IST+1h (UTC+6:30) from Sep 1942 to Oct 1945.
    b = to_utc(date(1943, 6, 1), time(12, 0), tz_name="Asia/Kolkata")
    assert b.utc_offset_hours == 6.5


def test_india_1948_is_ist():
    b = to_utc(date(1948, 6, 1), time(12, 0), tz_name="Asia/Kolkata")
    assert b.utc_offset_hours == 5.5


def test_india_modern():
    b = to_utc(date(1990, 5, 15), time(10, 30), tz_name="Asia/Kolkata")
    assert b.utc_offset_hours == 5.5
    assert b.utc.hour == 5 and b.utc.minute == 0


def test_kathmandu_offset():
    # Nepal has used UTC+5:45 since 1986.
    b = to_utc(date(1990, 1, 1), time(12, 0), tz_name="Asia/Kathmandu")
    assert abs(b.utc_offset_hours - 5.75) < 1e-9


def test_us_dst_transition():
    # 2020-03-08: US spring-forward. 01:00 EST = UTC-5; 03:30 EDT = UTC-4.
    before = to_utc(date(2020, 3, 8), time(1, 0), tz_name="America/New_York")
    after = to_utc(date(2020, 3, 8), time(3, 30), tz_name="America/New_York")
    assert before.utc_offset_hours == -5.0
    assert after.utc_offset_hours == -4.0


def test_latlng_resolves_india():
    # Hyderabad coordinates → Asia/Kolkata without an explicit tz.
    b = to_utc(date(2000, 1, 1), time(6, 0), lat=17.385, lng=78.4867)
    assert b.tz_name == "Asia/Kolkata"
    assert b.utc_offset_hours == 5.5

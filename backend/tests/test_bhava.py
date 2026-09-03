"""Bhava chalita span + membership tests."""

from jyotish.bhava import bhava_chalita


def _equal_cusps(asc=15.0):
    return [(asc + 30 * i) % 360.0 for i in range(12)]


def test_equal_cusps_spans_are_sign_shifted():
    ch = bhava_chalita(_equal_cusps(15.0), {})
    h1 = ch["houses"][0]
    assert h1["madhya"] == 15.0 and h1["start"] == 0.0 and h1["end"] == 30.0


def test_membership_and_chalita_shift():
    cusps = _equal_cusps(15.0)
    # 29.5° sits in house 1's span (0-30) even though close to the boundary;
    # 31° falls to house 2.
    ch = bhava_chalita(cusps, {"a": {"lon": 29.5}, "b": {"lon": 31.0},
                               "c": {"lon": 15.0}})
    assert ch["grahas"]["a"]["house"] == 1 and ch["grahas"]["a"]["in_sandhi"]
    assert ch["grahas"]["b"]["house"] == 2
    assert ch["grahas"]["c"]["house"] == 1 and not ch["grahas"]["c"]["in_sandhi"]


def test_wraparound_span():
    ch = bhava_chalita(_equal_cusps(345.0), {"x": {"lon": 350.0}, "y": {"lon": 200.0}})
    assert ch["grahas"]["x"]["house"] == 1
    assert 1 <= ch["grahas"]["y"]["house"] <= 12
    # Every span covers the zodiac exactly once.
    total = sum((h["end"] - h["start"]) % 360.0 for h in ch["houses"])
    assert abs(total - 360.0) < 1e-6

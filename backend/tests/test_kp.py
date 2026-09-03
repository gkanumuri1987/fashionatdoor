"""KP star/sub/sub-sub, horary 1-249 and significators — pure unit tests."""

import pytest

from jyotish.constants import DASHA_ORDER, DASHA_YEARS
from jyotish.kp import (SPAN, cusp_sublords, horary_number_to_lon,
                        horary_segments, planet_significators, ruling_planets,
                        star_sub_subsub)

KETU_SUB_WIDTH = SPAN * DASHA_YEARS["ketu"] / 120.0  # 7/120 × 13°20' = 0.77778°


# ── Sub geometry ─────────────────────────────────────────────────────────────

def test_sub_spans_sum_to_one_star():
    # The 9 sub widths within any star are years/120 of 13°20' → sum exactly.
    widths = [SPAN * DASHA_YEARS[lord] / 120.0 for lord in DASHA_ORDER]
    assert sum(widths) == pytest.approx(SPAN, abs=1e-12)
    # Cross-check via the horary walk: Ashwini contains no sign boundary,
    # so its segments are exactly the 9 subs and tile the star.
    ashwini = [s for s in horary_segments() if s["star_index"] == 0]
    assert len(ashwini) == 9
    assert sum(s["end_lon"] - s["start_lon"] for s in ashwini) == pytest.approx(SPAN)


def test_first_sub_of_ashwini_is_ketu():
    # Star lord Ketu → first sub is Ketu's own, 0.7778° wide from 0°.
    first = horary_segments()[0]
    assert (first["star_lord"], first["sub_lord"]) == ("ketu", "ketu")
    assert first["start_lon"] == 0.0
    assert first["end_lon"] == pytest.approx(KETU_SUB_WIDTH)
    assert KETU_SUB_WIDTH == pytest.approx(0.777778, abs=1e-6)


def test_half_degree_aries_is_ketu_ketu():
    d = star_sub_subsub(0.5)
    assert d["star_name"] == "Ashwini"
    assert d["star_lord"] == "ketu"
    assert d["sub_lord"] == "ketu"       # 0.5° < 0.7778° Ketu sub
    # Sub-sub by hand: 0.5° into the Ketu sub → fraction 0.5/0.77778 of the
    # sub → 0.5/0.77778 × 120 = 77.142857 "years" from Ketu. Cumulative from
    # Ketu: 7, 27, 33, 43, 50, 68 (rahu ends), 84 (jupiter ends) → 77.14
    # falls in Jupiter's span (68..84).
    assert d["sub_sub_lord"] == "jupiter"


def test_sub_after_ketu_in_ashwini_is_venus():
    # Known KP fact: the cycle continues Ketu → Venus.
    d = star_sub_subsub(KETU_SUB_WIDTH + 0.01)
    assert (d["star_lord"], d["sub_lord"]) == ("ketu", "venus")
    assert horary_segments()[1]["sub_lord"] == "venus"


def test_moon_100_deg_pushya_saturn_star_venus_sub():
    # Hand computation: 100 / 13.3333 = 7.5 → star index 7 = Pushya, lord
    # Saturn (DASHA_ORDER[7]). Within-star: 100 − 7×13.3333 = 6.6667° →
    # 6.6667/13.3333 × 120 = 60 years from Saturn. Cumulative from Saturn:
    # 19 (sat), 36 (merc), 43 (ketu), 63 (venus) → 60 falls in Venus (43..63).
    d = star_sub_subsub(100.0)
    assert d["star_index"] == 7
    assert d["star_name"] == "Pushya"
    assert d["star_lord"] == "saturn"
    assert d["sub_lord"] == "venus"
    # Sub-sub: (60−43)/20 × 120 = 102 years from Venus. Cumulative from
    # Venus: 20, 26, 36, 43, 61, 77, 96 (sat ends), 113 (merc ends) → 102
    # falls in Mercury's span (96..113).
    assert d["sub_sub_lord"] == "mercury"


# ── Horary 1-249 ─────────────────────────────────────────────────────────────

def test_horary_has_exactly_249_segments():
    segs = horary_segments()
    assert len(segs) == 249
    # 243 subs + 6 split by a sign boundary; splits happen only at 30°, 90°,
    # 150°, 210°, 270°, 330° (the 60°/180°/300° boundaries coincide with an
    # exact sub boundary, and 0°/120°/240° with a star boundary).
    assert segs[-1]["end_lon"] == pytest.approx(360.0)


def test_horary_number_1_starts_at_zero_and_monotonic():
    assert horary_number_to_lon(1) == 0.0
    starts = [horary_number_to_lon(n) for n in range(1, 250)]
    assert all(b > a for a, b in zip(starts, starts[1:]))
    # Segments tile the zodiac with no gaps.
    segs = horary_segments()
    for prev, cur in zip(segs, segs[1:]):
        assert cur["start_lon"] == pytest.approx(prev["end_lon"], abs=1e-12)


def test_horary_sign_boundary_splits():
    starts = {round(s["start_lon"], 9): s for s in horary_segments()}
    # 30° splits a sub in Krittika: the segment starting there continues the
    # SAME (star, sub) as the segment before it.
    seg_30 = starts[30.0]
    prev = horary_segments()[seg_30["number"] - 2]
    assert (seg_30["star_index"], seg_30["sub_lord"]) == (prev["star_index"], prev["sub_lord"])
    # 60° coincides with an exact sub boundary in Mrigashira (Mars star:
    # 7+18+16+19 = 60 years = Saturn sub end) → the sub CHANGES, no split.
    seg_60 = starts[60.0]
    prev_60 = horary_segments()[seg_60["number"] - 2]
    assert prev_60["sub_lord"] == "saturn"
    assert seg_60["sub_lord"] == "mercury"
    assert seg_60["sub_lord"] != prev_60["sub_lord"]


def test_horary_number_out_of_range():
    with pytest.raises(ValueError):
        horary_number_to_lon(0)
    with pytest.raises(ValueError):
        horary_number_to_lon(250)


# ── Cusps + significators ────────────────────────────────────────────────────

_CUSPS = [float(h * 30) for h in range(12)]  # synthetic equal Placidus cusps


def test_cusp_sublords_shape():
    out = cusp_sublords(_CUSPS)
    assert len(out) == 12
    assert [c["house"] for c in out] == list(range(1, 13))
    for c in out:
        assert {"star_lord", "sub_lord", "sub_sub_lord", "star_index", "star_name"} <= set(c)
    # Cusp 1 at 0° Aries → Ashwini, Ketu star, Ketu sub.
    assert (out[0]["star_lord"], out[0]["sub_lord"]) == ("ketu", "ketu")
    with pytest.raises(ValueError):
        cusp_sublords(_CUSPS[:11])


def test_significator_grades():
    positions = {
        "sun": {"lon": 5.0},       # occupies house 1; star lord ketu (Ashwini)
        "moon": {"lon": 28.0},     # house 1; Krittika → star lord SUN (occupant of 1)
        "jupiter": {"lon": 55.0},  # house 2; Mrigashira → star lord MARS (lord of 1, 8)
    }
    sig = planet_significators(positions, _CUSPS)
    h1 = sig["houses"][1]
    assert "moon" in h1["a"]              # in the star of an occupant (Sun)
    assert h1["b"] == ["moon", "sun"]     # occupants
    assert "jupiter" in h1["c"]           # in the star of the house lord (Mars)
    assert h1["d"] == ["mars"]            # sign lord of 0° Aries
    # Jupiter also grades (c) for house 8 (Scorpio, Mars-lorded).
    assert "jupiter" in sig["houses"][8]["c"]


def test_significator_symmetry():
    positions = {
        "sun": {"lon": 5.0}, "moon": {"lon": 28.0}, "mars": {"lon": 130.0},
        "jupiter": {"lon": 55.0}, "rahu": {"lon": 27.0}, "ketu": {"lon": 207.0},
    }
    sig = planet_significators(positions, _CUSPS)
    # planets↔houses consistent: g signifies h ⇔ g appears in some grade of h.
    for g, hs in sig["planets"].items():
        for h in hs:
            assert any(g in names for names in sig["houses"][h].values())
    for h, levels in sig["houses"].items():
        for names in levels.values():
            for g in names:
                assert h in sig["planets"][g]


def test_node_agency_rule():
    # Rahu at 27° shares Aries with Sun (5°) and Moon (28°) → it inherits
    # their grades; e.g. Moon grades (a) for house 1, so Rahu must too.
    positions = {"sun": {"lon": 5.0}, "moon": {"lon": 28.0}, "rahu": {"lon": 27.0}}
    sig = planet_significators(positions, _CUSPS)
    assert "rahu" in sig["houses"][1]["a"]
    assert "rahu" in sig["houses"][1]["b"]   # it is also a genuine occupant
    # Nodes never appear as house lords.
    for levels in sig["houses"].values():
        assert levels["d"][0] not in ("rahu", "ketu")


def test_ruling_planets_shape():
    # Sunday (weekday 6) → day lord Sun. Moon 100° → Cancer (lord Moon),
    # Pushya (Saturn). Lagna 5° → Aries (Mars), Ashwini (Ketu).
    rp = ruling_planets(6, moon_lon=100.0, lagna_lon=5.0)
    assert rp["day_lord"] == "sun"
    assert rp["moon_sign_lord"] == "moon"
    assert rp["moon_star_lord"] == "saturn"
    assert rp["lagna_sign_lord"] == "mars"
    assert rp["lagna_star_lord"] == "ketu"
    assert rp["moon_sub_lord"] == "venus"    # hand-derived in the 100° test above

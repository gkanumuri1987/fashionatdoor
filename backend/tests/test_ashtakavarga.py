"""Ashtakavarga tests — canonical table totals, SAV invariant, spot checks."""

from jyotish.ashtakavarga import (BAV_TOTALS, BINDU_TABLE, SAV_TOTAL,
                                  SEVEN_GRAHAS, bhinnashtakavarga,
                                  sarvashtakavarga)


def _positions(**overrides):
    base = {"sun": 5.0, "moon": 47.0, "mars": 100.0, "mercury": 152.0,
            "jupiter": 201.0, "venus": 260.0, "saturn": 311.0}
    base.update(overrides)
    return base


def test_table_totals_match_canonical():
    for graha, expected in BAV_TOTALS.items():
        total = sum(len(houses) for houses in BINDU_TABLE[graha].values())
        assert total == expected, f"{graha}: {total} != {expected}"


def test_every_bav_has_eight_contributors():
    for graha in SEVEN_GRAHAS:
        assert set(BINDU_TABLE[graha]) == set(SEVEN_GRAHAS) | {"lagna"}


def test_bav_totals_and_sav_337_arbitrary_positions():
    bav = bhinnashtakavarga(_positions(), lagna_sign=3)
    for graha in SEVEN_GRAHAS:
        assert sum(bav[graha]) == BAV_TOTALS[graha]
    sav = sarvashtakavarga(bav)
    assert sum(sav) == SAV_TOTAL == 337
    assert len(sav) == 12


def test_sav_337_other_positions():
    bav = bhinnashtakavarga(_positions(sun=359.9, moon=0.0, mars=0.0), lagna_sign=11)
    assert sum(sarvashtakavarga(bav)) == 337


def test_bindus_within_0_to_8():
    # All contributors in one sign maximizes stacking; still capped at 8.
    same = {g: 12.0 for g in SEVEN_GRAHAS}
    bav = bhinnashtakavarga(same, lagna_sign=0)
    for graha in SEVEN_GRAHAS:
        assert all(0 <= b <= 8 for b in bav[graha])


def test_sun_bav_spot_check_all_in_aries():
    """With every contributor in Aries, Sun's BAV in Aries counts exactly the
    contributors that grant house 1: Sun, Mars, Saturn (per the canonical
    table — Sun's own 1st-house bindu included)."""
    same = {g: 5.0 for g in SEVEN_GRAHAS}  # all in Aries
    bav = bhinnashtakavarga(same, lagna_sign=0)
    grantors_of_house_1 = [c for c, houses in BINDU_TABLE["sun"].items() if 1 in houses]
    assert grantors_of_house_1 == ["sun", "mars", "saturn"]
    assert bav["sun"][0] == 3


def test_contribution_counted_from_contributor_sign():
    """Moving only the Moon shifts only Moon's contributions. Sun in Aries:
    Moon in Aries grants Sun-BAV bindus in houses 3,6,10,11 from Aries;
    Moon in Taurus grants the same houses counted from Taurus."""
    bav_a = bhinnashtakavarga(_positions(moon=0.0), lagna_sign=0)   # Moon in Aries
    bav_b = bhinnashtakavarga(_positions(moon=30.0), lagna_sign=0)  # Moon in Taurus
    # House 3 from Aries = Gemini (2); from Taurus = Cancer (3).
    assert bav_a["sun"][2] == bav_b["sun"][3] + (bav_a["sun"][2] - bav_b["sun"][3])
    # Direct check: difference vector equals the Moon-table shift.
    diff = [bav_b["sun"][s] - bav_a["sun"][s] for s in range(12)]
    expected = [0] * 12
    for h in BINDU_TABLE["sun"]["moon"]:
        expected[(0 + h - 1) % 12] -= 1
        expected[(1 + h - 1) % 12] += 1
    assert diff == expected


def test_rahu_ketu_ignored():
    pos = _positions()
    pos_with_nodes = dict(pos, rahu=123.0, ketu=303.0)
    assert bhinnashtakavarga(pos, 0) == bhinnashtakavarga(pos_with_nodes, 0)

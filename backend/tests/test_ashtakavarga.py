"""Ashtakavarga tests — canonical table totals, SAV invariant, spot checks,
shodhana reductions, shodhya pinda, kakshya, contributor-level BAV."""

from jyotish.ashtakavarga import (BAV_TOTALS, BINDU_TABLE, GRAHA_MULT,
                                  KAKSHYA_LORDS, RASI_MULT, SAV_TOTAL,
                                  SEVEN_GRAHAS, bhinnashtakavarga,
                                  bhinnashtakavarga_detailed,
                                  ekadhipatya_shodhana, kakshya_of,
                                  kakshya_transit_favor, sarvashtakavarga,
                                  shodhya_pinda, trikona_shodhana)


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


# ---------------------------------------------------------------------------
# Trikona shodhana
# ---------------------------------------------------------------------------

def _vals(**at):
    """A 12-sign bindu row, zeros except the given sign=value pairs (s0..s11)."""
    row = [0] * 12
    for key, value in at.items():
        row[int(key[1:])] = value
    return row


def test_trikona_equal_triple_becomes_zero():
    bav = {"x": _vals(s0=5, s4=5, s8=5, s1=2, s5=3, s9=4)}
    out = trikona_shodhana(bav)
    assert out["x"][0] == out["x"][4] == out["x"][8] == 0


def test_trikona_zero_in_group_means_no_change():
    row = _vals(s1=0, s5=3, s9=4)
    out = trikona_shodhana({"x": row})
    assert [out["x"][s] for s in (1, 5, 9)] == [0, 3, 4]


def test_trikona_subtracts_group_minimum():
    out = trikona_shodhana({"x": _vals(s2=2, s6=3, s10=5)})
    assert [out["x"][s] for s in (2, 6, 10)] == [0, 1, 3]


def test_trikona_does_not_mutate_and_covers_all_groups():
    bav = bhinnashtakavarga(_positions(), lagna_sign=3)
    snapshot = {g: list(v) for g, v in bav.items()}
    out = trikona_shodhana(bav)
    assert bav == snapshot  # input untouched
    for g in SEVEN_GRAHAS:
        # After reduction every trine group either was left alone because a
        # zero was present, or now contains a zero (min subtracted / zeroed).
        for group in ((0, 4, 8), (1, 5, 9), (2, 6, 10), (3, 7, 11)):
            assert min(out[g][s] for s in group) == 0


# ---------------------------------------------------------------------------
# Ekadhipatya shodhana (Mars 0/7, Venus 1/6, Mercury 2/5, Jup 8/11, Sat 9/10)
# ---------------------------------------------------------------------------

def test_ekadhipatya_both_occupied_no_change():
    bav = {"x": _vals(s0=4, s7=2)}
    out = ekadhipatya_shodhana(bav, {"sun": 0, "moon": 7})
    assert out["x"][0] == 4 and out["x"][7] == 2


def test_ekadhipatya_one_occupied_unoccupied_leq_becomes_zero():
    # Aries occupied (4 bindus), Scorpio unoccupied with 3 <= 4 -> 0.
    out = ekadhipatya_shodhana({"x": _vals(s0=4, s7=3)}, {"sun": 0})
    assert out["x"][0] == 4 and out["x"][7] == 0


def test_ekadhipatya_one_occupied_unoccupied_greater_subtracts():
    # Taurus occupied (2), Libra unoccupied with 5 > 2 -> 5 - 2 = 3.
    out = ekadhipatya_shodhana({"x": _vals(s1=2, s6=5)}, {"moon": 1})
    assert out["x"][1] == 2 and out["x"][6] == 3


def test_ekadhipatya_both_unoccupied_equal_both_zero():
    out = ekadhipatya_shodhana({"x": _vals(s2=3, s5=3)}, {"sun": 0})
    assert out["x"][2] == 0 and out["x"][5] == 0


def test_ekadhipatya_both_unoccupied_larger_reduced_to_smaller():
    out = ekadhipatya_shodhana({"x": _vals(s8=6, s11=2)}, {"sun": 0})
    assert out["x"][8] == 2 and out["x"][11] == 2


def test_ekadhipatya_zero_sign_means_no_reduction_and_sun_moon_signs_exempt():
    # Capricorn 5, Aquarius 0: zero present -> pair untouched.
    row = _vals(s9=5, s10=0, s3=7, s4=7)  # Cancer/Leo values must survive too
    out = ekadhipatya_shodhana({"x": row}, {"sun": 0})
    assert out["x"][9] == 5 and out["x"][10] == 0
    assert out["x"][3] == 7 and out["x"][4] == 7  # not a dual-lord pair


# ---------------------------------------------------------------------------
# Shodhya pinda
# ---------------------------------------------------------------------------

def test_multipliers_exact():
    assert list(RASI_MULT) == [7, 10, 8, 4, 10, 6, 7, 8, 9, 5, 11, 12]
    assert [GRAHA_MULT[g] for g in SEVEN_GRAHAS] == [5, 5, 8, 5, 10, 7, 5]


def test_shodhya_pinda_hand_computed():
    reduced = {"sun": _vals(s0=2, s6=3)}
    graha_signs = {"sun": 0, "moon": 6, "mars": 1, "mercury": 2,
                   "jupiter": 3, "venus": 4, "saturn": 5}
    out = shodhya_pinda(reduced, graha_signs)
    # rasi: 2*RASI_MULT[0] + 3*RASI_MULT[6] = 2*7 + 3*7 = 35
    # graha: Sun in s0 -> 2*5, Moon in s6 -> 3*5, rest sit in 0-bindu signs.
    assert out["sun"] == {"rasi_pinda": 35, "graha_pinda": 25,
                          "shodhya_pinda": 60}


# ---------------------------------------------------------------------------
# Kakshya + contributor-level BAV
# ---------------------------------------------------------------------------

def test_kakshya_boundaries_and_lord_order():
    assert kakshya_of(0.0) == {"index": 0, "lord": "saturn"}
    assert kakshya_of(3.75) == {"index": 1, "lord": "jupiter"}
    assert kakshya_of(26.25) == {"index": 7, "lord": "lagna"}
    assert kakshya_of(29.999) == {"index": 7, "lord": "lagna"}
    assert kakshya_of(30.0) == {"index": 0, "lord": "saturn"}  # Taurus 0°
    assert KAKSHYA_LORDS == ("saturn", "jupiter", "mars", "sun",
                             "venus", "mercury", "moon", "lagna")


def test_detailed_bav_matches_bindu_counts():
    pos = _positions()
    bav = bhinnashtakavarga(pos, lagna_sign=3)
    detailed = bhinnashtakavarga_detailed(pos, lagna_sign=3)
    for g in SEVEN_GRAHAS:
        assert [len(detailed[g][s]) for s in range(12)] == bav[g]


def test_kakshya_transit_favor_membership():
    # Everything in Aries, lagna Aries: Sun-BAV Aries contributors are
    # exactly {sun, mars, saturn} (house-1 grantors of Sun's table).
    same = {g: 5.0 for g in SEVEN_GRAHAS}
    detailed = bhinnashtakavarga_detailed(same, lagna_sign=0)
    assert detailed["sun"][0] == {"sun", "mars", "saturn"}
    # Kakshya 0 (0°-3°45') lord = Saturn -> contributed -> favorable.
    fav = kakshya_transit_favor(detailed, "sun", 1.0)
    assert fav == {"sign": 0, "kakshya_index": 0, "kakshya_lord": "saturn",
                   "favorable": True, "bindus": 3}
    # Kakshya 1 lord = Jupiter -> did not contribute in Aries.
    assert kakshya_transit_favor(detailed, "sun", 4.0)["favorable"] is False
    # Kakshya 3 (11.25°-15°) lord = Sun -> favorable.
    assert kakshya_transit_favor(detailed, "sun", 12.0)["favorable"] is True

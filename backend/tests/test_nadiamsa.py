"""Nadiamsa (D-150) + Pushkara tests — index math, name scheme, tables."""

from jyotish.nadiamsa import (NADIAMSA_NAMES, PUSHKARA_BHAGA,
                              PUSHKARA_NAVAMSAS, d150, pushkara)


# ---------------------------------------------------------------------------
# D-150
# ---------------------------------------------------------------------------

def test_names_list_has_exactly_150_entries():
    assert len(NADIAMSA_NAMES) == 150
    assert all(isinstance(n, str) and n for n in NADIAMSA_NAMES)
    assert NADIAMSA_NAMES[0] == "Vasudha"
    assert NADIAMSA_NAMES[149] == "Parameshvari"


def test_d150_index_math_and_boundaries():
    assert d150(0.0)["index"] == 0
    assert d150(0.0)["global_index"] == 0
    assert d150(0.19)["index"] == 0        # still inside the first 12'
    assert d150(0.2)["index"] == 1         # exact boundary opens the next
    assert d150(29.999)["index"] == 149
    assert d150(29.999)["global_index"] == 149
    assert d150(30.0) == dict(d150(30.0), index=0, global_index=150, sign=1)
    assert d150(359.99)["global_index"] == 1799
    assert d150(360.0)["global_index"] == 0  # wraps


def test_d150_every_index_in_range():
    for i in range(1800):
        out = d150(i * 0.2 + 0.05)
        assert 0 <= out["index"] <= 149
        assert out["global_index"] == i


def test_d150_name_scheme_movable_fixed_dual():
    # Movable (Aries): direct 1 -> 150.
    assert d150(0.1)["name"] == "Vasudha"
    assert d150(29.9)["name"] == "Parameshvari"
    # Fixed (Taurus): reverse 150 -> 1.
    assert d150(30.1)["name"] == "Parameshvari"
    assert d150(59.9)["name"] == "Vasudha"
    # Dual (Gemini): starts at #76 (Sushitala), wraps after #150.
    assert d150(60.1)["name"] == "Sushitala"
    assert d150(60.1)["name_index"] == 75
    assert d150(60.0 + 75 * 0.2 + 0.05)["name"] == "Vasudha"  # 76th nadiamsa
    assert d150(89.9)["name_index"] == 74  # last dual nadiamsa = name #75


# ---------------------------------------------------------------------------
# Pushkara
# ---------------------------------------------------------------------------

def test_pushkara_navamsa_fire_signs_7th_and_9th():
    # Aries 20°00'-23°20' (7th navamsa) and 26°40'-30° (9th).
    assert pushkara(21.0)["is_pushkara_navamsa"] is True
    assert pushkara(21.0)["navamsa_index_in_sign"] == 6
    assert pushkara(27.0)["is_pushkara_navamsa"] is True
    assert pushkara(27.0)["navamsa_index_in_sign"] == 8
    assert pushkara(25.0)["is_pushkara_navamsa"] is False  # 8th navamsa
    assert pushkara(120.0 + 21.0)["is_pushkara_navamsa"] is True  # Leo too


def test_pushkara_navamsa_earth_air_water():
    # Earth (Taurus): 3rd (6°40'-10°) and 5th (13°20'-16°40').
    assert pushkara(30.0 + 7.0)["is_pushkara_navamsa"] is True
    assert pushkara(30.0 + 14.0)["is_pushkara_navamsa"] is True
    assert pushkara(30.0 + 11.0)["is_pushkara_navamsa"] is False
    # Air (Gemini): 6th (16°40'-20°) and 8th (23°20'-26°40').
    assert pushkara(60.0 + 17.0)["is_pushkara_navamsa"] is True
    assert pushkara(60.0 + 24.0)["is_pushkara_navamsa"] is True
    assert pushkara(60.0 + 21.0)["is_pushkara_navamsa"] is False
    # Water (Cancer): 1st (0°-3°20') and 3rd (6°40'-10°).
    assert pushkara(90.0 + 1.0)["is_pushkara_navamsa"] is True
    assert pushkara(90.0 + 8.0)["is_pushkara_navamsa"] is True
    assert pushkara(90.0 + 5.0)["is_pushkara_navamsa"] is False


def test_pushkara_bhaga_table_and_exact_degree_rule():
    assert list(PUSHKARA_BHAGA) == [21, 14, 24, 8, 19, 9, 24, 11, 23, 14, 19, 9]
    # Aries 21° = span 20°00'-21°00' of the sign.
    assert pushkara(20.5)["is_pushkara_bhaga"] is True
    assert pushkara(21.0)["is_pushkara_bhaga"] is False  # 22nd degree starts
    assert pushkara(19.9)["is_pushkara_bhaga"] is False
    # Taurus 14° -> 13°-14° in sign; Pisces 9° -> 8°-9° in sign.
    assert pushkara(30.0 + 13.2)["is_pushkara_bhaga"] is True
    assert pushkara(330.0 + 8.5)["is_pushkara_bhaga"] is True
    assert pushkara(330.0 + 9.5)["is_pushkara_bhaga"] is False


def test_pushkara_two_navamsas_per_sign():
    for elem, navs in PUSHKARA_NAVAMSAS.items():
        assert len(navs) == 2
        assert all(0 <= n <= 8 for n in navs)

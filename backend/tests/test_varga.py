"""Varga mapping unit tests — exact known mappings from the BPHS rules."""

from jyotish import varga


def test_d1_signs():
    assert varga.d1(0.0) == 0          # 0° Aries
    assert varga.d1(359.99) == 11      # late Pisces


def test_d9_boundaries():
    # 0° Aries → Aries navamsa; each 3°20' advances one sign.
    assert varga.d9(0.0) == 0
    assert varga.d9(3.34) == 1         # 2nd navamsa of Aries → Taurus
    assert varga.d9(29.99) == 8        # 9th navamsa of Aries → Sagittarius
    # Taurus (earth) starts at Capricorn.
    assert varga.d9(30.0) == 9
    # Gemini (air) starts at Libra; Cancer (water) at Cancer.
    assert varga.d9(60.0) == 6
    assert varga.d9(90.0) == 3
    # 29°59' Pisces → Pisces (last navamsa of the zodiac is vargottama-like).
    assert varga.d9(359.99) == 11


def test_d2_hora():
    assert varga.d2(10.0) == 4     # odd sign first half → Leo
    assert varga.d2(20.0) == 3     # odd sign second half → Cancer
    assert varga.d2(40.0) == 3     # even sign first half → Cancer
    assert varga.d2(50.0) == 4     # even sign second half → Leo


def test_d3_drekkana():
    assert varga.d3(5.0) == 0      # Aries 1st drekkana → Aries
    assert varga.d3(15.0) == 4     # 2nd → Leo (5th from Aries)
    assert varga.d3(25.0) == 8     # 3rd → Sagittarius (9th)


def test_d30_trimsamsa_odd_sign():
    # Aries (odd): 0-5 Aries, 5-10 Aquarius, 10-18 Sagittarius, 18-25 Gemini, 25-30 Libra
    assert varga.d30(2.0) == 0
    assert varga.d30(7.0) == 10
    assert varga.d30(14.0) == 8
    assert varga.d30(20.0) == 2
    assert varga.d30(28.0) == 6


def test_d30_trimsamsa_even_sign():
    # Taurus (even): 0-5 Taurus, 5-12 Virgo, 12-20 Pisces, 20-25 Capricorn, 25-30 Scorpio
    assert varga.d30(32.0) == 1
    assert varga.d30(38.0) == 5
    assert varga.d30(45.0) == 11
    assert varga.d30(52.0) == 9
    assert varga.d30(58.0) == 7


def test_d60_advances_from_own_sign():
    assert varga.d60(0.0) == 0
    assert varga.d60(0.6) == 1       # 2nd shashtiamsa
    assert varga.d60(29.99) == (0 + 59) % 12


def test_all_vargas_complete():
    v = varga.all_vargas(123.456)
    assert set(v) == {"D1", "D2", "D3", "D7", "D9", "D10", "D12", "D16",
                      "D20", "D24", "D27", "D30", "D40", "D45", "D60"}
    assert all(0 <= s <= 11 for s in v.values())

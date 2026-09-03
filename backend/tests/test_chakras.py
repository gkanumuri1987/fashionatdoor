"""Transit chakra tests — 28-scheme conversion, Sarvatobhadra vedha, Kota, Tripataki."""

from jyotish.chakras import (ABHIJIT_END, ABHIJIT_START, NAKSHATRAS_28,
                             kota_chakra, kota_ring_of, nak27_to_28,
                             nakshatra28_of, sarvatobhadra_vedha, tripataki,
                             vedha_partners)
from jyotish.nakshatra import SPAN

# 27-scheme nakshatra midpoint longitude (safely clear of the Abhijit window).
def _lon27(i):
    return i * SPAN + 2.0


# ── 28-scheme conversion ─────────────────────────────────────────────────────

def test_abhijit_window():
    assert nakshatra28_of(277.0) == 21                      # inside Abhijit
    assert NAKSHATRAS_28[21] == "Abhijit"
    assert nakshatra28_of(281.0) == 22                      # Shravana proper
    assert NAKSHATRAS_28[22] == "Shravana"
    assert nakshatra28_of(276.0) == 20                      # still U.Ashadha
    assert NAKSHATRAS_28[20] == "Uttara Ashadha"
    # Exact boundaries: start inclusive, end exclusive.
    assert nakshatra28_of(ABHIJIT_START) == 21
    assert nakshatra28_of(ABHIJIT_END) == 22


def test_28_scheme_ends_and_mapping():
    assert nakshatra28_of(0.5) == 0 and NAKSHATRAS_28[0] == "Ashwini"
    assert nakshatra28_of(359.9) == 27 and NAKSHATRAS_28[27] == "Revati"
    assert len(NAKSHATRAS_28) == 28
    # 27->28 index mapping: identity through U.Ashadha, +1 after.
    assert nak27_to_28(20) == 20
    assert nak27_to_28(21) == 22
    assert nak27_to_28(26) == 27


# ── Sarvatobhadra vedha ──────────────────────────────────────────────────────

def test_vedha_symmetry_all_28():
    for i in range(28):
        partners = vedha_partners(i)
        assert partners, f"nakshatra {i} has no vedha partners"
        assert i not in partners
        for j in partners:
            assert i in vedha_partners(j), f"vedha {i}->{j} not mutual"


def test_vedha_partner_count_bounded():
    for i in range(28):
        assert 1 <= len(vedha_partners(i)) <= 3


def test_sarvatobhadra_malefic_vedha_on_janma():
    # Janma Krittika (27-idx 2 -> 28-idx 2); partners = {12, 16, 26}.
    assert vedha_partners(2) == [12, 16, 26]
    res = sarvatobhadra_vedha(2, {"saturn": _lon27(16)})    # Anuradha
    assert res["janma_nakshatra"] == "Krittika"
    assert len(res["vedhas_on_janma"]) == 1
    hit = res["vedhas_on_janma"][0]
    assert hit["graha"] == "saturn"
    assert hit["from_nakshatra"] == "Anuradha"
    assert hit["nature"] == "adverse"


def test_sarvatobhadra_benefic_vedha_mixed_and_all_vedhas():
    res = sarvatobhadra_vedha(2, {"jupiter": _lon27(12), "venus": _lon27(3)})
    hits = {v["graha"]: v for v in res["vedhas_on_janma"]}
    assert set(hits) == {"jupiter"}                          # venus (Rohini) misses
    assert hits["jupiter"]["nature"] == "mixed"
    assert res["all_vedhas"]["jupiter"]["from_nakshatra"] == "Hasta"
    assert "Krittika" in res["all_vedhas"]["jupiter"]["targets"]


def test_sarvatobhadra_no_vedha_when_clear():
    res = sarvatobhadra_vedha(2, {"mars": _lon27(3), "sun": _lon27(4)})
    assert res["vedhas_on_janma"] == []


# ── Kota chakra ──────────────────────────────────────────────────────────────

def test_kota_ring_pattern_covers_28():
    rings = [kota_ring_of(o) for o in range(28)]
    # Quarter pattern repeats every 7 offsets.
    assert rings[0] == ("bahya", "entering")
    assert rings[3] == ("stambha", "entering")
    assert rings[4] == ("stambha", "exiting")
    assert rings[6] == ("prakara", "exiting")
    assert rings[7] == ("bahya", "entering")                # quarter 2 restarts
    assert rings[:7] == rings[7:14] == rings[14:21] == rings[21:28]
    names = [r for r, _ in rings]
    assert names.count("bahya") == 4
    assert names.count("prakara") == 8
    assert names.count("madhya") == 8
    assert names.count("stambha") == 8
    moves = [m for _, m in rings]
    assert moves.count("entering") == 16 and moves.count("exiting") == 12


def test_kota_placement_from_janma():
    # Janma Ashwini: a graha in the janma nakshatra sits at the outer entrance.
    res = kota_chakra(0, {"moon": _lon27(0), "saturn": _lon27(4)})
    assert res["rings"]["moon"] == {"nakshatra": "Ashwini", "offset": 0,
                                    "ring": "bahya", "moving": "entering"}
    assert res["rings"]["saturn"]["ring"] == "stambha"
    assert res["rings"]["saturn"]["moving"] == "exiting"


def test_kota_siege_alert_fires():
    # Saturn in stambha, Mars in madhya; Jupiter/Venus outside -> siege.
    res = kota_chakra(0, {"saturn": _lon27(3), "mars": _lon27(2),
                          "jupiter": _lon27(0), "venus": _lon27(6)})
    assert res["rings"]["saturn"]["ring"] == "stambha"
    assert res["rings"]["mars"]["ring"] == "madhya"
    assert res["rings"]["jupiter"]["ring"] == "bahya"
    assert res["rings"]["venus"]["ring"] == "prakara"
    assert len(res["alerts"]) == 1
    alert = res["alerts"][0]
    assert alert["type"] == "siege"
    assert alert["malefics_inside"] == ["mars", "saturn"]
    assert alert["benefics_inside"] == []


def test_kota_no_alert_when_benefic_inside_or_no_malefic():
    # Jupiter joins the inner fort -> no siege.
    res = kota_chakra(0, {"saturn": _lon27(3), "jupiter": _lon27(2)})
    assert res["alerts"] == []
    # Only benefics inside -> no siege either.
    res = kota_chakra(0, {"jupiter": _lon27(3), "saturn": _lon27(0)})
    assert res["alerts"] == []


# ── Tripataki chakra ─────────────────────────────────────────────────────────

def test_tripataki_vedha_from_trines_and_7th():
    res = tripataki(0, {"sun": 125.0,      # sign 4 = 5th house
                        "saturn": 185.0,   # sign 6 = 7th
                        "mars": 245.0,     # sign 8 = 9th
                        "jupiter": 5.0,    # sign 0 = 1st
                        "venus": 35.0})    # sign 1 = 2nd -> no vedha
    hits = {v["graha"]: v["house_from_moon"] for v in res["vedha_grahas"]}
    assert hits == {"sun": 5, "saturn": 7, "mars": 9, "jupiter": 1}
    assert res["nature"] == "adverse"


def test_tripataki_clear_and_moon_never_self_pierces():
    res = tripataki(0, {"venus": 35.0, "mercury": 65.0, "moon": 5.0})
    assert res["vedha_grahas"] == []
    assert res["nature"] == "clear"


def test_tripataki_year_moon_override_and_mixed():
    # Reference sign overridden to 4; Jupiter in sign 4 -> 1st-house vedha.
    res = tripataki(0, {"jupiter": 125.0}, current_year_moon_sign=4)
    assert res["moon_sign"] == 4
    assert res["vedha_grahas"] == [{"graha": "jupiter", "sign": 4,
                                    "house_from_moon": 1, "nature": "mixed"}]
    assert res["nature"] == "mixed"

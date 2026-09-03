"""Kundli Milan tests — table integrity + directional rules + end-to-end match."""

from datetime import date, time

import pytest

from jyotish import milan
from jyotish.chart import compute_chart

# ── Table integrity ──────────────────────────────────────────────────────────

def test_yoni_matrix_is_symmetric_with_diagonal_4():
    m = milan._YONI_MATRIX
    assert len(m) == 14 and all(len(r) == 14 for r in m)
    for i in range(14):
        assert m[i][i] == 4
        for j in range(14):
            assert m[i][j] == m[j][i]


def test_yoni_sworn_enemy_pairs_are_zero():
    a = milan._YONI_ANIMALS
    enemies = [("horse", "buffalo"), ("elephant", "lion"), ("sheep", "monkey"),
               ("serpent", "mongoose"), ("dog", "deer"), ("cat", "rat"), ("cow", "tiger")]
    for x, y in enemies:
        assert milan._YONI_MATRIX[a.index(x)][a.index(y)] == 0


def test_every_nakshatra_has_yoni_gana_nadi():
    for nak in range(27):
        assert nak in milan._NAK_YONI
        milan._gana(nak)
        milan._nadi(nak)


def test_gana_direction_sensitive():
    assert milan._GANA_MATRIX["deva"]["manushya"] == 6
    assert milan._GANA_MATRIX["manushya"]["deva"] == 5
    assert milan._GANA_MATRIX["manushya"]["rakshasa"] == 0


def test_tara_counts():
    # Same nakshatra → tara 1 (Janma) — benign.
    assert milan._tara_count(0, 0) == 1
    # 3rd from Ashwini is Krittika → Vipat (bad).
    assert milan._tara_count(0, 2) == 3
    # Wraps: from Revati (26) to Bharani (1) is 3rd.
    assert milan._tara_count(26, 1) == 3


def test_vashya_groups_resolve_half_signs():
    # Sagittarius first half = manava, second half = chatushpada.
    assert milan._vashya_group(8 * 30 + 10.0) == "manava"
    assert milan._vashya_group(8 * 30 + 20.0) == "chatushpada"
    # Capricorn first half quadruped, second half water.
    assert milan._vashya_group(9 * 30 + 10.0) == "chatushpada"
    assert milan._vashya_group(9 * 30 + 20.0) == "jalachara"


# ── End-to-end ───────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def charts():
    boy = compute_chart(date(1990, 5, 15), time(10, 30),
                        lat=17.385, lng=78.4867, tz_name="Asia/Kolkata")
    girl = compute_chart(date(1992, 11, 3), time(6, 45),
                         lat=13.0827, lng=80.2707, tz_name="Asia/Kolkata")
    return boy, girl


def test_match_shape_and_bounds(charts):
    boy, girl = charts
    m = milan.match(boy, girl)
    assert m["schema"] == "MilanV1"
    assert len(m["kootas"]) == 8
    assert 0 <= m["total"] <= 36
    maxes = {k["koota"]: k["max"] for k in m["kootas"]}
    assert maxes == {"varna": 1, "vashya": 2, "tara": 3, "yoni": 4,
                     "graha_maitri": 5, "gana": 6, "bhakoot": 7, "nadi": 8}
    for k in m["kootas"]:
        assert 0 <= k["points"] <= k["max"]
    assert m["verdict"] in ("excellent", "very_good", "acceptable", "below_threshold")


def test_match_self_pairing_scores_high(charts):
    """A chart matched with itself: same everything → most kootas max out,
    but same nadi is a dosha (0) — classic result."""
    boy, _ = charts
    m = milan.match(boy, boy)
    by_koota = {k["koota"]: k for k in m["kootas"]}
    assert by_koota["yoni"]["points"] == 4
    assert by_koota["gana"]["points"] == 6
    assert by_koota["graha_maitri"]["points"] == 5
    assert by_koota["nadi"]["points"] == 0 and by_koota["nadi"]["dosha"]
    assert by_koota["bhakoot"]["points"] == 7  # same sign is not a dosha pair


def test_manglik_reported_for_both(charts):
    boy, girl = charts
    m = milan.match(boy, girl)
    for side in ("boy", "girl"):
        mg = m[side]["manglik"]
        assert "is_manglik" in mg
        assert 1 <= mg["from_lagna"]["house"] <= 12
        assert 1 <= mg["from_moon"]["house"] <= 12


# ── Dashakoota ───────────────────────────────────────────────────────────────

def test_rajju_classification():
    from jyotish.milan import _rajju_of, dashakoota
    assert _rajju_of(0) == "pada"      # Ashwini
    assert _rajju_of(4) == "siro"      # Mrigashira
    assert _rajju_of(13) == "siro"     # Chitra
    assert _rajju_of(3) == "kantha"    # Rohini
    # All 27 nakshatras classified.
    assert all(_rajju_of(i) != "unknown" for i in range(27))
    d = dashakoota(4, 13)              # both siro
    assert d["rajju"]["dosha"] and d["rajju"]["severity"] == "grave"


def test_vedha_pairs_symmetric():
    from jyotish.milan import dashakoota
    assert dashakoota(0, 17)["vedha"]["dosha"]     # Ashwini-Jyeshtha
    assert dashakoota(17, 0)["vedha"]["dosha"]
    assert not dashakoota(0, 5)["vedha"]["dosha"]


def test_mahendra_and_stree_deergha():
    from jyotish.milan import dashakoota
    # Boy 3 nakshatras beyond girl +1 inclusive = 4 → mahendra.
    d = dashakoota(3, 0)
    assert d["mahendra"]["present"] and d["mahendra"]["count"] == 4
    assert not d["stree_deergha"]["present"]
    d2 = dashakoota(14, 0)             # count 15 > 13
    assert d2["stree_deergha"]["present"]

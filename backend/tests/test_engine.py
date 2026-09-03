"""Engine integration tests — real ephemeris anchors + full-chart invariants.

Astronomical anchors are events whose configuration is a public fact (eclipses,
full moons, published ayanamsa values), so they validate the ephemeris + sidereal
pipeline without trusting our own output. The full-chart snapshot pins engine
output for regression; its values are additionally cross-checked manually against
Jagannatha Hora (see scripts/verify_chart.py).
"""

from datetime import date, datetime, time, timezone

import pytest

from jyotish.chart import compute_chart, transit_report
from jyotish.ephemeris import ayanamsa_value, julian_day_ut, sidereal_positions
from jyotish.panchanga import panchanga
from jyotish.schema import ChartV1


def _jd(y, m, d, hh=0, mm=0):
    return julian_day_ut(datetime(y, m, d, hh, mm, tzinfo=timezone.utc))


# ── Astronomical anchors ─────────────────────────────────────────────────────

def test_lahiri_ayanamsa_2000():
    # Published Lahiri value near J2000 ≈ 23°51' (23.85°).
    ay = ayanamsa_value(_jd(2000, 1, 1, 12), "lahiri")
    assert 23.7 < ay < 24.0


def test_lahiri_ayanamsa_2024():
    # ≈ 24°12' in 2024.
    ay = ayanamsa_value(_jd(2024, 1, 1), "lahiri")
    assert 24.0 < ay < 24.4


def test_solar_eclipse_2020_is_amavasya():
    # Annular eclipse peak 2020-06-21 ~06:40 UTC — Sun/Moon conjunct.
    jd = _jd(2020, 6, 21, 6, 40)
    pos = sidereal_positions(jd)
    sep = abs((pos["moon"]["lon"] - pos["sun"]["lon"]) % 360.0)
    sep = min(sep, 360.0 - sep)
    assert sep < 1.0
    p = panchanga(pos["sun"]["lon"], pos["moon"]["lon"], date(2020, 6, 21))
    assert p["tithi"]["name"] == "Amavasya"


def test_full_moon_2024_04_23():
    # Purnima (Hanuman Jayanti) 2024-04-23; full moon ~23:49 IST.
    jd = _jd(2024, 4, 23, 12, 0)
    pos = sidereal_positions(jd)
    p = panchanga(pos["sun"]["lon"], pos["moon"]["lon"], date(2024, 4, 23))
    assert p["tithi"]["name"] == "Purnima"


def test_saturn_slow_moon_fast():
    jd = _jd(2000, 6, 1)
    pos = sidereal_positions(jd)
    assert abs(pos["saturn"]["speed"]) < 0.15
    assert 11.0 < abs(pos["moon"]["speed"]) < 16.0


# ── Full chart invariants ────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def chart():
    return compute_chart(date(1990, 5, 15), time(10, 30),
                         lat=17.385, lng=78.4867, tz_name="Asia/Kolkata")


def test_chart_validates_against_schema(chart):
    ChartV1.model_validate(chart)


def test_chart_basic_invariants(chart):
    assert len(chart["grahas"]) == 9
    assert all(0 <= g["lon"] < 360 for g in chart["grahas"].values())
    assert all(1 <= g["house"] <= 12 for g in chart["grahas"].values())
    assert len(chart["bhavas"]) == 12
    # Whole-sign: each bhava sign advances by one from lagna.
    lagna = chart["lagna"]["sign"]
    for b in chart["bhavas"]:
        assert b["sign"] == (lagna + b["house"] - 1) % 12
    # Rahu/Ketu exactly opposite.
    sep = abs(chart["grahas"]["rahu"]["lon"] - chart["grahas"]["ketu"]["lon"])
    assert min(sep, 360 - sep) == pytest.approx(180.0, abs=1e-6)
    # Occupants agree with graha houses.
    for b in chart["bhavas"]:
        for g in b["occupants"]:
            assert chart["grahas"][g]["house"] == b["house"]


def test_chart_utc_conversion(chart):
    assert chart["input"]["utc"].startswith("1990-05-15T05:00:00")
    assert chart["input"]["utc_offset_hours"] == 5.5


def test_dasha_first_lord_matches_moon_nakshatra(chart):
    from jyotish.constants import nakshatra_lord
    nak = chart["grahas"]["moon"]["nakshatra"]
    assert chart["vimshottari"]["mahadashas"][0]["lord"] == nakshatra_lord(nak["index"])
    assert chart["vimshottari"]["moon_nakshatra"] == nak["name"]


def test_transit_report_shape(chart):
    rep = transit_report(chart, datetime(2026, 8, 25, tzinfo=timezone.utc))
    assert len(rep["transits"]) == 9
    sat = rep["transits"]["saturn"]["house_from_moon"]
    assert rep["sade_sati"]["active"] == (sat in (12, 1, 2))


def test_determinism(chart):
    again = compute_chart(date(1990, 5, 15), time(10, 30),
                          lat=17.385, lng=78.4867, tz_name="Asia/Kolkata")
    # current_dasha depends on "now" — exclude it, everything else identical.
    a = {k: v for k, v in chart.items() if k != "current_dasha"}
    b = {k: v for k, v in again.items() if k != "current_dasha"}
    assert a == b


def test_ayanamsa_changes_positions():
    kwargs = dict(lat=17.385, lng=78.4867, tz_name="Asia/Kolkata")
    lahiri = compute_chart(date(1990, 5, 15), time(10, 30), ayanamsa="lahiri", **kwargs)
    kp = compute_chart(date(1990, 5, 15), time(10, 30), ayanamsa="kp", **kwargs)
    assert lahiri["grahas"]["sun"]["lon"] != kp["grahas"]["sun"]["lon"]
    # KP ayanamsa differs from Lahiri by a few arc-minutes only.
    diff = abs(lahiri["ayanamsa_value"] - kp["ayanamsa_value"])
    assert 0.0 < diff < 0.3


def test_pre_1900_birth_computes():
    # Gandhi's birth data (1869) — exercises the pre-1900 + LMT-era path.
    c = compute_chart(date(1869, 10, 2), time(7, 12),
                      lat=21.6417, lng=69.6293, tz_name="Asia/Kolkata")
    ChartV1.model_validate(c)
    assert len(c["grahas"]) == 9


# ── Audit fixes (dignity degree-partition, mahapurusha-from-moon) ────────────

def test_dignity_degree_partition_in_exaltation_sign():
    from jyotish.dignity import dignity_of
    # Moon in Taurus: 0-3° exalted, 3-30° moolatrikona (BPHS partition).
    assert dignity_of("moon", 30.0 + 1.0) == "exalted"
    assert dignity_of("moon", 30.0 + 10.0) == "moolatrikona"
    # Mercury in Virgo: exalted early, MT 16-20°, own 20-30°.
    assert dignity_of("mercury", 150.0 + 5.0) == "exalted"
    assert dignity_of("mercury", 150.0 + 18.0) == "moolatrikona"
    assert dignity_of("mercury", 150.0 + 25.0) == "own"
    # Whole-sign behaviour intact where MT is elsewhere.
    assert dignity_of("sun", 0.0 + 25.0) == "exalted"       # Sun anywhere in Aries
    assert dignity_of("saturn", 180.0 + 5.0) == "exalted"    # Saturn in Libra
    assert dignity_of("saturn", 300.0 + 5.0) == "moolatrikona"
    assert dignity_of("saturn", 300.0 + 25.0) == "own"


def test_d30_boundary_rounds_up():
    from jyotish import varga
    # Exactly 5° in an odd sign belongs to the SECOND trimsamsa (Aquarius).
    assert varga.d30(5.0) == 10
    assert varga.d30(4.99) == 0


def test_mahapurusha_from_moon_kendra():
    from jyotish.yogas import detect_yogas
    # Saturn own-sign Capricorn; Moon in Libra → Saturn is 4th from Moon
    # (kendra) but 2nd from a Sagittarius lagna (not a lagna kendra).
    grahas = {}
    placements = {
        "sun": 0, "moon": 6, "mars": 1, "mercury": 2, "jupiter": 4,
        "venus": 5, "saturn": 9, "rahu": 10, "ketu": 4,
    }
    lagna = 8  # Sagittarius
    for g, sign in placements.items():
        grahas[g] = {"lon": sign * 30 + 15.0, "sign": sign,
                     "house": (sign - lagna) % 12 + 1}
    yogas = detect_yogas(grahas, lagna)
    keys = {y["key"] for y in yogas}
    assert "mahapurusha_sasa" in keys


# ── v1.1 judgment layer integration ──────────────────────────────────────────

def test_chart_v11_strength_layer(chart):
    # Shadbala present for all 7 classical grahas with sane bounds.
    assert set(chart["shadbala_summary"]) == {"sun", "moon", "mars", "mercury",
                                              "jupiter", "venus", "saturn"}
    for g, e in chart["shadbala_summary"].items():
        assert 2.0 < e["rupas"] < 15.0
    # Ashtakavarga invariants.
    av = chart["ashtakavarga"]
    assert av["sarva_total"] == 337
    assert len(av["sarva"]) == 12 and all(0 <= b <= 8 * 8 for b in av["sarva"])
    assert set(av["bhinna"]) == set(chart["shadbala_summary"])
    # Bhava SAV bindus mirror the sarva of the bhava's sign.
    for b in chart["bhavas"]:
        assert b["sav_bindus"] == av["sarva"][b["sign"]]


def test_chart_v11_functional_and_avasthas(chart):
    fn = chart["functional_lords"]
    assert len(fn["maraka_lords"]) >= 1
    assert fn["badhaka"]["lord"] in chart["grahas"]
    # Cancer lagna (this chart): movable → badhaka house 11.
    assert fn["badhaka"]["house"] == 11
    for g, gd in chart["grahas"].items():
        a = gd["avasthas"]
        assert a["baladi"] in ("bala", "kumara", "yuva", "vriddha", "mrita")
        assert a["jagradadi"] in ("jagrat", "swapna", "sushupti")
        assert isinstance(a["vargottama"], bool)
    # Sunrise-based vara present with basis marker.
    assert chart["panchanga"]["vara"]["basis"] == "sunrise"
    assert chart["sunrise_utc"] is not None


def test_yoga_strength_annotated(chart):
    with_grahas = [y for y in chart["yogas"] if y.get("grahas")]
    assert with_grahas, "expected at least one yoga with participants"
    for y in with_grahas:
        if any(g in chart["shadbala_summary"] for g in y["grahas"]):
            assert "strength_ratio" in y and y["strength_ratio"] > 0


def test_dictums_carry_weights(chart):
    import sys
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))
    from ai.retrieval import dictums_for_chart
    dictums = dictums_for_chart(chart)
    weighted = [d for d in dictums if "weight" in d]
    assert len(weighted) >= 5, "graha and yoga dictums should carry strength weights"
    assert all(0.0 < d["weight"] <= 2.0 for d in weighted)


def test_pre_sunrise_birth_takes_previous_vara():
    # 03:00 IST birth — before sunrise, so the vara is the PREVIOUS weekday.
    c = compute_chart(date(1990, 5, 15), time(3, 0),
                      lat=17.385, lng=78.4867, tz_name="Asia/Kolkata")
    # 1990-05-15 was a Tuesday; pre-sunrise → Monday's vara (Somavara).
    assert c["panchanga"]["vara"]["name"] == "Somavara"
    day = compute_chart(date(1990, 5, 15), time(10, 30),
                        lat=17.385, lng=78.4867, tz_name="Asia/Kolkata")
    assert day["panchanga"]["vara"]["name"] == "Mangalavara"


# ── v1.2 Tier-2 layers in the chart ─────────────────────────────────────────

def test_chart_v12_jaimini_kp_chalita(chart):
    jm = chart["jaimini"]
    ks = jm["chara_karakas"]["karakas"]
    assert set(ks) == {"AK", "AmK", "BK", "MK", "PiK", "PK", "GK", "DK"}
    assert "ketu" not in [k["graha"] for k in ks.values()]
    assert jm["arudha_padas"]["AL"] == jm["arudha_padas"]["A1"]
    assert jm["ishta_devata"]["deity"]
    assert len(jm["chara_dasha"]) == 12
    ch = chart["bhava_chalita"]
    assert len(ch["houses"]) == 12 and len(ch["grahas"]) == 9
    kp = chart["kp"]
    assert len(kp["cusps"]) == 12
    for g, e in kp["planets"].items():
        assert e["star_lord"] and e["sub_lord"] and e["sub_sub_lord"]
    assert chart["use_chandra_lagna"] is False


def test_lagna_sensitivity_bands():
    exact = compute_chart(date(1990, 5, 15), time(10, 30),
                          lat=17.385, lng=78.4867, tz_name="Asia/Kolkata")
    assert exact["lagna_sensitivity"] is None
    approx = compute_chart(date(1990, 5, 15), time(10, 30),
                           lat=17.385, lng=78.4867, tz_name="Asia/Kolkata",
                           time_accuracy="approximate")
    ls = approx["lagna_sensitivity"]
    assert ls["band_minutes"] == 30 and len(ls["lagna_signs_across_band"]) == 3
    unknown = compute_chart(date(1990, 5, 15), time(10, 30),
                            lat=17.385, lng=78.4867, tz_name="Asia/Kolkata",
                            time_accuracy="unknown")
    assert unknown["lagna_sensitivity"]["band_minutes"] == 180
    # ±3h from 10:30 IST sweeps several signs — must flag instability.
    assert not unknown["lagna_sensitivity"]["stable"]

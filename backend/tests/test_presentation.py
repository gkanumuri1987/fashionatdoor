"""ReadingPageV1 presentation-contract tests."""

from datetime import date, time

import pytest

from jyotish.chart import compute_chart

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ai.presentation import reading_page


@pytest.fixture(scope="module")
def page():
    chart = compute_chart(date(1990, 5, 15), time(10, 30),
                          lat=17.385, lng=78.4867, tz_name="Asia/Kolkata")
    return reading_page(chart, "en")


def test_rule1_numbers_become_words(page):
    for g, bar in page["strength_bars"]["grahas"].items():
        assert bar["level"] in ("strong", "balanced", "thin")
        assert 0 <= bar["bar_percent"] <= 100
        assert "rupas" in bar["why"]           # raw number only in the why layer
    for h, hb in page["strength_bars"]["houses"].items():
        assert hb["level"] in ("supportive", "neutral", "thin")


def test_rule2_every_claim_has_receipt(page):
    assert len(page["claims"]) >= 10
    for c in page["claims"]:
        assert c["claim"] and c["chart_condition"] and c["source"]
        assert c["strength"] in ("full", "firm", "moderate", "thin")
        assert isinstance(c["cancellations"], list)


def test_rule3_single_verdict_per_topic(page):
    for topic, v in page["verdicts"].items():
        assert v["verdict"] in ("supportive", "mixed", "challenging")
        assert v["views_resolved"]              # competing views listed, resolved


def test_rule4_timeline(page):
    t = page["timeline"]
    assert len(t["bands"]) == 9
    assert sum(1 for b in t["bands"] if b["current"]) == 1
    assert t["current_sentence"] and "until" in t["current_sentence"]
    assert t["next_change"]


def test_rule5_glosses_localized():
    chart = compute_chart(date(1990, 5, 15), time(10, 30),
                          lat=17.385, lng=78.4867, tz_name="Asia/Kolkata")
    te = reading_page(chart, "te")["glosses"]
    assert te["yogakaraka"] == "మీ కీలక గ్రహం"


def test_rule6_uncertainty_for_inexact_time():
    chart = compute_chart(date(1990, 5, 15), time(10, 30),
                          lat=17.385, lng=78.4867, tz_name="Asia/Kolkata",
                          time_accuracy="unknown")
    notes = reading_page(chart)["uncertainty"]
    assert any("tentative" in n for n in notes)


def test_rule7_depth_levels(page):
    assert set(page["depth"]) == {"plain", "why", "tables"}

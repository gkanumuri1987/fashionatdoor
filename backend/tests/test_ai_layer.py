"""AI-layer tests that need NO API key: corpus integrity, deterministic
retrieval, guardrail scrubbing, palm session store retention rules."""

import time as _time
from datetime import date, time

import pytest

from ai import guardrails, retrieval
from jyotish.chart import compute_chart
from store import palm_sessions


@pytest.fixture(scope="module")
def chart():
    return compute_chart(date(1990, 5, 15), time(10, 30),
                         lat=17.385, lng=78.4867, tz_name="Asia/Kolkata")


# ── Corpus integrity ─────────────────────────────────────────────────────────

def test_corpus_covers_all_lagnas_and_placements():
    lagna = retrieval._load("lagna")
    assert set(lagna) == set(range(12))
    bhava = retrieval._load("graha_in_bhava")
    for g in ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"):
        assert set(bhava[g]) == set(range(1, 13)), f"{g} missing houses"
    nak = retrieval._load("nakshatra")
    assert set(nak) == set(range(27))
    dasha = retrieval._load("dasha")
    assert set(dasha) == {"sun", "moon", "mars", "mercury", "jupiter",
                          "venus", "saturn", "rahu", "ketu"}
    arch = retrieval._load("purana_archetypes")
    for g, entry in arch.items():
        assert entry.get("story") and entry.get("epic_figure") and entry.get("remedies"), g


# ── Retrieval is deterministic and complete ──────────────────────────────────

def test_retrieval_triggers_for_every_graha(chart):
    dictums = retrieval.dictums_for_chart(chart)
    triggers = " | ".join(d["trigger"] for d in dictums)
    for g in chart["grahas"]:
        assert f"{g} in house" in triggers
    assert "lagna" in triggers
    assert "moon nakshatra" in triggers
    # Yogas detected in this chart must each retrieve a dictum.
    for y in chart["yogas"]:
        assert y["name"].split(" ")[0].lower() in triggers.lower() or y["key"] in triggers


def test_archetypes_cover_pivotal_grahas(chart):
    arch = retrieval.archetypes_for_chart(chart)
    roles = {a["role"] for a in arch}
    assert "lagna lord" in roles
    grahas = {a["graha"] for a in arch}
    assert chart["lagna"]["lord"] in grahas


# ── Guardrails ───────────────────────────────────────────────────────────────

def test_scrub_removes_death_prediction():
    out = guardrails.scrub("You are kind. You will die in 2031. Jupiter blesses you.")
    assert "die" not in out["text"].lower()
    assert out["violations"]
    assert "Jupiter blesses you" in out["text"]


def test_scrub_removes_medical_and_investment():
    out = guardrails.scrub(
        "Saturn teaches patience. You will develop cancer next year. "
        "You should invest in stocks now. Keep a steady routine.")
    assert "cancer" not in out["text"].lower()
    assert "invest in stocks" not in out["text"].lower()
    assert len(out["violations"]) == 2
    assert "steady routine" in out["text"]


def test_scrub_appends_disclaimer():
    out = guardrails.scrub("A gentle reading.")
    assert "not a substitute" in out["text"]


def test_refuse_topic():
    assert guardrails.refuse_topic("when will I die?") is not None
    assert guardrails.refuse_topic("which stock should I buy") is not None
    assert guardrails.refuse_topic("tell me about my career") is None


# ── Palm session store ───────────────────────────────────────────────────────

def test_palm_session_lifecycle(tmp_path, monkeypatch):
    monkeypatch.setattr(palm_sessions, "_DIR", tmp_path)
    s = palm_sessions.create_session(now=1000.0)
    token = s["token"]
    assert palm_sessions.get_session(token, now=1000.0)["status"] == "awaiting_photo"
    # Expired → gone.
    assert palm_sessions.get_session(token, now=1000.0 + palm_sessions.TTL_SECONDS + 1) is None
    # Result save only stores derived JSON (no image bytes anywhere in the dir).
    palm_sessions.save_result(token, {"usable": True, "reading": "..."}, now=2000.0)
    got = palm_sessions.get_session(token, now=2000.0)
    assert got["status"] == "complete"
    files = list(tmp_path.iterdir())
    assert all(f.suffix == ".json" for f in files)


def test_palm_sweep(tmp_path, monkeypatch):
    monkeypatch.setattr(palm_sessions, "_DIR", tmp_path)
    palm_sessions.create_session(now=0.0)        # long expired
    # Creating a new session auto-sweeps the expired one.
    palm_sessions.create_session(now=_time.time())
    assert len(list(tmp_path.glob("*.json"))) == 1
    # Direct sweep is idempotent afterwards.
    assert palm_sessions.sweep_expired() == 0


def test_invalid_token_rejected():
    assert palm_sessions.get_session("../../etc/passwd") is None
    assert palm_sessions.get_session("zzz") is None

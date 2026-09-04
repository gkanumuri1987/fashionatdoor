"""Deterministic palmistry interpretation tests (no API key / no vision)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from palmistry.rules import interpret


def _features(**over):
    base = {
        "usable": True, "hand": "right",
        "hand_shape": {"type": "water"},
        "major_lines": {
            "heart": {"visible": True, "length": "long", "depth": "deep", "curve": "curved"},
            "head": {"visible": True, "length": "medium", "depth": "moderate", "curve": "curved"},
            "life": {"visible": True, "depth": "deep", "curve": "curved"},
            "fate": {"visible": True},
            "sun": {"visible": False},
            "mercury": {"visible": False},
        },
        "mounts": {"venus": "prominent", "jupiter": "developed", "saturn": "flat"},
        "special_marks": ["star on apollo"],
    }
    base.update(over)
    return base


def test_findings_carry_classical_meaning_and_source():
    out = interpret(_features())
    assert out["schema"] == "PalmReadingV1"
    assert out["hand_element"]["element"] == "water"
    # every finding has a meaning + a Samudrika source
    assert out["findings"]
    assert all(f.get("meaning") and f.get("source") for f in out["findings"])
    # the heart line's curve+length meaning is composed, not raw
    heart = next(f for f in out["findings"] if f["feature"] == "Heart line")
    assert "demonstrative" in heart["meaning"] or "warm" in heart["meaning"]


def test_life_line_never_lifespan():
    out = interpret(_features())
    life = next(f for f in out["findings"] if f["feature"] == "Life line")
    assert "NEVER indicates lifespan" in life["caveat"]
    assert "vitality" in out["life_line_rule"].lower()


def test_absent_fate_line_is_reassuring_not_a_lack():
    out = interpret(_features(major_lines={
        "heart": {"visible": True, "curve": "straight"},
        "fate": {"visible": False},
    }))
    fate = next(f for f in out["findings"] if f["feature"].startswith("Fate line"))
    assert fate["observation"] == "faint or absent"
    assert "never a lack" in fate["meaning"]


def test_mounts_and_marks_mapped():
    out = interpret(_features())
    venus = next(f for f in out["findings"] if "Venus" in f["feature"])
    assert "vitality" in venus["meaning"] or "affection" in venus["meaning"]
    assert out["special_marks"]
    assert "culmination" in out["special_marks"][0]["meaning"] or \
           "good fortune" in out["special_marks"][0]["meaning"]


def test_unknown_hand_shape_omitted_gracefully():
    out = interpret({"hand": "unknown", "hand_shape": {"type": "unknown"},
                     "major_lines": {}, "mounts": {}, "special_marks": []})
    assert out["hand_element"] is None
    assert out["findings"] == []  # nothing invented
    assert out["disclaimer"]

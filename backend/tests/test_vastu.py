"""Deterministic Vastu rules tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vastu.rules import ZONES, evaluate


def test_classical_placements():
    r = evaluate([
        {"label": "Kitchen", "type": "kitchen", "zone": "SE"},
        {"label": "Pooja", "type": "pooja", "zone": "NE"},
        {"label": "Master", "type": "master_bedroom", "zone": "SW"},
        {"label": "Main door", "type": "entrance", "zone": "E"},
    ])
    assert all(f["verdict"] in ("excellent", "good") for f in r["findings"])
    assert r["brahmasthan"]["blocked_by"] is None
    assert r["score"] > 0


def test_grave_placements_carry_remedies():
    r = evaluate([{"label": "Kitchen", "type": "kitchen", "zone": "NE"},
                  {"label": "Toilet", "type": "toilet", "zone": "NE"}])
    for f in r["findings"]:
        assert f["verdict"] == "grave"
        assert f["classical_position"]
        assert "soft_remedy" in f


def test_brahmasthan_block():
    r = evaluate([{"label": "WC", "type": "toilet", "zone": "center"}])
    assert r["brahmasthan"]["blocked_by"] == "toilet"


def test_unknown_room_skipped():
    r = evaluate([{"label": "???", "type": "observatory", "zone": "N"},
                  {"label": "Bad zone", "type": "kitchen", "zone": "UP"}])
    assert all(f["verdict"] == "unknown" for f in r["findings"])


def test_zone_list_complete():
    assert len(ZONES) == 16

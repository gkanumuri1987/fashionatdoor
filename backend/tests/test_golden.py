"""Golden-chart regression suite.

Every case in tests/golden/charts.json is recomputed from its raw birth input
and deep-compared against the pinned snapshot. ANY unintended change to the
engine math fails loudly here. The snapshots are engine output (self-consistent
regression anchors, spot-verified by eye against Jagannatha Hora) — a
deliberate change requires bumping jyotish.ENGINE_VERSION and regenerating via
scripts/make_golden.py.

Cases pinned as {"error": ...} document a known failure mode (e.g. the polar
Placidus/houses degeneracy at Tromsø) — the test asserts the SAME error
persists rather than skipping, so a silent behavior change is still caught.
"""

from __future__ import annotations

import importlib.util
import json
from datetime import date, time
from pathlib import Path

import pytest

import jyotish
from jyotish.chart import compute_chart

GOLDEN_PATH = Path(__file__).resolve().parent / "golden" / "charts.json"
REPO_ROOT = Path(__file__).resolve().parents[2]
MAKE_GOLDEN = REPO_ROOT / "scripts" / "make_golden.py"

# Floats compared via pytest.approx: longitudes/degrees at abs=1e-4,
# everything else at abs=1e-5.
_LON_KEYS = {"lon", "mc", "lagna_lon", "deg_in_sign"}
_ABS_LON = 1e-4
_ABS_FLOAT = 1e-5


def _load_reduce_chart():
    """Import reduce_chart from scripts/make_golden.py (single source of truth
    for the snapshot shape — no drift between generator and test)."""
    spec = importlib.util.spec_from_file_location("make_golden", MAKE_GOLDEN)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.reduce_chart


def _load_golden() -> dict:
    with open(GOLDEN_PATH, encoding="utf-8") as f:
        return json.load(f)


_GOLDEN = _load_golden()
_REDUCE = _load_reduce_chart()
_CASES = _GOLDEN["cases"]


def _assert_deep_equal(expected, actual, path: str = "$"):
    if isinstance(expected, float) or isinstance(actual, float):
        assert isinstance(actual, (int, float)) and isinstance(expected, (int, float)), \
            f"{path}: type mismatch — expected {expected!r}, got {actual!r}"
        leaf = path.rsplit(".", 1)[-1].split("[")[0]
        tol = _ABS_LON if leaf in _LON_KEYS else _ABS_FLOAT
        assert actual == pytest.approx(expected, abs=tol), \
            f"{path}: expected {expected!r}, got {actual!r} (abs tol {tol})"
    elif isinstance(expected, dict):
        assert isinstance(actual, dict), f"{path}: expected dict, got {type(actual).__name__}"
        assert sorted(actual.keys()) == sorted(expected.keys()), \
            f"{path}: key set changed — expected {sorted(expected)}, got {sorted(actual)}"
        for k in expected:
            _assert_deep_equal(expected[k], actual[k], f"{path}.{k}")
    elif isinstance(expected, list):
        assert isinstance(actual, list), f"{path}: expected list, got {type(actual).__name__}"
        assert len(actual) == len(expected), \
            f"{path}: length changed — expected {len(expected)}, got {len(actual)}"
        for i, (e, a) in enumerate(zip(expected, actual)):
            _assert_deep_equal(e, a, f"{path}[{i}]")
    else:
        assert actual == expected, f"{path}: expected {expected!r}, got {actual!r}"


def _compute(case: dict) -> dict:
    inp = case["input"]
    y, mo, d = (int(x) for x in inp["date"].split("-"))
    hh, mm = (int(x) for x in inp["time"].split(":"))
    return compute_chart(date(y, mo, d), time(hh, mm),
                         inp["lat"], inp["lng"], tz_name=inp["tz"])


@pytest.mark.parametrize("case", _CASES, ids=[c["id"] for c in _CASES])
def test_golden_chart(case):
    if "error" in case:
        # Documented failure mode — assert the SAME error persists.
        with pytest.raises(Exception) as excinfo:
            _compute(case)
        actual = f"{type(excinfo.value).__name__}: {excinfo.value}"
        assert actual == case["error"], (
            f"{case['id']}: failure mode changed — golden pinned "
            f"{case['error']!r}, engine now raises {actual!r}. If this is an "
            f"intentional fix, bump ENGINE_VERSION and regenerate the goldens."
        )
        return

    chart = _compute(case)
    snapshot = _REDUCE(chart)
    _assert_deep_equal(case["snapshot"], snapshot, path=f"$.{case['id']}")


def test_golden_file_meta():
    assert GOLDEN_PATH.exists(), "golden charts.json is missing — run scripts/make_golden.py"
    assert len(_CASES) >= 20, f"expected >= 20 golden cases, found {len(_CASES)}"
    assert _GOLDEN["engine_version"] == jyotish.ENGINE_VERSION, (
        f"golden file was generated for engine {_GOLDEN['engine_version']!r} but "
        f"jyotish.ENGINE_VERSION is {jyotish.ENGINE_VERSION!r} — a version bump "
        f"requires deliberately regenerating via scripts/make_golden.py"
    )
    assert "Jagannatha Hora" in _GOLDEN.get("note", ""), \
        "golden header must carry the spot-verification / regeneration note"
    ids = [c["id"] for c in _CASES]
    assert len(ids) == len(set(ids)), "duplicate case ids in golden file"

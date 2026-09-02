"""Deterministic dictum retrieval — chart JSON → the classical lines it satisfies.

No embeddings, no search: plain condition matching, so every statement in a
reading is traceable to a corpus entry the chart actually triggered.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

CORPUS_DIR = Path(__file__).resolve().parent / "corpus"


@lru_cache(maxsize=None)
def _load(name: str) -> dict:
    with open(CORPUS_DIR / f"{name}.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def dictums_for_chart(chart: dict) -> list[dict]:
    """Every corpus dictum this chart triggers, tagged with why."""
    out: list[dict] = []

    lagna = _load("lagna").get(chart["lagna"]["sign"])
    if lagna:
        out.append({"trigger": f"lagna {lagna['sign']}", "source": lagna["source"],
                    "dictum": lagna["dictum"]})

    bhava = _load("graha_in_bhava")
    for g, gd in chart["grahas"].items():
        line = bhava.get(g, {}).get(gd["house"])
        if line:
            qual = []
            if gd["dignity"] in ("exalted", "moolatrikona", "own"):
                qual.append(f"dignified ({gd['dignity']})")
            elif gd["dignity"] in ("debilitated", "great_enemy"):
                qual.append(f"weak ({gd['dignity']})")
            if gd["retrograde"] and g not in ("rahu", "ketu"):
                qual.append("retrograde")
            if gd["combust"]:
                qual.append("combust")
            out.append({
                "trigger": f"{g} in house {gd['house']}" + (f" [{', '.join(qual)}]" if qual else ""),
                "source": line.split("(")[-1].rstrip(")") if "(" in line else "classical",
                "dictum": line,
            })

    yoga_corpus = _load("yogas")
    for y in chart.get("yogas", []):
        key = y["key"]
        entry = yoga_corpus.get(key)
        if entry is None:  # prefix keys (neecha_bhanga_venus → neecha_bhanga)
            for prefix, e in yoga_corpus.items():
                if key.startswith(prefix):
                    entry = e
                    break
        if entry:
            out.append({"trigger": f"yoga {y['name']} ({'; '.join(y['factors'])})",
                        "source": entry["source"], "dictum": entry["dictum"]})

    nak = _load("nakshatra").get(chart["grahas"]["moon"]["nakshatra"]["index"])
    if nak:
        out.append({"trigger": f"moon nakshatra {nak['name']}",
                    "source": "classical nakshatra lore", "dictum": nak["dictum"]})

    dasha_corpus = _load("dasha")
    cur = chart.get("current_dasha")
    if cur:
        for level in ("maha", "antar"):
            entry = dasha_corpus.get(cur[level])
            if entry:
                out.append({"trigger": f"current {level}dasha {cur[level]} "
                                       f"(ends {cur[f'{level}_end'][:10]})",
                            "source": entry["source"], "dictum": entry["dictum"]})
    return out


def archetypes_for_chart(chart: dict) -> list[dict]:
    """Puranic archetypes for the chart's pivotal grahas: lagna lord, Moon's
    nakshatra lord, and the current mahadasha lord."""
    arch = _load("purana_archetypes")
    pivotal: list[tuple[str, str]] = [("lagna lord", chart["lagna"]["lord"])]
    pivotal.append(("moon nakshatra lord", chart["grahas"]["moon"]["nakshatra"]["lord"]))
    if chart.get("current_dasha"):
        pivotal.append(("current mahadasha lord", chart["current_dasha"]["maha"]))
    seen, out = set(), []
    for role, g in pivotal:
        if g in seen:
            continue
        seen.add(g)
        a = arch.get(g)
        if a:
            out.append({"role": role, "graha": g, **a})
    return out

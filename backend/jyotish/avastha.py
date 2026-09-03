"""Graha avasthas (states), graha yuddha (planetary war), vargottama.

Avasthas per BPHS:
- Baladi (age, by degree in sign; direction REVERSES for even signs):
  bala (infant) / kumara / yuva / vriddha / mrita in 6° bands. A yuva graha
  gives full results; a mrita graha gives almost none — this weights dictums.
- Jagradadi (alertness, by dignity): jagrat (awake — own/exalted/moolatrikona),
  swapna (dreaming — friend/neutral), sushupti (asleep — enemy/debilitated).
- Deeptadi (mood, composite): deepta (exalted), swastha (own/moolatrikona),
  mudita (great-friend/friend), shanta (neutral), duhkhita (enemy),
  khala (great-enemy or debilitated), vikala (combust), bhita (in a lost
  planetary war). First matching state in that priority order is reported
  (vikala/bhita override dignity states — an eclipsed graha cannot shine).

Graha yuddha: two of Mars/Mercury/Jupiter/Venus/Saturn within 1° of each
other are at war. Winner convention (documented; declination not carried in
ChartV1): the graha with the LOWER longitude wins (Surya Siddhanta rule used
by several implementations). Sun/Moon/nodes never war.

Vargottama: same sign in D1 and D9 — a classical strength marker.
"""

from __future__ import annotations

from .dignity import dignity_of
from .varga import d9

_BALADI = ["bala", "kumara", "yuva", "vriddha", "mrita"]
_WAR_CAPABLE = ("mars", "mercury", "jupiter", "venus", "saturn")


def baladi_avastha(lon: float) -> str:
    sign = int((lon % 360.0) // 30)
    deg = (lon % 360.0) % 30.0
    band = min(4, int(deg // 6))
    if sign % 2 == 1:  # even sign (Taurus, Cancer…) — order reverses
        band = 4 - band
    return _BALADI[band]


def jagradadi_avastha(dignity: str) -> str:
    if dignity in ("exalted", "moolatrikona", "own"):
        return "jagrat"
    if dignity in ("great_friend", "friend", "neutral"):
        return "swapna"
    return "sushupti"


def deeptadi_avastha(dignity: str, combust: bool, lost_war: bool) -> str:
    if lost_war:
        return "bhita"
    if combust:
        return "vikala"
    return {
        "exalted": "deepta", "moolatrikona": "swastha", "own": "swastha",
        "great_friend": "mudita", "friend": "mudita", "neutral": "shanta",
        "enemy": "duhkhita", "great_enemy": "khala", "debilitated": "khala",
    }.get(dignity, "shanta")


def graha_yuddha(positions: dict[str, dict]) -> list[dict]:
    """Detect planetary wars. Returns [{grahas, winner, loser, separation}]."""
    wars = []
    caps = [g for g in _WAR_CAPABLE if g in positions]
    for i, g1 in enumerate(caps):
        for g2 in caps[i + 1:]:
            l1, l2 = positions[g1]["lon"], positions[g2]["lon"]
            sep = abs((l1 - l2) % 360.0)
            sep = min(sep, 360.0 - sep)
            if sep <= 1.0:
                winner, loser = (g1, g2) if (l1 % 360.0) <= (l2 % 360.0) else (g2, g1)
                wars.append({"grahas": [g1, g2], "winner": winner, "loser": loser,
                             "separation": round(sep, 4)})
    return wars


def is_vargottama(lon: float) -> bool:
    return int((lon % 360.0) // 30) == d9(lon)


def avasthas_for(graha: str, lon: float, combust: bool, lost_war: bool) -> dict:
    dig = dignity_of(graha, lon)
    return {
        "baladi": baladi_avastha(lon),
        "jagradadi": jagradadi_avastha(dig),
        "deeptadi": deeptadi_avastha(dig, combust, lost_war),
        "vargottama": is_vargottama(lon),
    }

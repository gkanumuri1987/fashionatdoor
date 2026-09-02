"""Graha dignity, friendship (natural + temporal → compound), combustion."""

from __future__ import annotations

from .constants import (COMBUSTION_DEG, EXALTATION, GRAHAS, MOOLATRIKONA,
                        NATURAL_FRIENDS, OWN_SIGNS, SIGN_LORD)


def _angular_distance(a: float, b: float) -> float:
    d = abs((a - b) % 360.0)
    return min(d, 360.0 - d)


def natural_relation(graha: str, other: str) -> str:
    t = NATURAL_FRIENDS[graha]
    if other in t["friends"]:
        return "friend"
    if other in t["enemies"]:
        return "enemy"
    return "neutral"


def temporal_relation(graha_sign: int, other_sign: int) -> str:
    """Planets in the 2nd, 3rd, 4th, 10th, 11th, 12th sign from a graha are its
    temporal friends; all others are temporal enemies."""
    diff = (other_sign - graha_sign) % 12  # 0 = same sign
    return "friend" if diff in (1, 2, 3, 9, 10, 11) else "enemy"


_COMPOUND = {
    ("friend", "friend"): "great_friend",
    ("friend", "enemy"): "neutral",
    ("neutral", "friend"): "friend",
    ("neutral", "enemy"): "enemy",
    ("enemy", "friend"): "neutral",
    ("enemy", "enemy"): "great_enemy",
}


def compound_relation(graha: str, other: str, graha_sign: int, other_sign: int) -> str:
    nat = natural_relation(graha, other)
    tem = temporal_relation(graha_sign, other_sign)
    return _COMPOUND[(nat, tem)]


def dignity_of(graha: str, lon: float) -> str:
    """exalted | moolatrikona | own | great_friend | friend | neutral | enemy |
    great_enemy | debilitated — the standard ladder.

    Note: the friend/enemy rungs here use NATURAL friendship with the sign's
    lord (temporal relation needs the full chart; chart.py upgrades these to
    compound where it has all positions)."""
    sign = int((lon % 360.0) // 30)
    deg = (lon % 360.0) % 30.0

    ex_sign, _ = EXALTATION.get(graha, (None, None))
    if ex_sign is not None:
        if sign == ex_sign:
            return "exalted"
        if sign == (ex_sign + 6) % 12:
            return "debilitated"

    mt = MOOLATRIKONA.get(graha)
    if mt and sign == mt[0] and mt[1] <= deg < mt[2]:
        return "moolatrikona"

    if sign in OWN_SIGNS.get(graha, []):
        return "own"

    lord = SIGN_LORD[sign]
    if lord == graha:
        return "own"
    return natural_relation(graha, lord)


def combustion_flags(positions: dict[str, dict]) -> dict[str, bool]:
    """Which grahas are combust (too close to the Sun). Sun/nodes never combust."""
    sun_lon = positions["sun"]["lon"]
    out = {}
    for g in GRAHAS:
        if g in ("sun", "rahu", "ketu"):
            out[g] = False
            continue
        limits = COMBUSTION_DEG.get(g)
        if not limits:
            out[g] = False
            continue
        limit = limits[1] if positions[g].get("retrograde") else limits[0]
        out[g] = _angular_distance(positions[g]["lon"], sun_lon) <= limit
    return out

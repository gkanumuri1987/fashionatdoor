"""Ashtakavarga per BPHS — bindu (benefic-dot) tables for the 7 classical grahas.

Rules: Brihat Parashara Hora Shastra (Ashtakavarga adhyayas). For each graha's
Bhinnashtakavarga (BAV), eight contributors — the 7 grahas plus the lagna —
each grant one bindu in a fixed set of houses counted FROM THE CONTRIBUTOR'S
OWN SIGN. The tables below are the canonical ones (identical to those used by
JHora / Maitreya). Rahu/Ketu neither contribute nor receive.

Per-BAV totals (invariants): Sun 48, Moon 49, Mars 39, Mercury 54, Jupiter 56,
Venus 52, Saturn 39 — Sarvashtakavarga (SAV) always sums to 337 bindus.

All outputs are indexed by SIGN (0 = Aries .. 11 = Pisces), not by house.
"""

from __future__ import annotations

SEVEN_GRAHAS = ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn")

# For each graha's BAV: contributor -> houses (1-12) counted from the
# contributor's sign in which a bindu is granted. "lagna" = the ascendant sign.
BINDU_TABLE: dict[str, dict[str, tuple[int, ...]]] = {
    "sun": {
        "sun": (1, 2, 4, 7, 8, 9, 10, 11),
        "moon": (3, 6, 10, 11),
        "mars": (1, 2, 4, 7, 8, 9, 10, 11),
        "mercury": (3, 5, 6, 9, 10, 11, 12),
        "jupiter": (5, 6, 9, 11),
        "venus": (6, 7, 12),
        "saturn": (1, 2, 4, 7, 8, 9, 10, 11),
        "lagna": (3, 4, 6, 10, 11, 12),
    },
    "moon": {
        "sun": (3, 6, 7, 8, 10, 11),
        "moon": (1, 3, 6, 7, 10, 11),
        "mars": (2, 3, 5, 6, 9, 10, 11),
        "mercury": (1, 3, 4, 5, 7, 8, 10, 11),
        "jupiter": (1, 4, 7, 8, 10, 11, 12),
        "venus": (3, 4, 5, 7, 9, 10, 11),
        "saturn": (3, 5, 6, 11),
        "lagna": (3, 6, 10, 11),
    },
    "mars": {
        "sun": (3, 5, 6, 10, 11),
        "moon": (3, 6, 11),
        "mars": (1, 2, 4, 7, 8, 10, 11),
        "mercury": (3, 5, 6, 11),
        "jupiter": (6, 10, 11, 12),
        "venus": (6, 8, 11, 12),
        "saturn": (1, 4, 7, 8, 9, 10, 11),
        "lagna": (1, 3, 6, 10, 11),
    },
    "mercury": {
        "sun": (5, 6, 9, 11, 12),
        "moon": (2, 4, 6, 8, 10, 11),
        "mars": (1, 2, 4, 7, 8, 9, 10, 11),
        "mercury": (1, 3, 5, 6, 9, 10, 11, 12),
        "jupiter": (6, 8, 11, 12),
        "venus": (1, 2, 3, 4, 5, 8, 9, 11),
        "saturn": (1, 2, 4, 7, 8, 9, 10, 11),
        "lagna": (1, 2, 4, 6, 8, 10, 11),
    },
    "jupiter": {
        "sun": (1, 2, 3, 4, 7, 8, 9, 10, 11),
        "moon": (2, 5, 7, 9, 11),
        "mars": (1, 2, 4, 7, 8, 10, 11),
        "mercury": (1, 2, 4, 5, 6, 9, 10, 11),
        "jupiter": (1, 2, 3, 4, 7, 8, 10, 11),
        "venus": (2, 5, 6, 9, 10, 11),
        "saturn": (3, 5, 6, 12),
        "lagna": (1, 2, 4, 5, 6, 7, 9, 10, 11),
    },
    "venus": {
        "sun": (8, 11, 12),
        "moon": (1, 2, 3, 4, 5, 8, 9, 11, 12),
        "mars": (3, 5, 6, 9, 11, 12),
        "mercury": (3, 5, 6, 9, 11),
        "jupiter": (5, 8, 9, 10, 11),
        "venus": (1, 2, 3, 4, 5, 8, 9, 10, 11),
        "saturn": (3, 4, 5, 8, 9, 10, 11),
        "lagna": (1, 2, 3, 4, 5, 8, 9, 11),
    },
    "saturn": {
        "sun": (1, 2, 4, 7, 8, 10, 11),
        "moon": (3, 6, 11),
        "mars": (3, 5, 6, 10, 11, 12),
        "mercury": (6, 8, 9, 10, 11, 12),
        "jupiter": (5, 6, 11, 12),
        "venus": (6, 11, 12),
        "saturn": (3, 5, 6, 11),
        "lagna": (1, 3, 4, 6, 10, 11),
    },
}

# Canonical per-BAV bindu totals (used as a test invariant).
BAV_TOTALS = {"sun": 48, "moon": 49, "mars": 39, "mercury": 54,
              "jupiter": 56, "venus": 52, "saturn": 39}
SAV_TOTAL = 337


def _sign(lon: float) -> int:
    return int((lon % 360.0) // 30)


def bhinnashtakavarga(positions: dict[str, float], lagna_sign: int) -> dict[str, list[int]]:
    """BAV for each of the 7 grahas.

    positions: {graha: sidereal longitude in degrees} — must contain the 7
    classical grahas; rahu/ketu (if present) are ignored.
    lagna_sign: ascendant sign index (0 = Aries .. 11).

    Returns {graha: [bindus per sign]} with 12 ints (each 0-8) indexed by SIGN.
    """
    contrib_sign = {g: _sign(positions[g]) for g in SEVEN_GRAHAS}
    contrib_sign["lagna"] = lagna_sign % 12

    out: dict[str, list[int]] = {}
    for graha in SEVEN_GRAHAS:
        bav = [0] * 12
        for contributor, houses in BINDU_TABLE[graha].items():
            base = contrib_sign[contributor]
            for house in houses:
                bav[(base + house - 1) % 12] += 1
        out[graha] = bav
    return out


def sarvashtakavarga(bav: dict[str, list[int]]) -> list[int]:
    """SAV: per-sign sum of the 7 BAVs (always totals 337)."""
    return [sum(bav[g][s] for g in SEVEN_GRAHAS) for s in range(12)]

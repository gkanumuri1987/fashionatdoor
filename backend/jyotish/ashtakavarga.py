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


# ---------------------------------------------------------------------------
# Shodhana (reductions) + Shodhya Pinda — BPHS, JHora/Maitreya conventions
# ---------------------------------------------------------------------------

# The four trine (trikona) groups of signs.
TRIKONA_GROUPS: tuple[tuple[int, int, int], ...] = (
    (0, 4, 8),   # Aries, Leo, Sagittarius
    (1, 5, 9),   # Taurus, Virgo, Capricorn
    (2, 6, 10),  # Gemini, Libra, Aquarius
    (3, 7, 11),  # Cancer, Scorpio, Pisces
)

# The five sign-pairs sharing a single lord (dual lordship / ekadhipatya).
# Sun (Leo) and Moon (Cancer) own one sign each, so they are exempt.
EKADHIPATYA_PAIRS: dict[str, tuple[int, int]] = {
    "mars": (0, 7),      # Aries - Scorpio
    "venus": (1, 6),     # Taurus - Libra
    "mercury": (2, 5),   # Gemini - Virgo
    "jupiter": (8, 11),  # Sagittarius - Pisces
    "saturn": (9, 10),   # Capricorn - Aquarius
}

# Shodhya-pinda multipliers (BPHS).
# Per-sign multipliers, Aries..Pisces:
RASI_MULT: tuple[int, ...] = (7, 10, 8, 4, 10, 6, 7, 8, 9, 5, 11, 12)
# Per-graha multipliers, Sun..Saturn:
GRAHA_MULT: dict[str, int] = {"sun": 5, "moon": 5, "mars": 8, "mercury": 5,
                              "jupiter": 10, "venus": 7, "saturn": 5}


def trikona_shodhana(bav: dict[str, list[int]]) -> dict[str, list[int]]:
    """Trikona (trine) reduction of each graha's BAV — standard Parashara rule.

    For each of the four trine groups, per BAV:
      (a) all three signs hold EQUAL bindus  -> all three become 0
          (covers the all-zero case trivially);
      (b) otherwise, if ANY of the three is 0 -> NO reduction in that group;
      (c) otherwise subtract the MINIMUM of the three from each of the three.

    This is the convention implemented by JHora / Maitreya. Input is not
    mutated; a new {graha: [12 ints]} dict is returned.
    """
    out = {graha: list(vals) for graha, vals in bav.items()}
    for vals in out.values():
        for group in TRIKONA_GROUPS:
            a, b, c = (vals[s] for s in group)
            if a == b == c:
                for s in group:
                    vals[s] = 0
            elif min(a, b, c) == 0:
                continue
            else:
                m = min(a, b, c)
                for s in group:
                    vals[s] -= m
    return out


def ekadhipatya_shodhana(bav_after_trikona: dict[str, list[int]],
                         graha_signs: dict[str, int]) -> dict[str, list[int]]:
    """Ekadhipatya (dual-lordship) reduction — applied AFTER trikona shodhana.

    graha_signs: D1 sign index of each graha (pass all 9 — every listed graha
    counts toward sign occupancy). Applied to the 5 dual-lord pairs only
    (EKADHIPATYA_PAIRS); Cancer/Leo are never reduced.

    Sub-rules per pair per BAV (the JHora/Maitreya-style convention):
      - if EITHER sign of the pair holds 0 bindus  -> no reduction
        (zero-valued signs never change, and never trigger a reduction);
      - BOTH signs occupied by planets            -> no reduction;
      - ONE occupied, one unoccupied:
          unoccupied's bindus <= occupied's -> unoccupied becomes 0,
          else                              -> unoccupied -= occupied's;
        (the occupied sign is never changed);
      - BOTH unoccupied:
          equal bindus -> both become 0,
          else         -> the larger is reduced to the smaller's value.

    Input is not mutated; a new dict is returned.
    """
    occupied = {int(s) % 12 for s in graha_signs.values()}
    out = {graha: list(vals) for graha, vals in bav_after_trikona.items()}
    for vals in out.values():
        for s1, s2 in EKADHIPATYA_PAIRS.values():
            a, b = vals[s1], vals[s2]
            if a == 0 or b == 0:
                continue
            occ1, occ2 = s1 in occupied, s2 in occupied
            if occ1 and occ2:
                continue
            if occ1 or occ2:  # exactly one occupied
                occ_val = a if occ1 else b
                un_sign = s2 if occ1 else s1
                un_val = vals[un_sign]
                vals[un_sign] = 0 if un_val <= occ_val else un_val - occ_val
            else:  # both unoccupied
                if a == b:
                    vals[s1] = vals[s2] = 0
                elif a > b:
                    vals[s1] = b
                else:
                    vals[s2] = a
    return out


def shodhya_pinda(reduced_bav: dict[str, list[int]],
                  graha_signs: dict[str, int]) -> dict[str, dict[str, int]]:
    """Shodhya pinda per graha from the fully reduced BAV.

    rasi_pinda  = sum over signs of (reduced bindus * RASI_MULT[sign]).
    graha_pinda = sum over the 7 classical grahas of (reduced bindus in the
                  sign OCCUPIED by that graha * GRAHA_MULT[graha]).
    shodhya_pinda = rasi_pinda + graha_pinda.

    Returns {graha: {"rasi_pinda", "graha_pinda", "shodhya_pinda"}}.
    """
    out: dict[str, dict[str, int]] = {}
    for graha, vals in reduced_bav.items():
        rasi = sum(vals[s] * RASI_MULT[s] for s in range(12))
        gp = sum(vals[int(graha_signs[g]) % 12] * GRAHA_MULT[g]
                 for g in SEVEN_GRAHAS)
        out[graha] = {"rasi_pinda": rasi, "graha_pinda": gp,
                      "shodhya_pinda": rasi + gp}
    return out


# ---------------------------------------------------------------------------
# Kakshya (sign-eighths) + contributor-level BAV
# ---------------------------------------------------------------------------

# Each sign divides into 8 kakshyas of 3°45' each; lords in fixed order.
KAKSHYA_LORDS: tuple[str, ...] = ("saturn", "jupiter", "mars", "sun",
                                  "venus", "mercury", "moon", "lagna")
KAKSHYA_SPAN = 30.0 / 8.0  # 3.75 degrees = 3°45'


def kakshya_of(lon: float) -> dict:
    """Kakshya of a longitude: {"index": 0-7, "lord": name}.

    Kakshya lords in order within every sign: Saturn, Jupiter, Mars, Sun,
    Venus, Mercury, Moon, Lagna (3°45' each).
    """
    deg = (lon % 360.0) % 30.0
    idx = min(7, int((deg + 1e-9) / KAKSHYA_SPAN))
    return {"index": idx, "lord": KAKSHYA_LORDS[idx]}


def bhinnashtakavarga_detailed(positions: dict[str, float],
                               lagna_sign: int) -> dict[str, list[set[str]]]:
    """Contributor-level BAV: {graha: [set of contributors per sign] x 12}.

    Same tables/geometry as bhinnashtakavarga; each sign's entry is the SET
    of contributors ("sun".."saturn", "lagna") that granted a bindu there,
    so len(set) == the bindu count of bhinnashtakavarga for that sign.
    """
    contrib_sign = {g: _sign(positions[g]) for g in SEVEN_GRAHAS}
    contrib_sign["lagna"] = lagna_sign % 12

    out: dict[str, list[set[str]]] = {}
    for graha in SEVEN_GRAHAS:
        cells: list[set[str]] = [set() for _ in range(12)]
        for contributor, houses in BINDU_TABLE[graha].items():
            base = contrib_sign[contributor]
            for house in houses:
                cells[(base + house - 1) % 12].add(contributor)
        out[graha] = cells
    return out


def kakshya_transit_favor(bav: dict[str, list[set[str]]], graha: str,
                          transit_lon: float) -> dict:
    """Kakshya-level transit judgement for `graha` at `transit_lon`.

    bav MUST be the contributor-level structure returned by
    bhinnashtakavarga_detailed (the proper kakshya method needs to know WHO
    contributed each bindu, not just the count). The transit is favorable
    when the lord of the occupied kakshya is among the contributors of a
    bindu in that sign in the graha's own BAV (the lagna kakshya counts via
    the "lagna" contributor).

    Returns {"sign", "kakshya_index", "kakshya_lord", "favorable", "bindus"}.
    """
    sign = _sign(transit_lon)
    kk = kakshya_of(transit_lon)
    contributors = bav[graha][sign]
    return {
        "sign": sign,
        "kakshya_index": kk["index"],
        "kakshya_lord": kk["lord"],
        "favorable": kk["lord"] in contributors,
        "bindus": len(contributors),
    }

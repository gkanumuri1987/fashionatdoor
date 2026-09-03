"""Classical transit chakras — Sarvatobhadra, Kota, Tripataki.

Pure table arithmetic over caller-supplied sidereal longitudes; no ephemeris
access here. All three chakras reduce, computationally, to fixed lookup
relationships, which is what this module encodes.

Conventions (texts differ — each decision is stated):

- 28-NAKSHATRA SCHEME: Sarvatobhadra and Kota use the 28-fold zodiac with
  Abhijit inserted between Uttara Ashadha and Shravana. Abhijit spans
  276°40'..280°53'20" sidereal — the last quarter of Uttara Ashadha plus the
  first 1/15 of Shravana (the standard span). Index 21 = Abhijit; the 27-scheme
  indices 21..26 (Shravana..Revati) shift to 22..27.
- SARVATOBHADRA VEDHA: rather than modelling the full 9x9 grid (whose border
  layout varies by text), we encode its computational core — the fixed vedha
  triples the grid geometry produces. For 28-index i the partners are
  (i+14)%28 (sammukha/front — the cell straight across the grid), (28-i)%28
  and (14-i)%28 (the two flank lines — folds of the grid about its axes).
  Each formula is an involution, so vedha is MUTUAL by construction; self-hits
  and duplicates are dropped, so a nakshatra has up to 3 partners. Documented
  as the computational-geometry derivation of the classical grid.
- JANMA INPUT is a 27-scheme Moon nakshatra index (as produced by
  nakshatra.nakshatra_of), mapped straight into the 28 scheme (i<=20 -> i,
  else i+1); Abhijit itself is never a janma nakshatra under 27-scheme input.
- KOTA CHAKRA: the 28 nakshatras counted from janma walk a fixed path through
  the four fort rings. We implement the computational-standard repeating
  quarter pattern [bahya, prakara, madhya, stambha, stambha, madhya, prakara]
  (offsets 0-6 = quarter 1, 7-13 = quarter 2, ...; 4 quarters x 7 = 28).
  Within each quarter the first four steps move outer->inner ("entering"),
  the last three move inner->outer ("exiting"). Ring totals: bahya 4,
  prakara 8, madhya 8, stambha 8. Siege alert = any malefic inside the inner
  fort (stambha/madhya) while NO benefic is inside — the classical
  besieged-fortress caution.
- TRIPATAKI: implemented in the widely used simplification — the flag drawing
  adds no computational content beyond its vedha lines, which are: planets in
  the 1st/5th/9th (trine flags) and the 7th sign from the reference Moon sign
  pierce the Moon. Reference sign = the year's transit Moon sign when given,
  else the natal Moon sign. The Moon itself never pierces itself.
- NATURE: malefics (sun, mars, saturn, rahu, ketu) cast "adverse" vedha;
  benefics (moon, mercury, jupiter, venus) cast "mixed" vedha.
"""

from __future__ import annotations

from .constants import NAKSHATRAS
from .nakshatra import SPAN

# ── 28-nakshatra scheme ──────────────────────────────────────────────────────
NAKSHATRAS_28 = NAKSHATRAS[:21] + ["Abhijit"] + NAKSHATRAS[21:]

ABHIJIT_START = 20 * SPAN + 3 * SPAN / 4.0   # 276°40'   (last quarter of U.Ashadha)
ABHIJIT_END = 21 * SPAN + SPAN / 15.0        # 280°53'20" (first 1/15 of Shravana)

MALEFICS = {"sun", "mars", "saturn", "rahu", "ketu"}
BENEFICS = {"moon", "mercury", "jupiter", "venus"}


def _nature(graha: str) -> str:
    return "adverse" if graha in MALEFICS else "mixed"


def nakshatra28_of(lon: float) -> int:
    """28-scheme nakshatra index (Abhijit = 21) for a sidereal longitude."""
    lon = lon % 360.0
    if ABHIJIT_START <= lon < ABHIJIT_END:
        return 21
    idx27 = min(26, int(lon // SPAN))
    return idx27 if idx27 <= 20 else idx27 + 1


def nak27_to_28(idx27: int) -> int:
    """Map a 27-scheme nakshatra index into the 28 scheme (Abhijit skipped)."""
    idx27 = idx27 % 27
    return idx27 if idx27 <= 20 else idx27 + 1


# ── Sarvatobhadra chakra ─────────────────────────────────────────────────────

def vedha_partners(idx28: int) -> list[int]:
    """Fixed vedha partners of a 28-scheme nakshatra (mutual; up to 3)."""
    idx28 = idx28 % 28
    partners = {(idx28 + 14) % 28, (28 - idx28) % 28, (14 - idx28) % 28}
    partners.discard(idx28)
    return sorted(partners)


def sarvatobhadra_vedha(natal_moon_nak_27: int, transit_positions: dict[str, float]) -> dict:
    """Vedhas cast by transiting grahas in the Sarvatobhadra chakra.

    transit_positions: graha -> sidereal longitude. Reports every graha's
    pierced nakshatras plus, specifically, hits on the JANMA nakshatra.
    """
    janma28 = nak27_to_28(natal_moon_nak_27)
    vedhas_on_janma = []
    all_vedhas = {}
    for graha, lon in transit_positions.items():
        idx28 = nakshatra28_of(lon)
        targets = vedha_partners(idx28)
        all_vedhas[graha] = {
            "from_nakshatra": NAKSHATRAS_28[idx28],
            "from_index_28": idx28,
            "targets": [NAKSHATRAS_28[t] for t in targets],
        }
        if janma28 in targets:
            vedhas_on_janma.append({
                "graha": graha,
                "from_nakshatra": NAKSHATRAS_28[idx28],
                "nature": _nature(graha),
            })
    return {
        "janma_nakshatra": NAKSHATRAS_28[janma28],
        "janma_index_28": janma28,
        "vedhas_on_janma": vedhas_on_janma,
        "all_vedhas": all_vedhas,
    }


# ── Kota chakra ──────────────────────────────────────────────────────────────
KOTA_RINGS = ["bahya", "prakara", "madhya", "stambha"]
_KOTA_QUARTER = ["bahya", "prakara", "madhya", "stambha", "stambha", "madhya", "prakara"]
_INNER_FORT = {"stambha", "madhya"}


def kota_ring_of(offset: int) -> tuple[str, str]:
    """(ring, moving) for a nakshatra `offset` steps from janma (0-27)."""
    k = (offset % 28) % 7
    return _KOTA_QUARTER[k], ("entering" if k < 4 else "exiting")


def kota_chakra(natal_moon_nak_27: int, transit_positions: dict[str, float]) -> dict:
    """Place transiting grahas in the Kota chakra and flag the siege condition."""
    janma28 = nak27_to_28(natal_moon_nak_27)
    rings = {}
    for graha, lon in transit_positions.items():
        idx28 = nakshatra28_of(lon)
        ring, moving = kota_ring_of((idx28 - janma28) % 28)
        rings[graha] = {
            "nakshatra": NAKSHATRAS_28[idx28],
            "offset": (idx28 - janma28) % 28,
            "ring": ring,
            "moving": moving,
        }
    malefics_inside = sorted(g for g, r in rings.items()
                             if g in MALEFICS and r["ring"] in _INNER_FORT)
    benefics_inside = sorted(g for g, r in rings.items()
                             if g in BENEFICS and r["ring"] in _INNER_FORT)
    alerts = []
    if malefics_inside and not benefics_inside:
        alerts.append({
            "type": "siege",
            "malefics_inside": malefics_inside,
            "benefics_inside": benefics_inside,
            "note": "Malefics occupy the inner fort (stambha/madhya) with no "
                    "benefic inside — classical siege; health/adversity caution.",
        })
    return {"janma_nakshatra": NAKSHATRAS_28[janma28], "rings": rings, "alerts": alerts}


# ── Tripataki chakra ─────────────────────────────────────────────────────────
# House offsets (0-based signs from the reference Moon sign) that pierce it:
# 1st, 5th, 9th (the trine flags) and the 7th.
_TRIPATAKI_VEDHA_OFFSETS = {0: 1, 4: 5, 8: 9, 6: 7}


def tripataki(natal_moon_sign: int, transit_positions: dict[str, float],
              current_year_moon_sign: int | None = None) -> dict:
    """Vedha on the (year's) Moon sign from transiting planets.

    Simplified per the module docstring: planets in the 1st/5th/9th/7th sign
    from the reference Moon sign cast vedha. The Moon never pierces itself.
    """
    moon_sign = (current_year_moon_sign if current_year_moon_sign is not None
                 else natal_moon_sign) % 12
    vedha_grahas = []
    for graha, lon in transit_positions.items():
        if graha == "moon":
            continue
        sign = int((lon % 360.0) // 30.0)
        offset = (sign - moon_sign) % 12
        if offset in _TRIPATAKI_VEDHA_OFFSETS:
            vedha_grahas.append({
                "graha": graha,
                "sign": sign,
                "house_from_moon": _TRIPATAKI_VEDHA_OFFSETS[offset],
                "nature": _nature(graha),
            })
    if not vedha_grahas:
        nature = "clear"
    elif any(v["nature"] == "adverse" for v in vedha_grahas):
        nature = "adverse"
    else:
        nature = "mixed"
    return {"moon_sign": moon_sign, "vedha_grahas": vedha_grahas, "nature": nature}

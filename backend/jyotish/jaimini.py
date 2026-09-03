"""Jaimini astrology — chara karakas, arudha padas, karakamsa, rasi drishti, chara dasha.

Rule sources: Jaimini Upadesa Sutras (rasi drishti, arudha, karakamsa) and the
BPHS chara-karaka chapter. Where classical variants diverge, the choice is
documented on the function:

* Chara karakas use the EIGHT-karaka scheme (BPHS/Jaimini standard): the seven
  classical grahas plus Rahu, ranked by degree within sign descending; Rahu
  (which moves backwards) is ranked by (30 - deg_in_sign). Ketu is excluded.
* Arudha lordship uses the PRIMARY sign lords from ``constants.SIGN_LORD``
  (Scorpio → Mars, Aquarius → Saturn), not the co-lords Ketu/Rahu.
* Chara dasha follows the common K.N. Rao-style simplification: direction by
  lagna-sign parity (odd sign → forward through the zodiac, even → backward),
  and each sign's span counted to its lord per that sign's OWN parity.

All functions are pure and deterministic; longitudes/signs are precomputed
inputs (no ephemeris access here).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .constants import GRAHAS, SIGNS, SIGN_LORD
from .varga import d9

# The eight chara-karaka candidates, in canonical order (used only as a
# deterministic tie-break when two grahas share the exact same degree).
_KARAKA_GRAHAS = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu"]

# 8-scheme karaka names in rank order (PiK sits between MK and PK).
KARAKA_ORDER = ["AK", "AmK", "BK", "MK", "PiK", "PK", "GK", "DK"]

# Standard graha → Ishta Devata indications (common Jaimini/karakamsa table).
DEITY_OF = {
    "sun": "Rama/Surya",
    "moon": "Krishna/Gauri",
    "mars": "Hanuman/Subrahmanya",
    "mercury": "Vishnu",
    "jupiter": "Vishnu/Dattatreya",
    "venus": "Lakshmi/Devi",
    "saturn": "Shiva/Ayyappa",
    "rahu": "Durga",
    "ketu": "Ganesha",
}

_J2000_JD = 2451545.0  # JD of 2000-01-01 12:00 UTC
_YEAR_DAYS = 365.25


def _deg_in_sign(lon: float) -> float:
    return (lon % 360.0) % 30.0


def _jd_to_iso(jd: float) -> str:
    """JD (UT) → ISO-8601 string via a J2000 datetime anchor (no swisseph)."""
    anchor = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    return (anchor + timedelta(days=jd - _J2000_JD)).isoformat()


# ── Chara karakas ────────────────────────────────────────────────────────────

def chara_karakas(positions: dict[str, dict]) -> dict:
    """Eight-scheme chara karakas (AK AmK BK MK PiK PK GK DK).

    ``positions`` is the engine's standard {graha: {"lon": deg, ...}} mapping.
    Grahas are ranked by degree within sign DESCENDING; Rahu's effective degree
    is (30 - deg_in_sign) because it travels backwards through the zodiac.
    Ketu takes no karakatwa in the 8-scheme. Exact-degree ties break by the
    canonical graha order (deterministic).
    """
    ranked_grahas = []
    for g in _KARAKA_GRAHAS:
        deg = _deg_in_sign(positions[g]["lon"])
        effective = (30.0 - deg) if g == "rahu" else deg
        ranked_grahas.append((g, deg, effective))
    ranked_grahas.sort(key=lambda t: (-t[2], _KARAKA_GRAHAS.index(t[0])))

    karakas: dict[str, dict] = {}
    ranked: list[dict] = []
    for karaka, (g, deg, effective) in zip(KARAKA_ORDER, ranked_grahas):
        entry = {"graha": g, "deg_in_sign": round(deg, 6)}
        karakas[karaka] = entry
        ranked.append({"karaka": karaka, "graha": g,
                       "deg_in_sign": round(deg, 6),
                       "effective_deg": round(effective, 6)})
    return {"scheme": "8", "karakas": karakas, "ranked": ranked}


# ── Arudha padas ─────────────────────────────────────────────────────────────

def arudha_pada(house: int, lagna_sign: int, graha_signs: dict[str, int]) -> int:
    """Arudha of a bhava (house counted from the lagna sign).

    Rule (Jaimini Sutras 1.1.29-30): count from the house's sign to its lord's
    sign; the arudha lies that many signs onward from the LORD. Exception: if
    that lands in the house's own sign or the 7th from it, take the 10th from
    the landing position instead. Lordship uses the primary lords from
    ``constants.SIGN_LORD`` (Scorpio → Mars, Aquarius → Saturn).
    """
    house_sign = (lagna_sign + house - 1) % 12
    lord = SIGN_LORD[house_sign]
    lord_sign = graha_signs[lord] % 12
    steps = (lord_sign - house_sign) % 12  # inclusive count minus 1
    arudha = (lord_sign + steps) % 12
    if arudha == house_sign or arudha == (house_sign + 6) % 12:
        arudha = (arudha + 9) % 12  # 10th from the landing position
    return arudha


def arudha_padas(lagna_sign: int, graha_signs: dict[str, int]) -> dict:
    """All twelve arudhas A1..A12 plus the aliases AL (=A1) and UL (=A12).

    Upapada (UL) is taken as the arudha of the 12TH house — the standard
    Jaimini convention (the other school uses the 7th; documented choice).
    """
    out: dict[str, int] = {}
    for house in range(1, 13):
        out[f"A{house}"] = arudha_pada(house, lagna_sign, graha_signs)
    out["AL"] = out["A1"]
    out["UL"] = out["A12"]
    return out


# ── Karakamsa & Ishta Devata ─────────────────────────────────────────────────

def karakamsa(ak_graha: str, positions: dict[str, dict]) -> dict:
    """Karakamsa: the Atmakaraka's navamsa (D9) sign."""
    sign = d9(positions[ak_graha]["lon"])
    return {"sign": sign, "sign_name": SIGNS[sign]["en"]}


def ishta_devata(karakamsa_sign: int, graha_signs_d9: dict[str, int]) -> dict:
    """Ishta Devata from the 12th sign from karakamsa in the navamsa.

    Classical rule: a graha OCCUPYING the 12th from karakamsa in D9 indicates
    the Ishta Devata; if that sign is empty, its LORD (primary lords) does.
    The classical tie-break among multiple occupants is the highest degree in
    sign; since this function receives D9 SIGNS only (no degrees), ties break
    deterministically by the canonical ``constants.GRAHAS`` order instead
    (documented variant).
    """
    examined = (karakamsa_sign + 11) % 12
    occupants = [g for g in GRAHAS if graha_signs_d9.get(g) == examined]
    if occupants:
        indicator, basis = occupants[0], "occupant"
    else:
        indicator, basis = SIGN_LORD[examined], "lord"
    return {"house_examined": examined, "indicator_graha": indicator,
            "basis": basis, "deity": DEITY_OF[indicator]}


# ── Rasi drishti ─────────────────────────────────────────────────────────────

def rasi_drishti(sign_a: int, sign_b: int) -> bool:
    """Jaimini sign aspect (mutual by nature; this checks a → b).

    Movable signs aspect all FIXED signs except the adjacent one (the next
    sign); fixed signs aspect all MOVABLE signs except the adjacent one (the
    previous sign); dual signs aspect the other three DUAL signs.
    """
    a, b = sign_a % 12, sign_b % 12
    if a == b:
        return False
    mobility_a, mobility_b = a % 3, b % 3  # 0=movable, 1=fixed, 2=dual
    if mobility_a == 0:  # movable → fixed, except the very next sign
        return mobility_b == 1 and b != (a + 1) % 12
    if mobility_a == 1:  # fixed → movable, except the very previous sign
        return mobility_b == 0 and b != (a - 1) % 12
    return mobility_b == 2  # dual → the other duals


# ── Chara dasha ──────────────────────────────────────────────────────────────

def _sign_dasha_years(sign: int, graha_signs: dict[str, int]) -> int:
    """Span of one sign's chara dasha in years.

    Count from the sign to its lord's sign — forward if the sign is odd
    (Aries, Gemini, ... i.e. index even), backward if even — minus one.
    Lord in its own sign (count 1 → 0 years) gives the full 12 years.
    """
    lord_sign = graha_signs[SIGN_LORD[sign]] % 12
    if sign % 2 == 0:  # odd sign → count forward
        count = (lord_sign - sign) % 12 + 1
    else:              # even sign → count backward
        count = (sign - lord_sign) % 12 + 1
    years = count - 1
    return 12 if years == 0 else years


def chara_dasha(lagna_sign: int, graha_signs: dict[str, int], birth_jd: float) -> list[dict]:
    """K.N. Rao-style chara dasha — one full cycle of 12 sign periods.

    Documented simplification of the variant rules: the sequence starts from
    the LAGNA sign, and the direction through the zodiac follows the lagna
    sign's parity — odd sign (Aries, Gemini, Leo, ... index even) → forward,
    even sign → backward. Each sign's span comes from ``_sign_dasha_years``
    (count to its lord per that sign's OWN parity, minus 1; 0 → 12 years).
    Years are 365.25 days; timestamps are ISO strings derived from
    ``birth_jd`` via a J2000 datetime anchor (no ephemeris dependency).
    """
    step = 1 if lagna_sign % 2 == 0 else -1
    periods: list[dict] = []
    cursor = birth_jd
    for i in range(12):
        sign = (lagna_sign + step * i) % 12
        years = _sign_dasha_years(sign, graha_signs)
        end = cursor + years * _YEAR_DAYS
        periods.append({"sign": sign, "sign_name": SIGNS[sign]["en"],
                        "years": years, "start": _jd_to_iso(cursor),
                        "end": _jd_to_iso(end)})
        cursor = end
    return periods

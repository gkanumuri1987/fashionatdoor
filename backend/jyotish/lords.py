"""Functional nature of grahas per lagna — BPHS rules, derived not hardcoded.

For each lagna, every graha is classified as functional benefic / malefic /
neutral / yogakaraka, with maraka and badhaka lords identified. These MUST be
in the deterministic JSON: if the engine doesn't state them, the AI writer
would "derive" them — which is computing, and forbidden.

Rules applied (BPHS Yogakaraka adhyaya, standard interpretation):
- Lagna lord is always a functional benefic.
- Trikona lords (5, 9) are benefics.
- Lords of 3, 6, 11 (trishadaya) are functional malefics.
- Kendradhipati dosha: a NATURAL benefic owning only kendras (4, 7, 10) loses
  beneficence (→ neutral); a natural malefic owning only kendras sheds malice
  (→ neutral).
- Yogakaraka: one graha owning BOTH a kendra and a trikona (Saturn for
  Taurus/Libra, Mars for Cancer/Leo, Venus for Capricorn/Aquarius).
- 8th lord is a functional malefic unless it also owns the lagna or a trikona.
- Maraka lords: lords of 2 and 7.
- Badhaka: 11th lord for movable lagnas, 9th for fixed, 7th for dual.
- Verdict precedence: yogakaraka > (benefic reasons vs malefic reasons count)
  with mixed ownership resolved by the STRONGER house per BPHS mode ordering
  (trikona > kendra > others); ties → "mixed".
"""

from __future__ import annotations

from .constants import SIGN_LORD, SIGNS

_NATURAL_BENEFICS = {"jupiter", "venus", "mercury", "moon"}  # static convention
_KENDRA = {1, 4, 7, 10}
_TRIKONA = {5, 9}          # lagna (1) handled via the lagna-lord rule
_TRISHADAYA = {3, 6, 11}

_BADHAKA_HOUSE = {"movable": 11, "fixed": 9, "dual": 7}


def functional_nature(lagna_sign: int) -> dict:
    """Classify all 7 classical grahas for the given lagna sign (0=Aries)."""
    houses_of: dict[str, list[int]] = {}
    for h in range(1, 13):
        lord = SIGN_LORD[(lagna_sign + h - 1) % 12]
        houses_of.setdefault(lord, []).append(h)

    mobility = SIGNS[lagna_sign]["mobility"]
    badhaka_house = _BADHAKA_HOUSE[mobility]
    badhaka_lord = SIGN_LORD[(lagna_sign + badhaka_house - 1) % 12]
    marakas = sorted({SIGN_LORD[(lagna_sign + 1) % 12], SIGN_LORD[(lagna_sign + 6) % 12]})

    out: dict[str, dict] = {}
    for graha, owned in houses_of.items():
        owned_set = set(owned)
        reasons_benefic: list[str] = []
        reasons_malefic: list[str] = []

        owns_lagna = 1 in owned_set
        owns_trikona = bool(owned_set & _TRIKONA)
        owns_kendra = bool(owned_set & (_KENDRA - {1}))
        owns_trishadaya = bool(owned_set & _TRISHADAYA)
        owns_8 = 8 in owned_set

        if owns_lagna:
            reasons_benefic.append("lagna lord")
        if owns_trikona:
            reasons_benefic.append(f"trikona lord ({sorted(owned_set & _TRIKONA)})")
        if owns_trishadaya:
            reasons_malefic.append(f"trishadaya lord ({sorted(owned_set & _TRISHADAYA)})")
        if owns_8 and not owns_lagna and not owns_trikona:
            reasons_malefic.append("8th lord")

        yogakaraka = (owns_kendra or owns_lagna) and owns_trikona
        kendradhipati = (owns_kendra and not owns_lagna and not owns_trikona
                         and not owns_trishadaya and not owns_8)

        if yogakaraka:
            verdict = "yogakaraka"
        elif kendradhipati:
            verdict = "neutral"
            side = "benefic" if graha in _NATURAL_BENEFICS else "malefic"
            reasons_benefic.append(f"kendradhipati dosha neutralises natural {side}")
        elif reasons_benefic and reasons_malefic:
            verdict = "mixed"
        elif reasons_benefic:
            verdict = "benefic"
        elif reasons_malefic:
            verdict = "malefic"
        else:
            verdict = "neutral"

        out[graha] = {
            "houses_owned": owned,
            "verdict": verdict,
            "benefic_reasons": reasons_benefic,
            "malefic_reasons": reasons_malefic,
            "is_maraka": graha in marakas,
            "is_badhaka": graha == badhaka_lord,
        }

    return {
        "per_graha": out,
        "yogakaraka": [g for g, d in out.items() if d["verdict"] == "yogakaraka"],
        "maraka_lords": marakas,
        "badhaka": {"house": badhaka_house, "lord": badhaka_lord,
                    "basis": f"{mobility} lagna"},
    }

"""Ayurdaya (Pindayu / Amsayu / Nisargayu) per BPHS — STRENGTH-MODEL ONLY.

POLICY — READ FIRST: these figures are computed solely for internal
strength-model completeness (they are classical planetary-contribution sums
that also feed strength heuristics). NEVER surface lifespan estimates to
users, and the AI layer must NEVER receive this block. Every output carries a
``"policy"`` key restating this.

Pure deterministic arithmetic (no AI, no swisseph). Documented
simplifications:

* Pindayu contribution = base_years × (angular distance of the graha from its
  DEEP DEBILITATION point, 0-180°) / 180 — full base at deep exaltation,
  zero at deep debilitation, linear between.
* Only two classical haranas (reductions) are applied:
  (1) astangata harana — a combust graha (except Venus and Saturn) loses
      half; (2) shatru-kshetra harana — a graha in an enemy sign (natural
      relation with the sign lord) loses one third.
  Further haranas (chakrapata etc.) are omitted.
* Pindayu lagna contribution is simplified to
  (lagna degrees within its sign) / 30 × 12 years.
* Amsayu contribution per graha = (navamsa count from the Mesha navamsa,
  i.e. floor(lon / 3°20'), taken mod 12) years, with the same two haranas;
  lagna uses the same formula.
* Nisargayu is the fixed natural-span table (a base scheme, no haranas).
"""

from __future__ import annotations

from .constants import EXALTATION
from .dignity import combustion_flags, dignity_of

POLICY = "internal-only; never expose lifespan to users"

# Base years at deep exaltation (BPHS pindayu table).
PINDAYU_BASE: dict[str, int] = {
    "sun": 19, "moon": 25, "mars": 15, "mercury": 12,
    "jupiter": 15, "venus": 21, "saturn": 20,
}

# Natural spans (nisargayu) in the order of natural ages.
NISARGAYU_YEARS: dict[str, int] = {
    "moon": 1, "mars": 2, "mercury": 9, "venus": 20,
    "jupiter": 18, "sun": 20, "saturn": 50,
}

# Combustion harana never applies to these (besides the Sun itself).
_COMBUST_EXEMPT = {"venus", "saturn"}

_NAVAMSA_SPAN = 30.0 / 9.0  # 3°20'


def _angular_distance(a: float, b: float) -> float:
    d = abs((a - b) % 360.0)
    return min(d, 360.0 - d)


def _deep_debilitation_lon(graha: str) -> float:
    ex_sign, ex_deg = EXALTATION[graha]
    return (ex_sign * 30.0 + ex_deg + 180.0) % 360.0


def _haranas(graha: str, lon: float, combust: bool) -> tuple[float, list[str]]:
    """Multiplicative reduction factor + labels for the two applied haranas."""
    factor, applied = 1.0, []
    if combust and graha not in _COMBUST_EXEMPT:
        factor *= 0.5
        applied.append("astangata")
    if dignity_of(graha, lon) == "enemy":
        factor *= 2.0 / 3.0
        applied.append("shatru_kshetra")
    return factor, applied


def pindayu(positions: dict[str, dict], lagna_lon: float) -> dict:
    """Pindayu: per-graha years proportional to arc from deep debilitation.

    ``positions`` maps graha → {"lon", optional "retrograde"} and must contain
    the seven classical grahas plus the Sun (for combustion).
    """
    combust = combustion_flags(positions)
    per: dict[str, dict] = {}
    total = 0.0
    for g, base in PINDAYU_BASE.items():
        lon = positions[g]["lon"] % 360.0
        d = _angular_distance(lon, _deep_debilitation_lon(g))
        raw = base * d / 180.0
        factor, applied = _haranas(g, lon, combust.get(g, False))
        yrs = raw * factor
        per[g] = {"base": base, "raw_years": round(raw, 6),
                  "haranas": applied, "years": round(yrs, 6)}
        total += yrs

    lagna_years = ((lagna_lon % 30.0) / 30.0) * 12.0
    return {
        "per_graha": per,
        "lagna_years": round(lagna_years, 6),
        "total_years": round(total + lagna_years, 6),
    }


def amsayu(positions: dict[str, dict], lagna_lon: float) -> dict:
    """Amsayu: years from navamsa counts (count from Mesha navamsa, mod 12)."""
    combust = combustion_flags(positions)
    per: dict[str, dict] = {}
    total = 0.0
    for g in PINDAYU_BASE:
        lon = positions[g]["lon"] % 360.0
        count = int(lon // _NAVAMSA_SPAN)
        raw = float(count % 12)
        factor, applied = _haranas(g, lon, combust.get(g, False))
        yrs = raw * factor
        per[g] = {"navamsa_count": count, "raw_years": raw,
                  "haranas": applied, "years": round(yrs, 6)}
        total += yrs

    lagna_years = float(int((lagna_lon % 360.0) // _NAVAMSA_SPAN) % 12)
    return {
        "per_graha": per,
        "lagna_years": lagna_years,
        "total_years": round(total + lagna_years, 6),
    }


def nisargayu() -> dict:
    """Fixed natural spans. A base scheme only — no haranas, no chart input."""
    return {
        "years": dict(NISARGAYU_YEARS),
        "total_years": sum(NISARGAYU_YEARS.values()),
        "note": "fixed natural-span base scheme (order of natural ages); "
                "no chart-dependent modification applied",
    }


def ayurdaya(positions: dict[str, dict], lagna_lon: float) -> dict:
    """All three BPHS ayurdaya schemes. INTERNAL ONLY — see module policy."""
    return {
        "pindayu": pindayu(positions, lagna_lon),
        "amsayu": amsayu(positions, lagna_lon),
        "nisargayu": nisargayu(),
        "method_note": (
            "BPHS pindayu/amsayu/nisargayu with documented simplifications: "
            "linear arc-from-debilitation pindayu, two haranas only "
            "(astangata halves except Venus/Saturn; shatru-kshetra removes a "
            "third), simplified lagna terms; computed for strength-model "
            "completeness only"
        ),
        "policy": POLICY,
    }

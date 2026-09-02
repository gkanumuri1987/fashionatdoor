"""Classical yoga detection over a computed chart.

Each rule is a pure function over graha signs/houses; only PRESENT yogas are
returned, each with the factors that formed it (traceability for the AI layer —
every dictum it cites must point at one of these).

v1 set: pancha mahapurusha, Gajakesari, Budhaditya, Chandra-Mangala, Kemadruma,
basic Raja (kendra-lord + trikona-lord association), Vipareeta Raja, Neecha
Bhanga (simplified), Dhana (2nd/11th lord exchange or conjunction).
"""

from __future__ import annotations

from .constants import SIGN_LORD
from .dignity import dignity_of

_KENDRA = {1, 4, 7, 10}
_TRIKONA = {1, 5, 9}

_MAHAPURUSHA = {
    "mars": "Ruchaka", "mercury": "Bhadra", "jupiter": "Hamsa",
    "venus": "Malavya", "saturn": "Sasa",
}


def _house_of(sign: int, lagna_sign: int) -> int:
    return (sign - lagna_sign) % 12 + 1


def _house_from(sign: int, ref_sign: int) -> int:
    return (sign - ref_sign) % 12 + 1


def _conjunct(g1: dict, g2: dict) -> bool:
    return g1["sign"] == g2["sign"]


def detect_yogas(grahas: dict[str, dict], lagna_sign: int) -> list[dict]:
    """grahas: {name: {"lon", "sign", "house"}} (house counted from lagna)."""
    out: list[dict] = []
    moon_sign = grahas["moon"]["sign"]

    # ── Pancha Mahapurusha: own/exalted graha in a kendra from lagna ─────────
    for g, yname in _MAHAPURUSHA.items():
        d = dignity_of(g, grahas[g]["lon"])
        if d in ("exalted", "moolatrikona", "own") and grahas[g]["house"] in _KENDRA:
            out.append({"key": f"mahapurusha_{yname.lower()}", "name": f"{yname} Yoga",
                        "factors": [f"{g} {d} in house {grahas[g]['house']}"]})

    # ── Gajakesari: Jupiter in kendra from the Moon ──────────────────────────
    jup_from_moon = _house_from(grahas["jupiter"]["sign"], moon_sign)
    if jup_from_moon in _KENDRA:
        out.append({"key": "gajakesari", "name": "Gajakesari Yoga",
                    "factors": [f"jupiter in {jup_from_moon} from moon"]})

    # ── Budhaditya: Sun + Mercury conjunct ───────────────────────────────────
    if _conjunct(grahas["sun"], grahas["mercury"]):
        out.append({"key": "budhaditya", "name": "Budhaditya Yoga",
                    "factors": ["sun and mercury conjunct"]})

    # ── Chandra-Mangala: Moon + Mars conjunct or mutually 7th ────────────────
    if _conjunct(grahas["moon"], grahas["mars"]) or \
            _house_from(grahas["mars"]["sign"], moon_sign) == 7:
        out.append({"key": "chandra_mangala", "name": "Chandra-Mangala Yoga",
                    "factors": ["moon-mars association"]})

    # ── Kemadruma: nothing in 2nd/12th from Moon (excl. Sun and nodes),
    #    and Moon not conjunct any graha ───────────────────────────────────────
    others = [g for g in grahas if g not in ("moon", "sun", "rahu", "ketu")]
    flanked = any(_house_from(grahas[g]["sign"], moon_sign) in (2, 12) for g in others)
    with_moon = any(_conjunct(grahas[g], grahas["moon"]) for g in others)
    if not flanked and not with_moon:
        out.append({"key": "kemadruma", "name": "Kemadruma Yoga",
                    "factors": ["no graha in 2nd/12th from moon or with moon"]})

    # ── House lords ──────────────────────────────────────────────────────────
    lord_of = {h: SIGN_LORD[(lagna_sign + h - 1) % 12] for h in range(1, 13)}

    # Raja: a kendra lord and a trikona lord conjunct (excluding same graha)
    kendra_lords = {lord_of[h] for h in _KENDRA}
    trikona_lords = {lord_of[h] for h in _TRIKONA}
    for kl in kendra_lords:
        for tl in trikona_lords:
            if kl != tl and _conjunct(grahas[kl], grahas[tl]):
                out.append({"key": "raja_kendra_trikona", "name": "Raja Yoga",
                            "factors": [f"kendra lord {kl} conjunct trikona lord {tl}"]})
                break
        else:
            continue
        break

    # Vipareeta Raja: lord of 6/8/12 placed in 6/8/12
    dusthana = (6, 8, 12)
    vip = [f"lord of {h} ({lord_of[h]}) in house {grahas[lord_of[h]]['house']}"
           for h in dusthana if grahas[lord_of[h]]["house"] in dusthana]
    if vip:
        out.append({"key": "vipareeta_raja", "name": "Vipareeta Raja Yoga", "factors": vip})

    # Dhana: 2nd and 11th lords conjunct or in mutual exchange
    l2, l11 = lord_of[2], lord_of[11]
    if l2 != l11:
        exchange = (SIGN_LORD[grahas[l2]["sign"]] == l11 and SIGN_LORD[grahas[l11]["sign"]] == l2)
        if _conjunct(grahas[l2], grahas[l11]) or exchange:
            out.append({"key": "dhana_2_11", "name": "Dhana Yoga",
                        "factors": [f"2nd lord {l2} and 11th lord {l11} associated"]})

    # Neecha Bhanga (simplified): debilitated graha whose dispositor is in a
    # kendra from lagna or from the Moon
    for g in grahas:
        if dignity_of(g, grahas[g]["lon"]) == "debilitated":
            disp = SIGN_LORD[grahas[g]["sign"]]
            if disp in grahas:
                in_kendra_lagna = grahas[disp]["house"] in _KENDRA
                in_kendra_moon = _house_from(grahas[disp]["sign"], moon_sign) in _KENDRA
                if in_kendra_lagna or in_kendra_moon:
                    out.append({"key": f"neecha_bhanga_{g}", "name": "Neecha Bhanga Raja Yoga",
                                "factors": [f"{g} debilitated, dispositor {disp} in kendra"]})
    return out

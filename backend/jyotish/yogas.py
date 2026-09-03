"""Classical yoga detection over a computed chart.

Each rule is a pure function over graha signs/houses; only PRESENT yogas are
returned, each with the factors that formed it (traceability for the AI layer —
every dictum it cites must point at one of these).

Coverage: pancha mahapurusha (kendra from lagna OR Moon), Gajakesari,
Budhaditya, Chandra-Mangala, Kemadruma, Raja (kendra x trikona lords),
Vipareeta Raja — generic plus named Harsha/Sarala/Vimala, Neecha Bhanga
(simplified), Dhana, Chandra yogas (Sunapha/Anapha/Durudhara), Surya yogas
(Vesi/Vasi/Ubhayachari), Adhi, Amala, Kala Sarpa (12 named variants),
Guru-Chandala, Grahan, Saraswati, Lakshmi, Parivartana (Maha/Khala/Dainya).

Every yoga lists its participant ``grahas`` so the chart layer can attach a
Shadbala-based strength to it — a yoga on a strong graha is not the same
statement as the same yoga on a weak one.
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
        if d not in ("exalted", "moolatrikona", "own"):
            continue
        in_kendra_lagna = grahas[g]["house"] in _KENDRA
        in_kendra_moon = _house_from(grahas[g]["sign"], moon_sign) in _KENDRA
        if in_kendra_lagna or in_kendra_moon:
            ref = "lagna" if in_kendra_lagna else "moon"
            out.append({"key": f"mahapurusha_{yname.lower()}", "name": f"{yname} Yoga",
                        "grahas": [g],
                        "factors": [f"{g} {d} in kendra from {ref} (house {grahas[g]['house']})"]})

    # ── Gajakesari: Jupiter in kendra from the Moon ──────────────────────────
    jup_from_moon = _house_from(grahas["jupiter"]["sign"], moon_sign)
    if jup_from_moon in _KENDRA:
        out.append({"key": "gajakesari", "name": "Gajakesari Yoga",
                    "grahas": ["jupiter", "moon"],
                    "factors": [f"jupiter in {jup_from_moon} from moon"]})

    # ── Budhaditya: Sun + Mercury conjunct ───────────────────────────────────
    if _conjunct(grahas["sun"], grahas["mercury"]):
        out.append({"key": "budhaditya", "name": "Budhaditya Yoga",
                    "grahas": ["sun", "mercury"],
                    "factors": ["sun and mercury conjunct"]})

    # ── Chandra-Mangala: Moon + Mars conjunct or mutually 7th ────────────────
    if _conjunct(grahas["moon"], grahas["mars"]) or \
            _house_from(grahas["mars"]["sign"], moon_sign) == 7:
        out.append({"key": "chandra_mangala", "name": "Chandra-Mangala Yoga",
                    "grahas": ["moon", "mars"],
                    "factors": ["moon-mars association"]})

    # ── Kemadruma: nothing in 2nd/12th from Moon (excl. Sun and nodes),
    #    and Moon not conjunct any graha ───────────────────────────────────────
    others = [g for g in grahas if g not in ("moon", "sun", "rahu", "ketu")]
    flanked = any(_house_from(grahas[g]["sign"], moon_sign) in (2, 12) for g in others)
    with_moon = any(_conjunct(grahas[g], grahas["moon"]) for g in others)
    if not flanked and not with_moon:
        out.append({"key": "kemadruma", "name": "Kemadruma Yoga",
                    "grahas": ["moon"],
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
                            "grahas": [kl, tl],
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
        out.append({"key": "vipareeta_raja", "name": "Vipareeta Raja Yoga",
                    "grahas": [lord_of[h] for h in dusthana if grahas[lord_of[h]]["house"] in dusthana],
                    "factors": vip})
    # Named Viparita variants (BPHS): each dusthana lord itself in a dusthana.
    for h, vname in ((6, "Harsha"), (8, "Sarala"), (12, "Vimala")):
        lord = lord_of[h]
        if grahas[lord]["house"] in dusthana:
            out.append({"key": f"viparita_{vname.lower()}", "name": f"{vname} Yoga",
                        "grahas": [lord],
                        "factors": [f"{h}th lord {lord} in house {grahas[lord]['house']}"]})

    # Dhana: 2nd and 11th lords conjunct or in mutual exchange
    l2, l11 = lord_of[2], lord_of[11]
    if l2 != l11:
        exchange = (SIGN_LORD[grahas[l2]["sign"]] == l11 and SIGN_LORD[grahas[l11]["sign"]] == l2)
        if _conjunct(grahas[l2], grahas[l11]) or exchange:
            out.append({"key": "dhana_2_11", "name": "Dhana Yoga",
                        "grahas": [l2, l11],
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
                                "grahas": [g, disp],
                                "factors": [f"{g} debilitated, dispositor {disp} in kendra"]})

    out.extend(_extended_yogas(grahas, lagna_sign, lord_of, moon_sign))
    return out


_KALA_SARPA_NAMES = {
    1: "Ananta", 2: "Kulika", 3: "Vasuki", 4: "Shankhapala", 5: "Padma",
    6: "Mahapadma", 7: "Takshaka", 8: "Karkotaka", 9: "Shankhachuda",
    10: "Ghataka", 11: "Vishadhara", 12: "Sheshanaga",
}

_BENEFICS = ("jupiter", "venus", "mercury")


def _extended_yogas(grahas: dict[str, dict], lagna_sign: int,
                    lord_of: dict[int, str], moon_sign: int) -> list[dict]:
    out: list[dict] = []
    seven = [g for g in grahas if g not in ("rahu", "ketu")]

    # ── Chandra yogas: Sunapha (2nd from Moon), Anapha (12th), Durudhara ─────
    non_sun = [g for g in seven if g not in ("moon", "sun")]
    in_2 = [g for g in non_sun if _house_from(grahas[g]["sign"], moon_sign) == 2]
    in_12 = [g for g in non_sun if _house_from(grahas[g]["sign"], moon_sign) == 12]
    if in_2 and in_12:
        out.append({"key": "durudhara", "name": "Durudhara Yoga", "grahas": ["moon"] + in_2 + in_12,
                    "factors": [f"{in_2} in 2nd and {in_12} in 12th from moon"]})
    elif in_2:
        out.append({"key": "sunapha", "name": "Sunapha Yoga", "grahas": ["moon"] + in_2,
                    "factors": [f"{in_2} in 2nd from moon"]})
    elif in_12:
        out.append({"key": "anapha", "name": "Anapha Yoga", "grahas": ["moon"] + in_12,
                    "factors": [f"{in_12} in 12th from moon"]})

    # ── Surya yogas: Vesi / Vasi / Ubhayachari (excl. Moon and nodes) ────────
    sun_sign = grahas["sun"]["sign"]
    non_moon = [g for g in seven if g not in ("sun", "moon")]
    s2 = [g for g in non_moon if _house_from(grahas[g]["sign"], sun_sign) == 2]
    s12 = [g for g in non_moon if _house_from(grahas[g]["sign"], sun_sign) == 12]
    if s2 and s12:
        out.append({"key": "ubhayachari", "name": "Ubhayachari Yoga", "grahas": ["sun"] + s2 + s12,
                    "factors": [f"{s2} in 2nd and {s12} in 12th from sun"]})
    elif s2:
        out.append({"key": "vesi", "name": "Vesi Yoga", "grahas": ["sun"] + s2,
                    "factors": [f"{s2} in 2nd from sun"]})
    elif s12:
        out.append({"key": "vasi", "name": "Vasi Yoga", "grahas": ["sun"] + s12,
                    "factors": [f"{s12} in 12th from sun"]})

    # ── Adhi: benefics in 6/7/8 from the Moon ────────────────────────────────
    adhi = [g for g in _BENEFICS if _house_from(grahas[g]["sign"], moon_sign) in (6, 7, 8)]
    if len(adhi) >= 2:
        out.append({"key": "adhi", "name": "Adhi Yoga", "grahas": ["moon"] + adhi,
                    "factors": [f"benefics {adhi} in 6/7/8 from moon"]})

    # ── Amala: a benefic in the 10th from lagna or Moon ──────────────────────
    amala = [g for g in _BENEFICS
             if grahas[g]["house"] == 10 or _house_from(grahas[g]["sign"], moon_sign) == 10]
    if amala:
        out.append({"key": "amala", "name": "Amala Yoga", "grahas": amala,
                    "factors": [f"benefic {amala} in 10th from lagna/moon"]})

    # ── Kala Sarpa: all seven grahas within the Rahu→Ketu arc (or Ketu→Rahu) ─
    rahu_lon, ketu_lon = grahas["rahu"]["lon"], grahas["ketu"]["lon"]
    def _within(start: float, lon: float) -> bool:
        return (lon - start) % 360.0 < 180.0
    all_rahu_side = all(_within(rahu_lon, grahas[g]["lon"]) for g in seven)
    all_ketu_side = all(_within(ketu_lon, grahas[g]["lon"]) for g in seven)
    if all_rahu_side or all_ketu_side:
        rahu_house = grahas["rahu"]["house"]
        vname = _KALA_SARPA_NAMES.get(rahu_house, "Kala Sarpa")
        out.append({"key": "kala_sarpa", "name": f"Kala Sarpa Yoga ({vname})",
                    "grahas": ["rahu", "ketu"],
                    "factors": [f"all grahas on one side of the nodal axis; rahu in house {rahu_house}"]})

    # ── Guru-Chandala: Jupiter with Rahu or Ketu ─────────────────────────────
    for node in ("rahu", "ketu"):
        if grahas["jupiter"]["sign"] == grahas[node]["sign"]:
            out.append({"key": f"guru_chandala_{node}", "name": "Guru-Chandala Yoga",
                        "grahas": ["jupiter", node],
                        "factors": [f"jupiter conjunct {node}"]})

    # ── Grahan (eclipse-born flavour): Sun or Moon with a node ───────────────
    for lum in ("sun", "moon"):
        for node in ("rahu", "ketu"):
            if grahas[lum]["sign"] == grahas[node]["sign"]:
                out.append({"key": f"grahan_{lum}_{node}", "name": "Grahan Yoga",
                            "grahas": [lum, node],
                            "factors": [f"{lum} conjunct {node}"]})

    # ── Saraswati: Jup+Ven+Merc each in kendra/trikona/2nd, Jupiter dignified ─
    good_houses = {1, 2, 4, 5, 7, 9, 10}
    if all(grahas[g]["house"] in good_houses for g in _BENEFICS):
        jup_d = dignity_of("jupiter", grahas["jupiter"]["lon"])
        if jup_d in ("exalted", "moolatrikona", "own", "great_friend", "friend"):
            out.append({"key": "saraswati", "name": "Saraswati Yoga", "grahas": list(_BENEFICS),
                        "factors": ["jupiter, venus, mercury all in kendra/trikona/2nd; jupiter dignified"]})

    # ── Lakshmi: 9th lord in own/exalted sign in a kendra or trikona ─────────
    l9 = lord_of[9]
    l9_d = dignity_of(l9, grahas[l9]["lon"])
    if l9_d in ("exalted", "moolatrikona", "own") and grahas[l9]["house"] in {1, 4, 5, 7, 9, 10}:
        out.append({"key": "lakshmi", "name": "Lakshmi Yoga", "grahas": [l9],
                    "factors": [f"9th lord {l9} {l9_d} in house {grahas[l9]['house']}"]})

    # ── Parivartana (sign exchange) — Maha / Khala / Dainya ──────────────────
    from .constants import SIGN_LORD as _SL
    dainya_h = {6, 8, 12}
    khala_h = {3}
    seen_pairs = set()
    for g1 in seven:
        disp = _SL[grahas[g1]["sign"]]
        if disp == g1 or disp not in grahas or disp in ("rahu", "ketu"):
            continue
        if _SL[grahas[disp]["sign"]] == g1:
            pair = tuple(sorted((g1, disp)))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            h1, h2 = grahas[pair[0]]["house"], grahas[pair[1]]["house"]
            if dainya_h & {h1, h2}:
                kind, kname = "dainya", "Dainya Parivartana"
            elif khala_h & {h1, h2}:
                kind, kname = "khala", "Khala Parivartana"
            else:
                kind, kname = "maha", "Maha Parivartana"
            out.append({"key": f"parivartana_{kind}_{pair[0]}_{pair[1]}",
                        "name": f"{kname} Yoga", "grahas": list(pair),
                        "factors": [f"{pair[0]} (house {h1}) and {pair[1]} (house {h2}) exchange signs"]})
    return out

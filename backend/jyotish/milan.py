"""Kundli Milan — Ashtakoota (36 guna) + Manglik dosha. Deterministic.

Inputs are two computed ChartV1 dicts (conventionally boy/groom first,
girl/bride second — several kootas are direction-sensitive). Every koota
returns its points AND the reasoning factors, so the AI layer can narrate the
score without inventing numbers.

Table conventions (variants exist across regional traditions; these are the
tables used by mainstream Jyotish software, cross-checked in review):
  - Yoni 14x14 matrix: standard Muhurta table (diagonal 4, seven sworn-enemy
    pairs 0). Symmetric.
  - Vashya 5x5 matrix: Kalaprakasika-style, direction-sensitive.
  - Gana: Deva/Manushya asymmetry (deva groom + manushya bride 6; reversed 5).
Dashakoota (South Indian 10-koota) is a tracked follow-up.
"""

from __future__ import annotations

from .constants import NAKSHATRAS, SIGN_LORD
from .dignity import natural_relation
from .nakshatra import SPAN as NAK_SPAN

# ── Varna (1) ────────────────────────────────────────────────────────────────
# Sign element → varna. Rank: Brahmin 3 > Kshatriya 2 > Vaishya 1 > Shudra 0.
_VARNA_BY_ELEMENT = {"water": ("Brahmin", 3), "fire": ("Kshatriya", 2),
                     "earth": ("Vaishya", 1), "air": ("Shudra", 0)}
_ELEMENTS = ["fire", "earth", "air", "water"]  # sign index % 4


def _varna(sign: int) -> tuple[str, int]:
    return _VARNA_BY_ELEMENT[_ELEMENTS[sign % 4]]


# ── Vashya (2) ───────────────────────────────────────────────────────────────
_VASHYA_GROUPS = ["chatushpada", "manava", "jalachara", "vanachara", "keeta"]
_VASHYA_MATRIX = {  # groom group -> bride group -> points
    "chatushpada": {"chatushpada": 2, "manava": 1, "jalachara": 1, "vanachara": 0, "keeta": 1},
    "manava": {"chatushpada": 1, "manava": 2, "jalachara": 0.5, "vanachara": 0, "keeta": 1},
    "jalachara": {"chatushpada": 1, "manava": 0.5, "jalachara": 2, "vanachara": 1, "keeta": 1},
    "vanachara": {"chatushpada": 0, "manava": 0, "jalachara": 1, "vanachara": 2, "keeta": 0},
    "keeta": {"chatushpada": 1, "manava": 1, "jalachara": 1, "vanachara": 0, "keeta": 2},
}


def _vashya_group(moon_lon: float) -> str:
    sign = int((moon_lon % 360.0) // 30)
    deg = (moon_lon % 360.0) % 30.0
    if sign in (0, 1):
        return "chatushpada"
    if sign in (2, 5, 6, 10):
        return "manava"
    if sign in (3, 11):
        return "jalachara"
    if sign == 4:
        return "vanachara"
    if sign == 7:
        return "keeta"
    if sign == 8:  # Sagittarius: first half human (archer), second half horse
        return "manava" if deg < 15.0 else "chatushpada"
    # Capricorn: first half quadruped (goat), second half water (crocodile tail)
    return "chatushpada" if deg < 15.0 else "jalachara"


# ── Tara (3) ─────────────────────────────────────────────────────────────────
_BAD_TARAS = {3, 5, 7}  # Vipat, Pratyari, Naidhana


def _tara_count(from_nak: int, to_nak: int) -> int:
    """Inclusive count from one nakshatra to another, folded to 1..9."""
    return ((to_nak - from_nak) % 27) % 9 + 1


# ── Yoni (4) ─────────────────────────────────────────────────────────────────
_YONI_ANIMALS = ["horse", "elephant", "sheep", "serpent", "dog", "cat", "rat",
                 "cow", "buffalo", "tiger", "deer", "monkey", "mongoose", "lion"]
# nakshatra index -> animal index (standard mapping; Abhijit not used in 27-scheme)
_NAK_YONI = {
    0: 0, 23: 0,          # Ashwini, Shatabhisha — horse
    1: 1, 26: 1,          # Bharani, Revati — elephant
    2: 2, 7: 2,           # Krittika, Pushya — sheep
    3: 3, 4: 3,           # Rohini, Mrigashira — serpent
    5: 4, 18: 4,          # Ardra, Mula — dog
    6: 5, 8: 5,           # Punarvasu, Ashlesha — cat
    9: 6, 10: 6,          # Magha, P.Phalguni — rat
    11: 7, 25: 7,         # U.Phalguni, U.Bhadrapada — cow
    12: 8, 14: 8,         # Hasta, Swati — buffalo
    13: 9, 15: 9,         # Chitra, Vishakha — tiger
    16: 10, 17: 10,       # Anuradha, Jyeshtha — deer
    19: 11, 21: 11,       # P.Ashadha, Shravana — monkey
    20: 12,               # U.Ashadha — mongoose
    22: 13, 24: 13,       # Dhanishta, P.Bhadrapada — lion
}
# Standard Muhurta 14x14 (symmetric). Rows/cols in _YONI_ANIMALS order.
_YONI_MATRIX = [
    # ho el sh se do ca ra co bu ti de mo mg li
    [4, 2, 2, 3, 2, 2, 2, 1, 0, 1, 3, 3, 2, 1],  # horse
    [2, 4, 3, 3, 2, 2, 2, 2, 3, 1, 2, 3, 2, 0],  # elephant
    [2, 3, 4, 2, 1, 2, 1, 3, 3, 1, 2, 0, 3, 1],  # sheep
    [3, 3, 2, 4, 2, 1, 1, 1, 1, 2, 2, 2, 0, 2],  # serpent
    [2, 2, 1, 2, 4, 2, 1, 2, 2, 1, 0, 2, 1, 1],  # dog
    [2, 2, 2, 1, 2, 4, 0, 2, 2, 1, 3, 3, 2, 1],  # cat
    [2, 2, 1, 1, 1, 0, 4, 2, 2, 2, 2, 2, 1, 2],  # rat
    [1, 2, 3, 1, 2, 2, 2, 4, 3, 0, 3, 2, 2, 1],  # cow
    [0, 3, 3, 1, 2, 2, 2, 3, 4, 1, 2, 2, 2, 1],  # buffalo
    [1, 1, 1, 2, 1, 1, 2, 0, 1, 4, 1, 1, 2, 1],  # tiger
    [3, 2, 2, 2, 0, 3, 2, 3, 2, 1, 4, 2, 2, 1],  # deer
    [3, 3, 0, 2, 2, 3, 2, 2, 2, 1, 2, 4, 3, 2],  # monkey
    [2, 2, 3, 0, 1, 2, 1, 2, 2, 2, 2, 3, 4, 2],  # mongoose
    [1, 0, 1, 2, 1, 1, 2, 1, 1, 1, 1, 2, 2, 4],  # lion
]

# ── Graha Maitri (5) ─────────────────────────────────────────────────────────
_MAITRI_SCORE = {
    ("friend", "friend"): 5.0, ("friend", "neutral"): 4.0, ("neutral", "friend"): 4.0,
    ("neutral", "neutral"): 3.0, ("friend", "enemy"): 1.0, ("enemy", "friend"): 1.0,
    ("neutral", "enemy"): 0.5, ("enemy", "neutral"): 0.5, ("enemy", "enemy"): 0.0,
}

# ── Gana (6) ─────────────────────────────────────────────────────────────────
_GANA_OF_NAK = {
    "deva": {0, 4, 6, 7, 12, 14, 16, 21, 26},
    "manushya": {1, 3, 5, 10, 11, 19, 20, 24, 25},
    "rakshasa": {2, 8, 9, 13, 15, 17, 18, 22, 23},
}
_GANA_MATRIX = {  # groom -> bride -> points
    "deva": {"deva": 6, "manushya": 6, "rakshasa": 1},
    "manushya": {"deva": 5, "manushya": 6, "rakshasa": 0},
    "rakshasa": {"deva": 1, "manushya": 0, "rakshasa": 6},
}


def _gana(nak: int) -> str:
    for g, s in _GANA_OF_NAK.items():
        if nak in s:
            return g
    raise ValueError(f"nakshatra {nak} not in gana table")


# ── Nadi (8) ─────────────────────────────────────────────────────────────────
_NADI_OF_NAK = {
    "adi": {0, 5, 6, 11, 12, 17, 18, 23, 24},
    "madhya": {1, 4, 7, 10, 13, 16, 19, 22, 25},
    "antya": {2, 3, 8, 9, 14, 15, 20, 21, 26},
}


def _nadi(nak: int) -> str:
    for n, s in _NADI_OF_NAK.items():
        if nak in s:
            return n
    raise ValueError(f"nakshatra {nak} not in nadi table")


# ── Manglik ──────────────────────────────────────────────────────────────────
_MANGLIK_HOUSES = {1, 2, 4, 7, 8, 12}  # 2nd per South Indian tradition — reported


def _manglik(chart: dict) -> dict:
    mars = chart["grahas"]["mars"]
    lagna_sign = chart["lagna"]["sign"]
    moon_sign = chart["grahas"]["moon"]["sign"]
    from_lagna = mars["house"]
    from_moon = (mars["sign"] - moon_sign) % 12 + 1
    is_from_lagna = from_lagna in _MANGLIK_HOUSES
    is_from_moon = from_moon in _MANGLIK_HOUSES

    cancellations = []
    if mars["sign"] in (0, 7):
        cancellations.append("Mars in own sign (Aries/Scorpio)")
    if mars["sign"] == 9:
        cancellations.append("Mars exalted in Capricorn")
    jup = chart["grahas"]["jupiter"]
    if ((mars["sign"] - jup["sign"]) % 12 + 1) in (5, 7, 9):
        cancellations.append("Mars aspected by Jupiter (5/7/9 drishti)")

    return {
        "from_lagna": {"house": from_lagna, "manglik": is_from_lagna},
        "from_moon": {"house": from_moon, "manglik": is_from_moon},
        "is_manglik": is_from_lagna or is_from_moon,
        "cancellations": cancellations,
        "note": "House 2 counts as Manglik per South Indian tradition. "
                "Cancellations reduce severity; both charts Manglik also neutralises.",
    }


# ── The match ────────────────────────────────────────────────────────────────

def _moon_of(chart: dict) -> tuple[float, int, int]:
    m = chart["grahas"]["moon"]
    return m["lon"], m["sign"], m["nakshatra"]["index"]


def match(boy: dict, girl: dict) -> dict:
    """Ashtakoota guna milan between two ChartV1 dicts (boy first, girl second)."""
    b_lon, b_sign, b_nak = _moon_of(boy)
    g_lon, g_sign, g_nak = _moon_of(girl)
    kootas = []

    # 1 — Varna
    bv, bvr = _varna(b_sign)
    gv, gvr = _varna(g_sign)
    varna_pts = 1.0 if bvr >= gvr else 0.0
    kootas.append({"koota": "varna", "max": 1, "points": varna_pts,
                   "boy": bv, "girl": gv})

    # 2 — Vashya
    bg, gg = _vashya_group(b_lon), _vashya_group(g_lon)
    kootas.append({"koota": "vashya", "max": 2,
                   "points": float(_VASHYA_MATRIX[bg][gg]), "boy": bg, "girl": gg})

    # 3 — Tara (both directions, 1.5 each when benign)
    t1 = _tara_count(g_nak, b_nak)   # bride → groom
    t2 = _tara_count(b_nak, g_nak)   # groom → bride
    tara_pts = (0.0 if t1 in _BAD_TARAS else 1.5) + (0.0 if t2 in _BAD_TARAS else 1.5)
    kootas.append({"koota": "tara", "max": 3, "points": tara_pts,
                   "boy": f"tara {t1} from girl", "girl": f"tara {t2} from boy"})

    # 4 — Yoni
    by, gy = _NAK_YONI[b_nak], _NAK_YONI[g_nak]
    kootas.append({"koota": "yoni", "max": 4, "points": float(_YONI_MATRIX[by][gy]),
                   "boy": _YONI_ANIMALS[by], "girl": _YONI_ANIMALS[gy]})

    # 5 — Graha Maitri (Moon-sign lords)
    bl, gl = SIGN_LORD[b_sign], SIGN_LORD[g_sign]
    if bl == gl:
        maitri_pts = 5.0
    else:
        maitri_pts = _MAITRI_SCORE[(natural_relation(bl, gl), natural_relation(gl, bl))]
    kootas.append({"koota": "graha_maitri", "max": 5, "points": maitri_pts,
                   "boy": bl, "girl": gl})

    # 6 — Gana
    bga, gga = _gana(b_nak), _gana(g_nak)
    kootas.append({"koota": "gana", "max": 6, "points": float(_GANA_MATRIX[bga][gga]),
                   "boy": bga, "girl": gga})

    # 7 — Bhakoot (mutual Moon-sign positions; 2/12, 5/9, 6/8 are dosha)
    diff = (g_sign - b_sign) % 12 + 1
    rev = (b_sign - g_sign) % 12 + 1
    bhakoot_dosha = {diff, rev} in ({2, 12}, {5, 9}, {6, 8})
    bhakoot_exception = bhakoot_dosha and (
        bl == gl or (natural_relation(bl, gl) == "friend" and natural_relation(gl, bl) == "friend"))
    kootas.append({"koota": "bhakoot", "max": 7,
                   "points": 0.0 if bhakoot_dosha else 7.0,
                   "boy": boy["moon_sign_name"], "girl": girl["moon_sign_name"],
                   "dosha": bhakoot_dosha,
                   "exception": "Moon-sign lords same/mutual friends — dosha considered "
                                "mitigated by tradition" if bhakoot_exception else None})

    # 8 — Nadi
    bn, gn = _nadi(b_nak), _nadi(g_nak)
    nadi_dosha = bn == gn
    nadi_exception = None
    if nadi_dosha:
        if b_nak == g_nak and b_sign != g_sign:
            nadi_exception = "Same nakshatra, different rashi — classical exception"
        elif b_sign == g_sign and b_nak != g_nak:
            nadi_exception = "Same rashi, different nakshatra — classical exception"
    kootas.append({"koota": "nadi", "max": 8, "points": 0.0 if nadi_dosha else 8.0,
                   "boy": bn, "girl": gn, "dosha": nadi_dosha, "exception": nadi_exception})

    total = sum(k["points"] for k in kootas)
    if total >= 32:
        verdict = "excellent"
    elif total >= 25:
        verdict = "very_good"
    elif total >= 18:
        verdict = "acceptable"
    else:
        verdict = "below_threshold"

    return {
        "schema": "MilanV1",
        "total": total,
        "max": 36,
        "verdict": verdict,
        "kootas": kootas,
        "boy": {"moon_sign": boy["moon_sign_name"], "nakshatra": NAKSHATRAS[b_nak],
                "manglik": _manglik(boy)},
        "girl": {"moon_sign": girl["moon_sign_name"], "nakshatra": NAKSHATRAS[g_nak],
                 "manglik": _manglik(girl)},
        "manglik_note": _manglik_verdict(_manglik(boy), _manglik(girl)),
        "dashakoota": dashakoota(b_nak, g_nak),
        "doshas": [k["koota"] for k in kootas if k.get("dosha")],
        "disclaimer": "Guna milan is one traditional lens; doshas carry classical "
                      "exceptions and a low score alone is not a verdict on a marriage.",
    }


def _manglik_verdict(bm: dict, gm: dict) -> str:
    if bm["is_manglik"] and gm["is_manglik"]:
        return "Both charts are Manglik — the dosha is traditionally neutralised between them."
    if bm["is_manglik"] or gm["is_manglik"]:
        who = "boy" if bm["is_manglik"] else "girl"
        m = bm if bm["is_manglik"] else gm
        if m["cancellations"]:
            return (f"The {who}'s chart is Manglik but carries cancellation factors: "
                    + "; ".join(m["cancellations"]))
        return f"The {who}'s chart is Manglik; the other is not — traditionally weighed carefully."
    return "Neither chart is Manglik."


# ── Dashakoota additions (South Indian practice) ─────────────────────────────
# Rajju is held the most important of these; a same-rajju match is a classical
# objection (Siro rajju gravest). Vedha pairs "pierce" each other. Mahendra
# supports longevity/progeny; Stree-deergha asks the boy's nakshatra to be
# well beyond the girl's.

_RAJJU = {
    "pada": {0, 8, 9, 17, 18, 26},        # Ashwini, Ashlesha, Magha, Jyeshtha, Mula, Revati
    "kati": {1, 7, 10, 16, 19, 25},       # Bharani, Pushya, P.Phalguni, Anuradha, P.Ashadha, U.Bhadrapada
    "nabhi": {2, 6, 11, 15, 20, 24},      # Krittika, Punarvasu, U.Phalguni, Vishakha, U.Ashadha, P.Bhadrapada
    "kantha": {3, 5, 12, 14, 21, 23},     # Rohini, Ardra, Hasta, Swati, Shravana, Shatabhisha
    "siro": {4, 13, 22},                  # Mrigashira, Chitra, Dhanishta
}

# Classical vedha (piercing) nakshatra pairs; Chitra stands alone (no full-pair
# vedha in the common 13-pair table — documented simplification).
_VEDHA_PAIRS = [
    (0, 17), (1, 16), (2, 15), (3, 14), (4, 22), (5, 21), (6, 20),
    (7, 19), (8, 18), (9, 26), (10, 25), (11, 24), (12, 23),
]


def _rajju_of(nak: int) -> str:
    for name, members in _RAJJU.items():
        if nak in members:
            return name
    return "unknown"


def dashakoota(boy_nak: int, girl_nak: int) -> dict:
    """The four Dashakoota checks beyond Ashtakoota overlap: Rajju, Vedha,
    Mahendra, Stree-deergha. (Dina/Gana/Yoni/Rasi/Vashya/Rasyadhipati already
    surface through the Ashtakoota tables.)"""
    b_rajju, g_rajju = _rajju_of(boy_nak), _rajju_of(girl_nak)
    rajju_dosha = b_rajju == g_rajju
    vedha = any({boy_nak, girl_nak} == {a, b} for a, b in _VEDHA_PAIRS)
    # Mahendra: boy's nakshatra counted from the girl's at 4,7,10,... (steps of 3)
    count_g_to_b = (boy_nak - girl_nak) % 27 + 1
    mahendra = count_g_to_b in (4, 7, 10, 13, 16, 19, 22, 25)
    # Stree-deergha: the same count should exceed 13 (variant: 9 — noted).
    stree_deergha = count_g_to_b > 13
    return {
        "rajju": {"boy": b_rajju, "girl": g_rajju, "dosha": rajju_dosha,
                  "severity": ("grave" if rajju_dosha and b_rajju == "siro" else
                               "significant" if rajju_dosha else None),
                  "note": "Same rajju is a classical objection; Siro rajju gravest."
                          if rajju_dosha else "Different rajjus — favourable."},
        "vedha": {"dosha": vedha,
                  "note": "Nakshatras mutually pierce (vedha) — classical objection."
                          if vedha else "No vedha between the nakshatras."},
        "mahendra": {"present": mahendra, "count": count_g_to_b,
                     "note": "Supports longevity and protection." if mahendra else
                             "Not formed (informational, not a dosha)."},
        "stree_deergha": {"present": stree_deergha, "count": count_g_to_b,
                          "note": "Count from girl's to boy's nakshatra exceeds 13 — "
                                  "favourable (some traditions accept >9)."
                                  if stree_deergha else
                                  "Count 13 or below — weaker on this koota (variant threshold 9)."},
    }

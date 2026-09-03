"""Fine divisional tables — Nadiamsa (D-150) and Pushkara navamsa/bhaga.

Nadiamsa: each sign divides into 150 parts of 12' (0°12' = 0.2°) — 1800
nadiamsas around the zodiac. Names follow the Chandra Kala Nadi (Deva
Keralam) list as compiled by C. S. Patel from the Adyar Library manuscript
(the list most widely reproduced, e.g. in nadi literature and JHora):
Vasudha (1) .. Parameshvari (150). A few names legitimately repeat in the
canonical list (e.g. Durbhaga at #37 and #62, Sukhada at #43 and #77);
Haarini (#117, hāriṇī) and Harini (#118, hariṇī) are distinct entries.

Name-counting scheme (standard Chandra Kala Nadi convention):
  - MOVABLE signs (Aries, Cancer, Libra, Capricorn): names run 1 -> 150;
  - FIXED signs (Taurus, Leo, Scorpio, Aquarius):    names run 150 -> 1;
  - DUAL signs (Gemini, Virgo, Sagittarius, Pisces): names start at #76
    (Sushitala) -> #150, then wrap #1 -> #75.

Pushkara: the pushkara-navamsa table per element and the single
pushkara-bhaga degree per sign, per the standard published tables (as used
by JHora; bhaga degrees 21, 14, 24, 8, 19, 9, 24, 11, 23, 14, 19, 9 for
Aries..Pisces).
"""

from __future__ import annotations

_EPS = 1e-9

NADI_SPAN = 30.0 / 150.0  # 0.2 degrees = 12 minutes of arc

# The 150 nadiamsa names (ASCII transliteration), C. S. Patel / Chandra Kala
# Nadi ordering: index 0 = nadiamsa #1 (Vasudha) .. index 149 = #150.
NADIAMSA_NAMES: tuple[str, ...] = (
    "Vasudha", "Vaishnavi", "Brahmi", "Kalakuta", "Sankari",
    "Sudhakari", "Sama", "Saumya", "Sura", "Maya",
    "Manohara", "Madhvi", "Manjusvana", "Ghora", "Kumbhini",
    "Kutila", "Prabha", "Para", "Payasvini", "Mala",
    "Jagati", "Jarjhara", "Dhruva", "Musala", "Mudgara",
    "Pasha", "Champaka", "Damaka", "Mahi", "Kalusha",
    "Kamala", "Kanta", "Kala", "Karikara", "Kshama",
    "Durdhara", "Durbhaga", "Vishva", "Vishirna", "Vikata",
    "Avila", "Viprabha", "Sukhada", "Snigdha", "Sodara",
    "Surasundari", "Amritaplavini", "Kaala", "Kamadhuk", "Karavirani",
    "Gahvara", "Kundini", "Raudra", "Vishakhya", "Vishanashini",
    "Nirmada", "Shitala", "Nimna", "Prita", "Priyavardhini",
    "Managhna", "Durbhaga", "Chitra", "Chimini", "Chiranjivini",
    "Bhupa", "Gadahara", "Nala", "Nalini", "Nirmala",
    "Nadi", "Sudhamritamshu", "Kalushankura", "Trailokyamohanakari", "Mahamari",
    "Sushitala", "Sukhada", "Suprabha", "Shobha", "Shobhana",
    "Shivada", "Shiva", "Bala", "Jvala", "Gada",
    "Gadha", "Nutana", "Sumanohara", "Somaballi", "Somalata",
    "Mangala", "Mudrika", "Kshudha", "Mokshapavarga", "Balaya",
    "Navanita", "Nishakari", "Nivritti", "Nigada", "Sara",
    "Sangita", "Samada", "Sabha", "Vishvambhara", "Kumari",
    "Kokila", "Kunjarakriti", "Aindra", "Svaha", "Svara",
    "Brahmi", "Prita", "Rakshajalaplava", "Varuni", "Madira",
    "Maitri", "Haarini", "Harini", "Marut", "Dhananjaya",
    "Dhanakari", "Dhanada", "Kachchhapa", "Ambuja", "Mamshani",
    "Shulini", "Raudri", "Shiva", "Shivakari", "Kalaa",
    "Kunda", "Mukunda", "Bharata", "Hasita", "Kadali",
    "Smara", "Kandala", "Kokila", "Papa", "Kamini",
    "Kalashodbhava", "Viraprasu", "Sangara", "Shatayajna", "Shatavari",
    "Prahvi", "Patalini", "Naga", "Pankaja", "Parameshvari",
)

# Pushkara navamsas (0-based navamsa index within the sign) per element.
# Standard table (JHora): fire 7th & 9th; earth 3rd & 5th; air 6th & 8th;
# water 1st & 3rd — e.g. Aries 20°00'-23°20' (7th) and 26°40'-30°00' (9th).
PUSHKARA_NAVAMSAS: dict[int, frozenset[int]] = {
    0: frozenset({6, 8}),  # fire:  Aries, Leo, Sagittarius
    1: frozenset({2, 4}),  # earth: Taurus, Virgo, Capricorn
    2: frozenset({5, 7}),  # air:   Gemini, Libra, Aquarius
    3: frozenset({0, 2}),  # water: Cancer, Scorpio, Pisces
}

# Pushkara bhaga DEGREE per sign, Aries..Pisces (standard published list,
# e.g. JHora). "Aries 21°" means the 21st degree of Aries, i.e. the span
# 20°00'-21°00' of the sign: floor(deg_in_sign) + 1 == value.
PUSHKARA_BHAGA: tuple[int, ...] = (21, 14, 24, 8, 19, 9, 24, 11, 23, 14, 19, 9)


def _sign(lon: float) -> int:
    return int((lon % 360.0) // 30)


def _deg(lon: float) -> float:
    return (lon % 360.0) % 30.0


def d150(lon: float) -> dict:
    """Nadiamsa (D-150) of a longitude.

    Returns:
      index        — 0-149 positional nadiamsa within the sign (0.2° each);
      global_index — 0-1799 around the zodiac (sign*150 + index);
      name_index   — 0-149 index into NADIAMSA_NAMES after applying the
                     movable/fixed/dual counting scheme (see module doc);
      name         — the nadiamsa name;
      sign         — sign index 0-11.
    """
    sign = _sign(lon)
    idx = min(149, int((_deg(lon) + _EPS) / NADI_SPAN))
    modality = sign % 3  # 0 movable, 1 fixed, 2 dual
    if modality == 0:
        name_index = idx
    elif modality == 1:
        name_index = 149 - idx
    else:
        name_index = (75 + idx) % 150
    return {
        "index": idx,
        "global_index": sign * 150 + idx,
        "name_index": name_index,
        "name": NADIAMSA_NAMES[name_index],
        "sign": sign,
    }


def pushkara(lon: float) -> dict:
    """Pushkara navamsa and pushkara bhaga status of a longitude.

    is_pushkara_navamsa — the longitude falls in one of the sign's two
      pushkara navamsas (element table above).
    is_pushkara_bhaga — the longitude falls in the sign's pushkara-bhaga
      DEGREE (the specific whole degree: floor(deg_in_sign) + 1 == the
      published degree number; e.g. Aries 21° = 20°00'-21°00').
    navamsa_index_in_sign — 0-based (0-8) navamsa index within the sign.
    """
    sign = _sign(lon)
    deg = _deg(lon)
    nav_idx = min(8, int((deg + _EPS) / (30.0 / 9.0)))
    return {
        "is_pushkara_navamsa": nav_idx in PUSHKARA_NAVAMSAS[sign % 4],
        "is_pushkara_bhaga": int(deg) + 1 == PUSHKARA_BHAGA[sign],
        "navamsa_index_in_sign": nav_idx,
        "sign": sign,
    }

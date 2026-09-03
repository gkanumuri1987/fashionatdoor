"""Hindu calendar arithmetic — ahargana, era years, the 60-year Jupiter cycle,
and the pre-Gregorian honesty note.

Scope note: these are the CIVIL/computational conventions used by mainstream
panchangas, documented per function. Exact lunar (Ugadi-boundary) era years
would require the masa machinery; the standard civil approximation used here
is stated explicitly where it applies.
"""

from __future__ import annotations

from .ephemeris import jd_to_utc, sidereal_positions

# Kali Yuga epoch: JD 588465.5 = Feb 18, 3102 BCE (proleptic Gregorian:
# Jan 23, -3101), midnight at Ujjain. Convention: the classical siddhantas
# use either the midnight (ardharatrika, JD 588465.5) or sunrise (audayika,
# JD 588465.75 at Ujjain ≈ 588466.0 civil) epoch; we use the MIDNIGHT value
# 588465.5, the common computational choice.
KALI_EPOCH_JD = 588465.5

SAMVATSARA_NAMES = [
    "Prabhava", "Vibhava", "Shukla", "Pramoda", "Prajapati", "Angirasa",
    "Shrimukha", "Bhava", "Yuva", "Dhatri", "Ishvara", "Bahudhanya",
    "Pramathi", "Vikrama", "Vrisha", "Chitrabhanu", "Svabhanu", "Tarana",
    "Parthiva", "Vyaya", "Sarvajit", "Sarvadhari", "Virodhi", "Vikriti",
    "Khara", "Nandana", "Vijaya", "Jaya", "Manmatha", "Durmukha",
    "Hemalamba", "Vilambi", "Vikari", "Sharvari", "Plava", "Shubhakrit",
    "Shobhakrit", "Krodhi", "Vishvavasu", "Parabhava", "Plavanga", "Kilaka",
    "Saumya", "Sadharana", "Virodhikrit", "Paridhavi", "Pramadi", "Ananda",
    "Rakshasa", "Nala", "Pingala", "Kalayukti", "Siddharthi", "Raudra",
    "Durmati", "Dundubhi", "Rudhirodgari", "Raktakshi", "Krodhana", "Akshaya",
]

# Southern (Chaitradi/Meshadi) cycle: offset calibrated on the anchor
# Saka 1947 (2025-26 CE) = Vishvavasu (index 38): (1947 + 11) % 60 == 38.
_SOUTH_OFFSET = 11

# Northern (mean-Jupiter) cycle: one samvatsara per mean-Jupiter year of
# 361.026721 days (the Jupiter "barhaspatya" year: the time mean Jupiter
# takes to traverse one sign, sidereal period 4332.32 d / 12 ≈ 361.03 d).
# Offset calibrated so 2025-26 lands on/within ±1 of Vishvavasu (index 38):
# floor(kali_ahargana(2025-06-01) / 361.026721) = 5186; (5186 + 12) % 60 = 38.
# The northern name legitimately DIFFERS from the southern name in the same
# year — the north expunges (kshaya) samvatsaras when mean Jupiter slips a
# sign in under a solar year, so the two cycles have drifted historically.
_MEAN_JUPITER_YEAR_DAYS = 361.026721
_NORTH_OFFSET = 12


def kali_ahargana(jd_ut: float) -> float:
    """Days elapsed since the Kali Yuga epoch (JD 588465.5 — see module note)."""
    return jd_ut - KALI_EPOCH_JD


def _era_year(jd_ut: float, offset: int) -> int:
    """gregorian_year - offset, minus 1 before the year's Mesha sankranti.

    Standard civil approximation (documented): the Saka/Vikrama year is taken
    to turn at the SIDEREAL Mesha sankranti (mid-April) rather than the exact
    Chaitradi lunar new year (Ugadi, which falls days-to-weeks earlier).
    Between Ugadi and the Mesha sankranti this approximation is one year low;
    everywhere else it matches the almanacs.

    Before-sankranti test: months 1-3 are always before; in April the sidereal
    Sun is in Meena (lon ≥ 180°, actually ~330-360°) before the crossing and
    in Mesha (lon < 30°) after.
    """
    u = jd_to_utc(jd_ut)
    sun_lon = sidereal_positions(jd_ut)["sun"]["lon"]
    before_mesha = u.month < 4 or (u.month == 4 and sun_lon >= 180.0)
    return u.year - offset - (1 if before_mesha else 0)


def saka_year(jd_ut: float) -> int:
    """Salivahana Saka year (civil approximation: gregorian - 78, -1 before
    the year's Mesha sankranti)."""
    return _era_year(jd_ut, 78)


def vikrama_year(jd_ut: float) -> int:
    """Vikrama samvat year (civil approximation: gregorian + 57 → offset -57,
    -1 before the year's Mesha sankranti)."""
    return _era_year(jd_ut, -57)


def samvatsara(jd_ut: float, scheme: str = "telugu_lunar") -> dict:
    """Name of the year in the 60-samvatsara Jupiter cycle.

    Schemes:
      - "telugu_lunar": Chaitradi (southern) — index (saka + 11) % 60,
        anchored on Saka 1947 (2025-26) = Vishvavasu. Year boundary here is
        the civil-approximated Saka turn (see _era_year note re Ugadi).
      - "tamil_solar": Meshadi — the SAME southern cycle, year boundary at
        the Mesha sankranti. Our civil Saka year already turns at the Mesha
        sankranti, so the index formula is identical; only the (already
        applied) boundary differs from the strict lunar reckoning.
      - "north_jupiter": mean-Jupiter based — floor(kali_ahargana /
        361.026721) + offset, calibrated to the 2025-26 anchor. Historically
        the northern name can DIFFER from the southern name in the same year
        (expunged samvatsaras) — that is expected, not a bug.
    """
    if scheme in ("telugu_lunar", "tamil_solar"):
        saka = saka_year(jd_ut)
        idx = (saka + _SOUTH_OFFSET) % 60
        note = ("Chaitradi cycle from the Saka year (civil approximation; "
                "strict boundary is Ugadi)." if scheme == "telugu_lunar" else
                "Meshadi cycle — year turns at the Mesha sankranti.")
    elif scheme == "north_jupiter":
        idx = (int(kali_ahargana(jd_ut) // _MEAN_JUPITER_YEAR_DAYS)
               + _NORTH_OFFSET) % 60
        note = ("Mean-Jupiter (barhaspatya) cycle; can differ from the "
                "southern name in the same year due to expunged samvatsaras.")
    else:
        raise ValueError(f"unknown samvatsara scheme: {scheme!r}")
    return {"scheme": scheme, "index": idx,
            "name": SAMVATSARA_NAMES[idx], "note": note}


def julian_calendar_note(y: int, m: int, d: int) -> str | None:
    """Honesty flag for pre-Gregorian dates.

    The engine (like swisseph as we call it) treats input dates as PROLEPTIC
    GREGORIAN. Historical records before 1582-10-15 are usually JULIAN
    (about 10 days behind in the 1500s), so a date copied from an old source
    needs converting before the chart is meaningful. Conversion itself is out
    of scope — this note is the flag. Returns None for 1582-10-15 and later.
    """
    if (y, m, d) < (1582, 10, 15):
        return ("Date precedes the Gregorian reform (1582-10-15): the engine "
                "treats it as PROLEPTIC GREGORIAN, but historical records of "
                "that era are usually JULIAN (~10 days offset in the 1500s). "
                "Convert Julian dates to proleptic Gregorian before input.")
    return None

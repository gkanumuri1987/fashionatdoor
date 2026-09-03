"""Surya Siddhanta positions (traditional ganita) + Vakya moon.

PARITY/COMPARISON MODE — NOT the default engine. The app's default remains
DRIK (Swiss Ephemeris, ``ephemeris.py``); this module exists so a traditional
siddhantic panchanga can be shown SIDE-BY-SIDE with the drik values
("traditional vs modern" transparency). Expect the documented deviations —
they are the point, not a bug.

Conventions (documented per the audit style):

* EPOCH — Kali Yuga epoch alignment: at ahargana 0 (JD 588465.5, see
  ``calendar_hindu.KALI_EPOCH_JD``) ALL mean PLANETS are taken at 0° — the
  classical Surya Siddhanta epoch convention (mean conjunction at 0° Mesha
  at the Kali epoch). The text additionally specifies the moon's apogee at
  90° and Rahu (the node) at 180° at that epoch — applied as the KSHEPA
  epoch offsets below. No bija corrections are applied (pure canonical
  parameters).
* MEAN MOTION — revolutions per Mahayuga over 1,577,917,828 civil days, the
  canonical Surya Siddhanta counts. Rahu's revolutions are RETROGRADE (the
  node moves backwards): its longitude is the negated accumulation.
* MANDA — the SS iterative manda scheme simplified to ONE application of the
  equation: sin(eq) = (paridhi/360) × sin(kendra), kendra = mandocca − mean.
  Adding the signed equation handles both hemispheres (the classical
  "subtract past apogee / add past perigee" falls out of the sine's sign).
  Paridhis are the EVEN-sign values used as fixed constants (the odd/even
  interpolation of the full text is omitted — documented simplification).
* SHIGHRA — the SS half-manda/half-shighra iteration simplified to the
  standard sequence: manda on the mean, then one shighra conversion
  eq = atan2(r·sin k, 1 + r·cos k) with r = shighra-paridhi/360 — the
  standard epicyclic (hypotenuse) conversion of epicycle offset to
  geocentric angle. For Mars/Jupiter/Saturn the sighrocca is the SUN's mean
  longitude; for Mercury/Venus the mean planet IS the sun's mean and the
  sighrocca comes from their own sighra revolutions. The manda for
  Mercury/Venus is applied to that mean (sun) with their own mandocca —
  per-step simplification of the full four-step scheme, documented.
* VAKYA MOON — COMPUTATIONAL vakya, not the literal 248 memorized sentences:
  the Vararuchi/Tamil method rests on the moon's 248-day anomalistic cycle
  (248 days ≈ 9 anomalistic months), after which the true-longitude PATTERN
  repeats shifted by a near-constant (~27.7°/cycle). We reproduce that
  structure from our own SS true moon: longitude = SS-true-moon at the same
  phase of the cycle anchored at the 2000-01-01 epoch, plus whole-cycle
  shifts. See ``vakya_moon`` for the calibration constants.

Accuracy expectation: this simplified single-iteration scheme differs from
drik by up to ~1–2° for sun/moon and several degrees for the five planets —
the comparison bands, not exactness, are what is tested.
"""

from __future__ import annotations

import math

from .calendar_hindu import kali_ahargana
from .constants import NAKSHATRAS, TITHIS, YOGAS_27, karana_name

# ── Canonical Surya Siddhanta parameters ─────────────────────────────────────

# Civil days per Mahayuga (4,320,000 sidereal years).
CIVIL_DAYS_PER_MAHAYUGA = 1_577_917_828

# Revolutions per Mahayuga — the canonical SS counts. "mercury_sighra" /
# "venus_sighra" are the sighrocca revolutions (the mean PLANET of an
# inferior is the sun); "moon_apogee" is the mandocca (it moves, unlike the
# planets' fixed apogees below); "rahu" is retrograde (see mean_longitude_ss).
REVOLUTIONS = {
    "sun": 4_320_000,
    "moon": 57_753_336,
    "mars": 2_296_832,
    "mercury_sighra": 17_937_060,
    "jupiter": 364_220,
    "venus_sighra": 7_022_376,
    "saturn": 146_568,
    "moon_apogee": 488_203,
    "rahu": 232_238,
}

# Kshepa (epoch positions at ahargana 0): mean PLANETS all start at 0°, but
# the SS specifies the moon's apogee at 90° and the node (Rahu) at 180° at
# the Kali epoch. Applied additively (before Rahu's retrograde negation is
# expressed as offset − accumulation).
KSHEPA = {"moon_apogee": 90.0, "rahu": 180.0}

# Manda paridhis (epicycle circumference in degrees, EVEN-sign values).
MANDA_PARIDHI = {
    "sun": 14.0, "moon": 32.0, "mars": 75.0, "mercury": 30.0,
    "jupiter": 33.0, "venus": 12.0, "saturn": 49.0,
}

# Shighra paridhis (even-sign values) for the five star-planets.
SHIGHRA_PARIDHI = {
    "mars": 235.0, "mercury": 133.0, "jupiter": 70.0,
    "venus": 262.0, "saturn": 39.0,
}

# Fixed mandocca (apogee) longitudes per the SS, degrees. The MOON's mandocca
# is not here — it moves (use REVOLUTIONS["moon_apogee"]).
MANDOCCA = {
    "sun": 77.2833,      # 77°17'
    "mars": 130.0,
    "mercury": 220.45,   # 220°13' (of Mercury's own orbit)
    "jupiter": 171.3,    # 171°18'
    "venus": 79.83,      # 79°50'
    "saturn": 236.6,     # 236°37'
}


def _wrap180(deg: float) -> float:
    """Wrap an angle difference into (-180, 180]."""
    return (deg + 180.0) % 360.0 - 180.0


# ── Mean and true positions ──────────────────────────────────────────────────

def mean_longitude_ss(body: str, ahargana: float) -> float:
    """Surya Siddhanta MEAN longitude (degrees) from the Kali ahargana.

    (revolutions × ahargana / 1,577,917,828) × 360, mod 360. Epoch
    convention: at ahargana 0 every mean PLANET is at 0° (see module note);
    the moon's apogee starts at 90° and Rahu at 180° (KSHEPA). Rahu is
    RETROGRADE: its accumulation is negated (offset − forward motion), so
    its mean longitude DECREASES with time.
    """
    revs = REVOLUTIONS[body]
    lon = (revs * ahargana / CIVIL_DAYS_PER_MAHAYUGA * 360.0) % 360.0
    if body == "rahu":
        return (KSHEPA["rahu"] - lon) % 360.0
    return (lon + KSHEPA.get(body, 0.0)) % 360.0


def manda_equation(body: str, kendra_deg: float) -> float:
    """Signed manda (equation of centre) in degrees for the given kendra.

    kendra = mandocca − mean longitude. sin(eq) = (paridhi/360) × sin(kendra);
    the sine's sign supplies the classical add/subtract by hemisphere
    (positive for kendra in (0°, 180°), negative in (180°, 360°), zero at
    0°/180°, extremal near 90°/270°).
    """
    r = MANDA_PARIDHI[body] / 360.0
    return math.degrees(math.asin(r * math.sin(math.radians(kendra_deg))))


def shighra_equation(body: str, kendra_deg: float) -> float:
    """Signed shighra correction in degrees for the given shighra kendra.

    kendra = sighrocca − manda-corrected longitude. The standard epicyclic
    conversion eq = atan2(r·sin k, 1 + r·cos k), r = shighra-paridhi/360:
    the angle at the earth subtended by the epicycle offset (the SS
    hypotenuse/karna formulation). Zero at kendra 0°/180°.
    """
    r = SHIGHRA_PARIDHI[body] / 360.0
    k = math.radians(kendra_deg)
    return math.degrees(math.atan2(r * math.sin(k), 1.0 + r * math.cos(k)))


def _true_sun(ahargana: float) -> float:
    mean = mean_longitude_ss("sun", ahargana)
    return (mean + manda_equation("sun", MANDOCCA["sun"] - mean)) % 360.0


def true_moon_ss(ahargana: float) -> float:
    """SS true moon: mean moon + manda with the MOVING mandocca."""
    mean = mean_longitude_ss("moon", ahargana)
    ucca = mean_longitude_ss("moon_apogee", ahargana)
    return (mean + manda_equation("moon", ucca - mean)) % 360.0


def true_positions_ss(ahargana: float) -> dict[str, float]:
    """SS true longitudes for all 9 grahas at the given Kali ahargana.

    Sequence per body (see module note for the simplifications):
      sun/moon — mean + manda;
      mars/jupiter/saturn — mean + manda, then shighra with the sun's mean
        longitude as sighrocca;
      mercury/venus — mean planet = sun's mean, + own manda, then shighra
        with their own sighrocca;
      rahu — retrograde mean node; ketu = rahu + 180°.
    """
    sun_mean = mean_longitude_ss("sun", ahargana)
    out: dict[str, float] = {
        "sun": _true_sun(ahargana),
        "moon": true_moon_ss(ahargana),
    }
    for body in ("mars", "jupiter", "saturn"):
        mean = mean_longitude_ss(body, ahargana)
        manda_corr = (mean + manda_equation(body, MANDOCCA[body] - mean)) % 360.0
        out[body] = (manda_corr
                     + shighra_equation(body, sun_mean - manda_corr)) % 360.0
    for body in ("mercury", "venus"):
        manda_corr = (sun_mean
                      + manda_equation(body, MANDOCCA[body] - sun_mean)) % 360.0
        sighrocca = mean_longitude_ss(f"{body}_sighra", ahargana)
        out[body] = (manda_corr
                     + shighra_equation(body, sighrocca - manda_corr)) % 360.0
    rahu = mean_longitude_ss("rahu", ahargana)
    out["rahu"] = rahu
    out["ketu"] = (rahu + 180.0) % 360.0
    return out


# ── Vakya moon ───────────────────────────────────────────────────────────────

# 248 civil days ≈ 9 anomalistic months — the Vararuchi cycle.
VAKYA_CYCLE_DAYS = 248

# Vakya epoch anchor: Kali ahargana of 2000-01-01 00:00 UT.
# JD 2451544.5 − KALI_EPOCH_JD 588465.5 = 1,863,079 (exact fixed constant,
# no ephemeris needed).
VAKYA_ANCHOR_AHARGANA = 1_863_079.0

# Dhruva (epoch offset): ZERO BY CONSTRUCTION — vakya_moon is built from our
# own SS true moon at the anchored cycle phase, so at the 2000-01-01 anchor
# vakya_moon == true_moon_ss exactly and no residual constant is needed.
# (The classical tables need a dhruva because their 248 increments are frozen
# sentences; our computational equivalent regenerates them from the SS moon.)
VAKYA_DHRUVA = 0.0

_cycle_shift_cache: float | None = None


def vakya_cycle_shift() -> float:
    """Per-cycle longitude shift, computed ONCE from the SS moon itself.

    The vakya premise: the moon's true-longitude pattern repeats every 248
    days shifted by a near-constant (~27.7° — one sidereal-month remainder).
    We average (true_moon(a+248) − true_moon(a)) over samples spread across
    one cycle at the anchor, wrapping each difference, to smooth the small
    anomalistic residue (248 d is ~0.009 d short of 9 anomalistic months).
    Documented as the computational equivalent of the sentence tables.
    """
    global _cycle_shift_cache
    if _cycle_shift_cache is None:
        samples = 8
        step = VAKYA_CYCLE_DAYS / samples
        total = 0.0
        for i in range(samples):
            a = VAKYA_ANCHOR_AHARGANA + i * step
            total += _wrap180(true_moon_ss(a + VAKYA_CYCLE_DAYS)
                              - true_moon_ss(a))
        _cycle_shift_cache = total / samples
    return _cycle_shift_cache


def vakya_moon(ahargana: float) -> float:
    """Vakya-method moon longitude (degrees) — computational vakya.

    days_in_cycle = (ahargana − anchor) mod 248; the longitude is the SS
    true moon at the SAME cycle phase of the ANCHOR cycle, advanced by
    whole-cycle shifts (``vakya_cycle_shift``) plus the dhruva (zero here —
    see VAKYA_DHRUVA). Approximation error is the slow anomalistic-phase
    drift of the 248-day cycle — well inside the tested 3° band near the
    calibration epoch.
    """
    days = ahargana - VAKYA_ANCHOR_AHARGANA
    n_cycles = math.floor(days / VAKYA_CYCLE_DAYS)
    days_into_cycle = days - n_cycles * VAKYA_CYCLE_DAYS
    base = true_moon_ss(VAKYA_ANCHOR_AHARGANA + days_into_cycle)
    return (base + n_cycles * vakya_cycle_shift() + VAKYA_DHRUVA) % 360.0


# ── Comparison + siddhantic panchanga ────────────────────────────────────────

def compare_with_drik(jd_ut: float, ayanamsa: str = "lahiri") -> dict:
    """Side-by-side SS vs drik (Swiss Ephemeris) sidereal longitudes.

    The user-facing transparency view: per body the siddhanta longitude, the
    drik longitude, and delta_deg wrapped to (-180, 180]. DRIK REMAINS THE
    DEFAULT everywhere in the app — this comparison is informational.
    Note the frames differ slightly by design: SS longitudes live in the SS
    epoch frame, drik in the chosen ayanamsa; the residual zero-point offset
    is part of the traditional-vs-modern deviation being displayed.
    """
    from .ephemeris import sidereal_positions  # comparison helper only

    ahargana = kali_ahargana(jd_ut)
    ss = true_positions_ss(ahargana)
    drik = sidereal_positions(jd_ut, ayanamsa=ayanamsa)
    bodies = {}
    for body, ss_lon in ss.items():
        drik_lon = drik[body]["lon"]
        bodies[body] = {
            "siddhanta": ss_lon,
            "drik": drik_lon,
            "delta_deg": _wrap180(ss_lon - drik_lon),
        }
    return {
        "_mode": "surya_siddhanta_vs_drik",
        "ayanamsa": ayanamsa,
        "ahargana": ahargana,
        "vakya_moon": vakya_moon(ahargana),
        "bodies": bodies,
        "note": ("Comparison mode: drik (Swiss Ephemeris) is the default "
                 "engine; siddhanta values shown for traditional parity."),
    }


def panchanga_siddhantic(ahargana: float, moon_method: str = "siddhanta") -> dict:
    """Traditional-parity panchanga limbs from the SS sun/moon.

    Formulas mirror panchanga.py locally (elongation/12° tithi, 6° karana,
    sum/13°20' yoga, moon/13°20' nakshatra) but feed on SS positions so a
    siddhantic panchanga can be shown against the drik one. moon_method:
    "siddhanta" (SS true moon, default) or "vakya" (the 248-day cycle moon).
    """
    if moon_method not in ("siddhanta", "vakya"):
        raise ValueError(f"unknown moon_method: {moon_method!r}")
    sun = _true_sun(ahargana)
    moon = vakya_moon(ahargana) if moon_method == "vakya" else true_moon_ss(ahargana)
    elong = (moon - sun) % 360.0
    tithi_idx = min(29, int(elong // 12.0))
    yoga_idx = min(26, int(((sun + moon) % 360.0) // (360.0 / 27.0)))
    karana_idx = min(59, int(elong // 6.0))
    nak_idx = min(26, int(moon // (360.0 / 27.0)))
    return {
        "_mode": "surya_siddhanta",
        "moon_method": moon_method,
        "sun": sun,
        "moon": moon,
        "tithi": {"index": tithi_idx + 1, "name": TITHIS[tithi_idx],
                  "paksha": "shukla" if tithi_idx < 15 else "krishna"},
        "nakshatra": {"index": nak_idx, "name": NAKSHATRAS[nak_idx]},
        "yoga": {"index": yoga_idx + 1, "name": YOGAS_27[yoga_idx]},
        "karana": {"index": karana_idx + 1, "name": karana_name(karana_idx)},
        "note": ("Traditional (Surya Siddhanta) parity values — the app's "
                 "default panchanga is drik."),
    }

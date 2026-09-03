"""Shadbala — the six-fold graha strength per BPHS. Units: virupas (60 = 1 rupa).

Computed for the 7 classical grahas (rahu/ketu excluded, as in BPHS).
Everything here is pure arithmetic over precomputed sidereal longitudes/speeds
passed in via ShadbalaInputs — no ephemeris import.

Conventions & documented simplifications
========================================
STHANA (positional) = uccha + saptavargaja + ojayugma + kendradi + drekkana.
  * Uccha bala: angular distance from the deep-debilitation point / 3 → 0..60.
  * Saptavargaja: dignity in D1, D2, D3, D7, D9, D12, D30. Points:
    moolatrikona 45 (D1 only — MT is degree-defined, so it exists only in the
    rasi chart; varga positions cap at "own"), own 30, adhimitra (great
    friend) 20, mitra 15, sama 10, satru 4, adhisatru 2. (Some texts use
    22.5/3.75/1.875 for the friend rungs; we use the whole-number 20/15/10/4/2
    scale.) Friendship uses the COMPOUND relation — natural + temporal, with
    temporal relation always evaluated from the D1 (rasi) chart positions.
  * Ojayugma: Sun/Mars/Jupiter/Mercury/Saturn score 15 in an odd rasi and 15
    in an odd navamsa; Moon/Venus score in even rasi/navamsa.
  * Kendradi: whole-sign house from lagna — kendra 60, panaphara 30,
    apoklima 15.
  * Drekkana: male grahas (Sun/Mars/Jupiter) 15 in the 1st drekkana of their
    sign, female (Moon/Venus) in the 2nd, neutral (Mercury/Saturn) in the 3rd.

DIG (directional): power houses — Jupiter/Mercury 1st, Sun/Mars 10th,
  Saturn 7th, Moon/Venus 4th. Bhava cusps are approximated as whole-sign
  offsets from the lagna DEGREE (power point = lagna_lon + (house-1)*30);
  dig bala = angular distance from the point OPPOSITE the power point / 3
  → 0..60. (Full BPHS uses the bhava madhya from Sripati houses; the
  whole-sign-cusp approximation is documented and standard for this engine.)

KALA (temporal) = nathonnatha + paksha + tribhaga + vara + hora + ayana
  (+ yuddha adjustment).
  * Nathonnatha: local apparent midnight is approximated as apparent midday
    ((sunrise+sunset)/2) minus half a day. unnata = fraction of the half-day
    elapsed from midnight (0 at midnight → 1 at noon). Diurnal grahas
    (Sun/Jupiter/Venus) get 60*unnata; nocturnal (Moon/Mars/Saturn) get
    60*(1-unnata); Mercury always 60.
  * Paksha: shukla fraction = Moon-Sun elongation scaled to 0..1 over the
    waxing half. Benefics (Jupiter, Venus, Mercury — treated statically as
    benefic — and the waxing Moon) get fraction*60; malefics 60 minus that.
    The Moon's paksha bala is DOUBLED per BPHS (may exceed 60).
  * Tribhaga: day (sunrise→sunset) thirds are lorded by Mercury, Sun, Saturn;
    night thirds by Moon, Venus, Mars. The lord of the birth third gets 60.
    Jupiter ALWAYS gets 60. For a night birth before sunrise the night is
    taken to have begun at the previous sunset (sunset_jd - 1 day); night
    length is approximated with a next/previous sunrise one civil day away.
  * Vara: 45 to the weekday lord (weekday is Python convention, 0=Monday).
  * Hora: 60 to the lord of the birth hora. Horas are EQUAL 24th-parts of the
    day counted from sunrise (the unequal day/night-hour refinement is
    omitted); the first hora belongs to the weekday lord and successive lords
    follow the hora order Sun, Venus, Mercury, Moon, Saturn, Jupiter, Mars.
  * Abda (year-lord 15) and masa (month-lord 30) balas are computed from the
    Kali ahargana when ShadbalaInputs.full_bphs=True (default False keeps the
    legacy totals byte-identical for the pinned golden charts):
      ahargana = jd_ut − 588465.5 (the Kali epoch, Feb 18 3102 BCE 00:00 UT).
      WEEKDAY ANCHOR (calibrated): floor(jd + 1.5) mod 7 → 0=Sunday..6=Saturday
      (checked: JD 2460310.5 = 2024-01-01, a Monday, → 1). The Kali epoch day
      maps to 5 = FRIDAY, matching tradition, i.e. Python weekday 4 — so Kali
      day N has Python weekday (4 + N) mod 7.
      Abda: the year is 360 civil days; year_start = A − (A mod 360) with
      A = floor(ahargana); the abda lord is the vara lord of that day (15
      virupas). Masa: same with 30-day months (30 virupas).
  * Ayana: declination proxy = 23.45 * sin(sayana longitude), where
    sayana = sidereal + ayanamsa. North-strong grahas (Sun/Mars/Jupiter/
    Venus): 60*(23.45+decl)/46.9; south-strong (Moon/Saturn): the complement;
    Mercury is strong both ways: 60*(23.45+|decl|)/46.9. The Sun's ayana bala
    is doubled per BPHS (may exceed 60). This ignores celestial latitude
    (an accepted approximation).
  * Graha yuddha: only between the five taras (Mars..Saturn) within 1° of
    each other. SIMPLIFICATION: the faster-moving graha wins (BPHS uses the
    more northern one); the winner gains and the loser loses
    (1 - separation) * 30 virupas.

CHESTA (motional): Sun = its ayana bala (the doubled value); Moon = its
  paksha bala (the doubled value) — both per BPHS, in both modes.
  For Mars..Saturn, TWO implementations:
  * full_bphs=True → TRUE chesta from mean elements (the widely used rule, as
    in Maitreya/JHora-style open implementations): chesta_kendra =
    seeghroccha − madhya, reduced to 0..360, and if > 180 use 360 − k;
    chesta bala = k / 3 shashtiamsas (0..60). For the OUTER planets
    (Mars/Jupiter/Saturn) the seeghroccha is the MEAN SUN and madhya is the
    planet's mean longitude; for MERCURY/VENUS the seeghroccha is the planet's
    OWN mean heliocentric longitude and madhya is the mean Sun. Either way the
    reduced kendra equals reduce(|mean_planet − mean_sun|), so retrograde
    motion (opposition for outer planets, inferior conjunction for inner)
    scores near 60. Mean longitudes are standard mean-element polynomials
    referenced to J2000 (Meeus, "Astronomical Algorithms" 2nd ed., Table 31.a
    for the planets, eq. 25.2 for the Sun; mean equinox of date,
    T = (jd − 2451545.0)/36525). The kendra is a LONGITUDE DIFFERENCE, so the
    ayanamsa cancels — tropical mean elements may be differenced directly
    against each other (mean_longitude() still accepts an ayanamsa for a
    sidereal reading).
  * full_bphs=False (default) → the legacy speed-proxy (kept so pinned golden
    totals stay byte-identical): chesta = 30 + 30*(mean_speed − actual_speed)
    / mean_speed, clamped 0..60. Mean speeds (deg/day): Mars 0.524,
    Mercury 1.383, Jupiter 0.083, Venus 1.2, Saturn 0.033 (Sun 0.9856,
    Moon 13.176 are used only for motion-state naming).

MOTION STATES (avasthas of motion, informational, always returned): the 8
  classical names are assigned from the ratio r = actual_speed / mean_speed
  (engine-documented thresholds; the classical texts name the states without
  numeric bounds, so the bands below are this engine's convention):
    r <= −0.5        → vakra       (full retrograde)
    −0.5 < r < −0.05 → anuvakra    (slow/entering retrograde)
    |r| <= 0.05      → vikala      (stationary)
    0.05 < r < 0.5   → mandatara   (very slow direct)
    0.5 <= r < 0.9   → manda       (slow)
    0.9 <= r <= 1.1  → sama        (near mean motion)
    1.1 < r < 1.5    → chara       (fast)
    r >= 1.5         → atichara    (very fast)

VIMSHOPAKA (shadvarga, informational, always returned): D1,D2,D3,D9,D12,D30
  weighted 6,2,4,5,2,1 (total 20). Dignity factor per varga:
  exalted/moolatrikona/own → 1.0; great_friend/friend → 3/4; neutral → 1/2;
  enemy → 1/4; great_enemy/debilitated → 0. MT only exists in D1 (degree
  band); friendship is the COMPOUND relation with temporal evaluated from D1
  positions (same convention as saptavargaja). Score is 0..20 per graha.

BHAVA BALA (bhava_bala(), separate function): per-house total of
  * bhavadhipati bala — the house lord's shadbala total (virupas); lord of
    the sign holding the bhava madhya.
  * bhava dig bala — the Maitreya-style rasi-type rule: the bhava madhya's
    RASI class picks the strong house — nara rashis (Gemini, Virgo, Libra,
    Aquarius, 1st half Sagittarius) strong in the 1st; jalachara (Cancer,
    Pisces, 2nd half Capricorn) in the 4th; chatushpada (Aries, Taurus, Leo,
    2nd half Sagittarius, 1st half Capricorn) in the 10th; keeta (Scorpio)
    in the 7th. bala = 60 − (angular distance from the strong bhava's
    madhya)/3, floored at 0.
  * bhava drishti bala — sum over the 7 grahas of sphuta drishti onto the
    bhava madhya (special sign aspects of Mars/Jupiter/Saturn uplifted to 60,
    same convention as graha drik), benefics positive, malefics negative, /4.

NAISARGIKA (natural, fixed): Sun 60, Moon 51.43, Venus 42.85, Jupiter 34.28,
  Mercury 25.7, Mars 17.14, Saturn 8.57.

DRIK (aspectual): sphuta drishti of each other graha on this one, from the
  separation D = (lon_aspected - lon_aspecting) mod 360, canonical piecewise:
    D <  30 : 0
    30-60  : (D-30)/2
    60-90  : (D-60)+15
    90-120 : 30 + (120-D)/2
    120-150: 150-D
    150-180: (D-150)*2          (opposition = 60)
    180-300: (300-D)/2          (tapers back to 0)
    >= 300 : 0
  SPECIAL aspects — Mars on the 4th/8th sign, Jupiter on the 5th/9th,
  Saturn on the 3rd/10th — are treated as FULL 60 (documented choice; some
  texts uplift to 45). Benefic aspects (Jupiter, Venus, Mercury — static —
  and the waxing Moon) add, malefic subtract:
  drik bala = (benefic drishti sum − malefic drishti sum) / 4. May be negative.

Required strength (rupas, BPHS): Sun 6.5, Moon 6.0, Mars 5.0, Mercury 7.0,
Jupiter 6.5, Venus 5.5, Saturn 5.0. is_strong = total_rupas >= required.

Also exported:
  * ishta_kashta(uccha, chesta) — ishta = sqrt(uccha*chesta),
    kashta = sqrt((60-uccha)*(60-chesta)); inputs clamped to 0..60.
  * bhava_bala_simple(sav, bhava_signs) — the SAV-bindu view of house
    strength (NOT the full BPHS bhava bala).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .constants import EXALTATION, MOOLATRIKONA, SIGN_LORD, VARA_LORDS
from .dignity import compound_relation
from .varga import d1, d2, d3, d7, d9, d12, d30

SHADBALA_GRAHAS = ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn")

NAISARGIKA_BALA = {
    "sun": 60.0, "moon": 51.43, "venus": 42.85, "jupiter": 34.28,
    "mercury": 25.7, "mars": 17.14, "saturn": 8.57,
}

REQUIRED_RUPAS = {
    "sun": 6.5, "moon": 6.0, "mars": 5.0, "mercury": 7.0,
    "jupiter": 6.5, "venus": 5.5, "saturn": 5.0,
}

DIG_POWER_HOUSE = {
    "jupiter": 1, "mercury": 1, "sun": 10, "mars": 10,
    "saturn": 7, "moon": 4, "venus": 4,
}

# Saptavargaja dignity points (see module docstring for the chosen scale).
_SAPTAVARGA_POINTS = {
    "moolatrikona": 45.0, "own": 30.0, "great_friend": 20.0, "friend": 15.0,
    "neutral": 10.0, "enemy": 4.0, "great_enemy": 2.0,
}
_SAPTAVARGA_FUNCS = (("D1", d1), ("D2", d2), ("D3", d3), ("D7", d7),
                     ("D9", d9), ("D12", d12), ("D30", d30))

_ODD_PARITY_GRAHAS = ("sun", "mars", "jupiter", "mercury", "saturn")

_DIURNAL = ("sun", "jupiter", "venus")
_NOCTURNAL = ("moon", "mars", "saturn")

_STATIC_BENEFICS = ("jupiter", "venus", "mercury")  # Moon added when waxing

_DAY_TRIBHAGA_LORDS = ("mercury", "sun", "saturn")
_NIGHT_TRIBHAGA_LORDS = ("moon", "venus", "mars")

HORA_ORDER = ("sun", "venus", "mercury", "moon", "saturn", "jupiter", "mars")

MEAN_SPEED = {"mars": 0.524, "mercury": 1.383, "jupiter": 0.083,
              "venus": 1.2, "saturn": 0.033,
              # sun/moon entries are used only for motion-state naming.
              "sun": 0.9856, "moon": 13.176}

# Mean-longitude polynomials, mean equinox of date (Meeus, "Astronomical
# Algorithms" 2nd ed.: Table 31.a for the planets, eq. 25.2 for the Sun).
# L = a + b*T + c*T^2 degrees, T = (jd_ut - 2451545.0) / 36525 (J2000).
_MEAN_ELEMENTS = {
    "sun":     (280.46646, 36000.76983, 0.0003032),
    "mercury": (252.250906, 149474.0722491, 0.00030350),
    "venus":   (181.979801, 58519.2130302, 0.00031014),
    "mars":    (355.433000, 19141.6964471, 0.00031052),
    "jupiter": (34.351519, 3036.3027748, 0.00022330),
    "saturn":  (50.077444, 1223.5110686, 0.00051908),
}

MOTION_STATES = ("vakra", "anuvakra", "vikala", "mandatara",
                 "manda", "sama", "chara", "atichara")

# Kali epoch: Feb 18, 3102 BCE 00:00 UT — a FRIDAY (see module docstring for
# the weekday-anchor calibration).
KALI_EPOCH_JD = 588465.5
_KALI_EPOCH_PY_WEEKDAY = 4  # Friday in Python's 0=Monday convention

# Vimshopaka: shadvarga weights (total 20) and dignity factors.
_VIMSHOPAKA_VARGAS = (("D1", d1, 6.0), ("D2", d2, 2.0), ("D3", d3, 4.0),
                      ("D9", d9, 5.0), ("D12", d12, 2.0), ("D30", d30, 1.0))
_VIMSHOPAKA_FACTOR = {
    "exalted": 1.0, "moolatrikona": 1.0, "own": 1.0,
    "great_friend": 0.75, "friend": 0.75, "neutral": 0.5,
    "enemy": 0.25, "great_enemy": 0.0, "debilitated": 0.0,
}

_TARAS = ("mars", "mercury", "jupiter", "venus", "saturn")

_MAX_OBLIQUITY = 23.45

_SPECIAL_SIGN_ASPECTS = {"mars": (4, 8), "jupiter": (5, 9), "saturn": (3, 10)}


@dataclass
class ShadbalaInputs:
    """Precomputed chart quantities needed by shadbala() — no ephemeris calls.

    positions: {graha: {"lon": sidereal deg, "speed": deg/day}} for the 9
    grahas (rahu/ketu tolerated but ignored).
    weekday: Python convention (0=Monday .. 6=Sunday) of the civil birth date.
    ayanamsa_value: degrees, to recover sayana longitudes for ayana bala.
    full_bphs: OPTIONAL (default False). When True, chesta bala for
    Mars..Saturn uses the TRUE mean-element rule and kala bala gains the
    abda (15) + masa (30) components. The default keeps the legacy numeric
    totals byte-identical (the golden-chart snapshots pin them); flipping it
    on is the full-BPHS mode. Purely additive keys (motion_state, vimshopaka)
    are returned in BOTH modes.
    """
    positions: dict[str, dict]
    lagna_lon: float
    jd_ut: float
    lat: float
    lng: float
    sunrise_jd: float
    sunset_jd: float
    is_day_birth: bool
    weekday: int
    ayanamsa_value: float
    full_bphs: bool = False


# ── small helpers ────────────────────────────────────────────────────────────

def _sign(lon: float) -> int:
    return int((lon % 360.0) // 30)


def _angular_distance(a: float, b: float) -> float:
    d = abs((a - b) % 360.0)
    return min(d, 360.0 - d)


def _is_odd_sign(sign: int) -> bool:
    return sign % 2 == 0  # Aries(0) is the 1st (odd) sign


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _moon_is_waxing(positions: dict[str, dict]) -> bool:
    """Bright-half Moon (waxing; full moon inclusive) counts as benefic."""
    elong = (positions["moon"]["lon"] - positions["sun"]["lon"]) % 360.0
    return 0.0 < elong <= 180.0


# ── sthana components ────────────────────────────────────────────────────────

def uccha_bala(graha: str, lon: float) -> float:
    """Distance from the deep-debilitation point / 3 → 0..60 virupas."""
    ex_sign, ex_deg = EXALTATION[graha]
    deep_exaltation = ex_sign * 30.0 + ex_deg
    deep_debilitation = (deep_exaltation + 180.0) % 360.0
    return _angular_distance(lon, deep_debilitation) / 3.0


def saptavargaja_bala(graha: str, lon: float, d1_signs: dict[str, int]) -> float:
    """Dignity points across D1,D2,D3,D7,D9,D12,D30 (see docstring scale)."""
    total = 0.0
    for varga_name, func in _SAPTAVARGA_FUNCS:
        vsign = func(lon)
        if varga_name == "D1":
            mt = MOOLATRIKONA.get(graha)
            deg = (lon % 360.0) % 30.0
            if mt and vsign == mt[0] and mt[1] <= deg < mt[2]:
                total += _SAPTAVARGA_POINTS["moolatrikona"]
                continue
        lord = SIGN_LORD[vsign]
        if lord == graha:
            total += _SAPTAVARGA_POINTS["own"]
            continue
        rel = compound_relation(graha, lord, d1_signs[graha], d1_signs[lord])
        total += _SAPTAVARGA_POINTS[rel]
    return total


def ojayugma_bala(graha: str, lon: float) -> float:
    """15 for the matching parity in rasi + 15 in navamsa (0/15/30)."""
    want_odd = graha in _ODD_PARITY_GRAHAS
    score = 0.0
    if _is_odd_sign(d1(lon)) == want_odd:
        score += 15.0
    if _is_odd_sign(d9(lon)) == want_odd:
        score += 15.0
    return score


def kendradi_bala(lon: float, lagna_lon: float) -> float:
    house = (_sign(lon) - _sign(lagna_lon)) % 12 + 1
    if house in (1, 4, 7, 10):
        return 60.0
    if house in (2, 5, 8, 11):
        return 30.0
    return 15.0


def drekkana_bala(graha: str, lon: float) -> float:
    part = int(((lon % 360.0) % 30.0) // 10.0)  # 0,1,2
    if graha in ("sun", "mars", "jupiter"):
        return 15.0 if part == 0 else 0.0
    if graha in ("moon", "venus"):
        return 15.0 if part == 1 else 0.0
    return 15.0 if part == 2 else 0.0  # mercury, saturn


# ── dig bala ─────────────────────────────────────────────────────────────────

def dig_bala(graha: str, lon: float, lagna_lon: float) -> float:
    """Distance from the nadir of the graha's power point / 3 → 0..60.

    Power point approximated as lagna_lon + (power_house-1)*30 (whole-sign
    cusp approximation, documented in the module docstring)."""
    power_point = (lagna_lon + (DIG_POWER_HOUSE[graha] - 1) * 30.0) % 360.0
    weakest_point = (power_point + 180.0) % 360.0
    return _angular_distance(lon, weakest_point) / 3.0


# ── kala components ──────────────────────────────────────────────────────────

def nathonnatha_bala(graha: str, jd_ut: float, sunrise_jd: float,
                     sunset_jd: float) -> float:
    midday_jd = (sunrise_jd + sunset_jd) / 2.0
    midnight_jd = midday_jd - 0.5
    t = (jd_ut - midnight_jd) % 1.0
    unnata = min(t, 1.0 - t) * 2.0  # 0 at midnight → 1 at noon
    if graha == "mercury":
        return 60.0
    if graha in _DIURNAL:
        return 60.0 * unnata
    return 60.0 * (1.0 - unnata)  # nocturnal


def paksha_bala(graha: str, positions: dict[str, dict]) -> float:
    elong = (positions["moon"]["lon"] - positions["sun"]["lon"]) % 360.0
    shukla_fraction = elong / 180.0 if elong <= 180.0 else (360.0 - elong) / 180.0
    is_benefic = graha in _STATIC_BENEFICS or (
        graha == "moon" and _moon_is_waxing(positions))
    bala = shukla_fraction * 60.0 if is_benefic else (1.0 - shukla_fraction) * 60.0
    if graha == "moon":
        bala *= 2.0  # BPHS: Moon's paksha bala is doubled
    return bala


def tribhaga_bala(graha: str, jd_ut: float, sunrise_jd: float, sunset_jd: float,
                  is_day_birth: bool) -> float:
    if graha == "jupiter":
        return 60.0
    if is_day_birth:
        span = max(sunset_jd - sunrise_jd, 1e-9)
        frac = _clamp((jd_ut - sunrise_jd) / span, 0.0, 1.0 - 1e-9)
        lords = _DAY_TRIBHAGA_LORDS
    else:
        if jd_ut >= sunset_jd:
            night_start, night_end = sunset_jd, sunrise_jd + 1.0
        else:  # pre-dawn birth: the night began at the previous sunset
            night_start, night_end = sunset_jd - 1.0, sunrise_jd
        span = max(night_end - night_start, 1e-9)
        frac = _clamp((jd_ut - night_start) / span, 0.0, 1.0 - 1e-9)
        lords = _NIGHT_TRIBHAGA_LORDS
    return 60.0 if lords[int(frac * 3.0)] == graha else 0.0


def vara_bala(graha: str, weekday: int) -> float:
    return 45.0 if VARA_LORDS[weekday % 7] == graha else 0.0


def hora_bala(graha: str, jd_ut: float, sunrise_jd: float, weekday: int) -> float:
    elapsed = (jd_ut - sunrise_jd) % 1.0
    hora_index = int(elapsed * 24.0)  # equal-hour simplification
    start = HORA_ORDER.index(VARA_LORDS[weekday % 7])
    return 60.0 if HORA_ORDER[(start + hora_index) % 7] == graha else 0.0


def ayana_bala(graha: str, lon: float, ayanamsa_value: float) -> float:
    sayana_lon = (lon + ayanamsa_value) % 360.0
    decl = _MAX_OBLIQUITY * math.sin(math.radians(sayana_lon))
    if graha == "mercury":
        bala = 60.0 * (_MAX_OBLIQUITY + abs(decl)) / (2.0 * _MAX_OBLIQUITY)
    elif graha in ("moon", "saturn"):  # south-declination strong
        bala = 60.0 * (_MAX_OBLIQUITY - decl) / (2.0 * _MAX_OBLIQUITY)
    else:  # sun, mars, jupiter, venus: north strong
        bala = 60.0 * (_MAX_OBLIQUITY + decl) / (2.0 * _MAX_OBLIQUITY)
    if graha == "sun":
        bala *= 2.0  # BPHS: Sun's ayana bala is doubled
    return bala


def yuddha_adjustments(positions: dict[str, dict]) -> dict[str, float]:
    """Graha-yuddha virupa adjustments (winner +, loser −); {} entries are 0.

    Simplification (documented): the faster graha wins; magnitude
    (1 − separation°) * 30."""
    adj = {g: 0.0 for g in SHADBALA_GRAHAS}
    for i, a in enumerate(_TARAS):
        for b in _TARAS[i + 1:]:
            sep = _angular_distance(positions[a]["lon"], positions[b]["lon"])
            if sep >= 1.0:
                continue
            amount = (1.0 - sep) * 30.0
            winner, loser = ((a, b) if positions[a]["speed"] >= positions[b]["speed"]
                             else (b, a))
            adj[winner] += amount
            adj[loser] -= amount
    return adj


def abda_masa_ahargana(jd_ut: float) -> float:
    """Kali ahargana: elapsed days since the Kali epoch (JD 588465.5)."""
    return jd_ut - KALI_EPOCH_JD


def _kali_day_lord(day_number: int) -> str:
    """Vara lord of Kali day N (day 0 = the epoch day, a Friday)."""
    return VARA_LORDS[(_KALI_EPOCH_PY_WEEKDAY + day_number) % 7]


def abda_lord(jd_ut: float) -> str:
    """Lord of the current 360-day Kali year (vara lord of its first day)."""
    a = math.floor(abda_masa_ahargana(jd_ut))
    return _kali_day_lord(a - a % 360)


def masa_lord(jd_ut: float) -> str:
    """Lord of the current 30-day Kali month (vara lord of its first day)."""
    a = math.floor(abda_masa_ahargana(jd_ut))
    return _kali_day_lord(a - a % 30)


def abda_bala(graha: str, jd_ut: float) -> float:
    return 15.0 if abda_lord(jd_ut) == graha else 0.0


def masa_bala(graha: str, jd_ut: float) -> float:
    return 30.0 if masa_lord(jd_ut) == graha else 0.0


# ── chesta ───────────────────────────────────────────────────────────────────

def mean_longitude(graha: str, jd_ut: float, ayanamsa_value: float = 0.0) -> float:
    """Mean longitude (deg) from standard mean elements (Meeus Table 31.a /
    eq. 25.2, mean equinox of date, J2000-referenced polynomials).

    Tropical by default; pass ayanamsa_value to get the sidereal reading.
    For the planets this is the mean HELIOCENTRIC longitude (which doubles as
    the classical madhya for the outer planets and as the seeghroccha for
    Mercury/Venus); "sun" gives the geometric mean Sun."""
    a, b, c = _MEAN_ELEMENTS[graha]
    t = (jd_ut - 2451545.0) / 36525.0
    return (a + b * t + c * t * t - ayanamsa_value) % 360.0


def chesta_kendra(graha: str, jd_ut: float) -> float:
    """Reduced chesta kendra (0..180 deg) for Mars..Saturn.

    Outer planets: kendra = seeghroccha(mean Sun) − madhya(mean planet);
    Mercury/Venus: kendra = seeghroccha(own mean helio) − madhya(mean Sun).
    Reduced to 0..360, and 360−k when k>180 — both orderings collapse to
    reduce(|mean_planet − mean_sun|). The ayanamsa cancels in the difference,
    so tropical mean elements are differenced directly."""
    k = (mean_longitude(graha, jd_ut) - mean_longitude("sun", jd_ut)) % 360.0
    return 360.0 - k if k > 180.0 else k


def motion_state(graha: str, speed: float) -> str:
    """One of the 8 avasthas of motion from actual vs mean daily speed.

    Thresholds are this engine's documented convention (see module docstring);
    classically named only for the 5 taras, but sun/moon are classified too
    (they never retrograde, so they land in the direct bands)."""
    r = speed / MEAN_SPEED[graha]
    if r <= -0.5:
        return "vakra"
    if r < -0.05:
        return "anuvakra"
    if r <= 0.05:
        return "vikala"
    if r < 0.5:
        return "mandatara"
    if r < 0.9:
        return "manda"
    if r <= 1.1:
        return "sama"
    if r < 1.5:
        return "chara"
    return "atichara"


def chesta_bala(graha: str, positions: dict[str, dict],
                ayana: float, paksha: float,
                jd_ut: float | None = None) -> float:
    """Chesta bala. Sun→ayana, Moon→paksha (per BPHS) in both modes.

    For Mars..Saturn: with jd_ut given, the TRUE mean-element rule
    (chesta = reduced kendra / 3, see chesta_kendra); with jd_ut=None the
    legacy speed-proxy (kept for the pinned golden totals)."""
    if graha == "sun":
        return ayana  # BPHS: Sun's chesta = its ayana bala
    if graha == "moon":
        return paksha  # BPHS: Moon's chesta = its paksha bala
    if jd_ut is not None:
        return chesta_kendra(graha, jd_ut) / 3.0
    mean = MEAN_SPEED[graha]
    actual = positions[graha]["speed"]
    return _clamp(30.0 + 30.0 * (mean - actual) / mean, 0.0, 60.0)


# ── drik ─────────────────────────────────────────────────────────────────────

def sphuta_drishti(separation: float) -> float:
    """Canonical BPHS fractional-aspect value for D = (to − from) mod 360."""
    d = separation % 360.0
    if d < 30.0:
        return 0.0
    if d < 60.0:
        return (d - 30.0) / 2.0
    if d < 90.0:
        return (d - 60.0) + 15.0
    if d < 120.0:
        return 30.0 + (120.0 - d) / 2.0
    if d < 150.0:
        return 150.0 - d
    if d < 180.0:
        return (d - 150.0) * 2.0
    if d <= 300.0:
        return (300.0 - d) / 2.0
    return 0.0


def _drishti_on_point(point_lon: float, positions: dict[str, dict],
                      exclude: str | None = None) -> float:
    """(benefic drishti − malefic drishti) onto a longitude, / 4.

    Shared by graha drik bala (exclude = the aspected graha) and bhava
    drishti bala (exclude=None: all 7 grahas aspect the bhava madhya).
    Special sign aspects of Mars/Jupiter/Saturn are uplifted to 60."""
    moon_waxing = _moon_is_waxing(positions)
    sign_to = _sign(point_lon)
    benefic_sum = 0.0
    malefic_sum = 0.0
    for other in SHADBALA_GRAHAS:
        if other == exclude:
            continue
        lon_from = positions[other]["lon"]
        d = (point_lon - lon_from) % 360.0
        value = sphuta_drishti(d)
        sign_count = (sign_to - _sign(lon_from)) % 12 + 1
        if sign_count in _SPECIAL_SIGN_ASPECTS.get(other, ()):
            value = 60.0  # special aspects of Mars/Jupiter/Saturn → full
        is_benefic = other in _STATIC_BENEFICS or (other == "moon" and moon_waxing)
        if is_benefic:
            benefic_sum += value
        else:
            malefic_sum += value
    return (benefic_sum - malefic_sum) / 4.0


def drik_bala(graha: str, positions: dict[str, dict]) -> float:
    """(benefic drishti sum − malefic drishti sum) / 4; may be negative."""
    return _drishti_on_point(positions[graha]["lon"], positions, exclude=graha)


# ── vimshopaka ───────────────────────────────────────────────────────────────

def vimshopaka_bala(graha: str, lon: float, d1_signs: dict[str, int]) -> float:
    """Shadvarga vimshopaka, 0..20 (weights 6,2,4,5,2,1 over D1,D2,D3,D9,
    D12,D30; dignity factors per the module docstring)."""
    ex_sign, _ = EXALTATION[graha]
    deb_sign = (ex_sign + 6) % 12
    total = 0.0
    for varga_name, func, weight in _VIMSHOPAKA_VARGAS:
        vsign = func(lon)
        if varga_name == "D1":
            mt = MOOLATRIKONA.get(graha)
            deg = (lon % 360.0) % 30.0
            if mt and vsign == mt[0] and mt[1] <= deg < mt[2]:
                total += weight  # moolatrikona (degree-defined, D1 only)
                continue
        if vsign == ex_sign:
            total += weight
            continue
        if vsign == deb_sign:
            continue  # factor 0
        lord = SIGN_LORD[vsign]
        if lord == graha:
            total += weight
            continue
        rel = compound_relation(graha, lord, d1_signs[graha], d1_signs[lord])
        total += weight * _VIMSHOPAKA_FACTOR[rel]
    return total


# ── assembly ─────────────────────────────────────────────────────────────────

def shadbala(chart_inputs: ShadbalaInputs) -> dict[str, dict]:
    """Full shadbala for the 7 classical grahas. See module docstring."""
    ci = chart_inputs
    pos = ci.positions
    d1_signs = {g: _sign(pos[g]["lon"]) for g in SHADBALA_GRAHAS}
    yuddha = yuddha_adjustments(pos)

    out: dict[str, dict] = {}
    for g in SHADBALA_GRAHAS:
        lon = pos[g]["lon"]

        sthana = {
            "uccha": uccha_bala(g, lon),
            "saptavargaja": saptavargaja_bala(g, lon, d1_signs),
            "ojayugma": ojayugma_bala(g, lon),
            "kendradi": kendradi_bala(lon, ci.lagna_lon),
            "drekkana": drekkana_bala(g, lon),
        }
        sthana["total"] = sum(sthana.values())

        dig = dig_bala(g, lon, ci.lagna_lon)

        paksha = paksha_bala(g, pos)
        ayana = ayana_bala(g, lon, ci.ayanamsa_value)
        kala = {
            "nathonnatha": nathonnatha_bala(g, ci.jd_ut, ci.sunrise_jd, ci.sunset_jd),
            "paksha": paksha,
            "tribhaga": tribhaga_bala(g, ci.jd_ut, ci.sunrise_jd, ci.sunset_jd,
                                      ci.is_day_birth),
            "vara": vara_bala(g, ci.weekday),
            "hora": hora_bala(g, ci.jd_ut, ci.sunrise_jd, ci.weekday),
            "ayana": ayana,
            "yuddha": yuddha[g],
        }
        if ci.full_bphs:
            kala["abda"] = abda_bala(g, ci.jd_ut)
            kala["masa"] = masa_bala(g, ci.jd_ut)
        kala["total"] = sum(kala.values())

        chesta = chesta_bala(g, pos, ayana, paksha,
                             jd_ut=ci.jd_ut if ci.full_bphs else None)
        naisargika = NAISARGIKA_BALA[g]
        drik = drik_bala(g, pos)

        total_virupas = sthana["total"] + dig + kala["total"] + chesta + naisargika + drik
        total_rupas = total_virupas / 60.0
        required = REQUIRED_RUPAS[g]

        out[g] = {
            "sthana": {k: round(v, 2) for k, v in sthana.items()},
            "dig": round(dig, 2),
            "kala": {k: round(v, 2) for k, v in kala.items()},
            "chesta": round(chesta, 2),
            "naisargika": round(naisargika, 2),
            "drik": round(drik, 2),
            "total_virupas": round(total_virupas, 2),
            "total_rupas": round(total_rupas, 3),
            "required_rupas": required,
            "ratio": round(total_rupas / required, 3),
            "is_strong": total_rupas >= required,
            # Purely additive keys (returned in both modes):
            "motion_state": motion_state(g, pos[g]["speed"]),
            "vimshopaka": round(vimshopaka_bala(g, lon, d1_signs), 2),
        }
    return out


# ── bhava bala ───────────────────────────────────────────────────────────────

def _bhava_strong_house(madhya: float) -> int:
    """Strong house (1/4/7/10) for a bhava madhya by its rasi's creature class
    (nara→1, jalachara→4, keeta→7, chatushpada→10); see module docstring."""
    s = _sign(madhya)
    first_half = ((madhya % 360.0) % 30.0) < 15.0
    if s in (2, 5, 6, 10) or (s == 8 and first_half):
        return 1   # nara (incl. 1st half Sagittarius)
    if s in (3, 11) or (s == 9 and not first_half):
        return 4   # jalachara (incl. 2nd half Capricorn)
    if s == 7:
        return 7   # keeta (Scorpio)
    return 10      # chatushpada (Aries, Taurus, Leo, 2nd half Sag, 1st half Cap)


def bhava_dig_bala(madhya: float, cusps: list[float]) -> float:
    """60 − (angular distance from the strong bhava's madhya)/3, floored at 0."""
    strong = _bhava_strong_house(madhya)
    return max(0.0, 60.0 - _angular_distance(madhya, cusps[strong - 1]) / 3.0)


def bhava_drishti_bala(madhya: float, positions: dict[str, dict]) -> float:
    """Sphuta drishti of all 7 grahas onto the bhava madhya (benefic +,
    malefic −, /4); may be negative."""
    return _drishti_on_point(madhya, positions)


def bhava_bala(shadbala_result: dict[str, dict], cusps: list[float],
               positions: dict[str, dict]) -> dict[int, dict]:
    """Full BPHS-style bhava bala for houses 1..12.

    shadbala_result: the dict returned by shadbala() (bhavadhipati bala reads
    each house lord's "total_virupas").
    cusps: 12 bhava madhya longitudes, index 0 = house 1 (whole-sign callers
    may pass sign starts; the components are evaluated at whatever point is
    given).
    positions: the same {graha: {"lon", "speed"}} mapping shadbala() takes.

    Returns {house: {"bhavadhipati", "bhava_dig", "bhava_drishti", "total"}}.
    """
    out: dict[int, dict] = {}
    for house in range(1, 13):
        madhya = cusps[house - 1] % 360.0
        lord = SIGN_LORD[_sign(madhya)]
        adhipati = float(shadbala_result[lord]["total_virupas"])
        dig = bhava_dig_bala(madhya, cusps)
        drishti = bhava_drishti_bala(madhya, positions)
        out[house] = {
            "lord": lord,
            "bhavadhipati": round(adhipati, 2),
            "bhava_dig": round(dig, 2),
            "bhava_drishti": round(drishti, 2),
            "total": round(adhipati + dig + drishti, 2),
        }
    return out


def ishta_kashta(uccha_bala_v: float, chesta_bala_v: float) -> tuple[float, float]:
    """Ishta/Kashta phala from uccha & chesta balas (inputs clamped to 0..60).

    ishta = sqrt(uccha*chesta); kashta = sqrt((60-uccha)*(60-chesta))."""
    u = _clamp(uccha_bala_v, 0.0, 60.0)
    c = _clamp(chesta_bala_v, 0.0, 60.0)
    ishta = math.sqrt(u * c)
    kashta = math.sqrt((60.0 - u) * (60.0 - c))
    return round(ishta, 2), round(kashta, 2)


def bhava_bala_simple(sav: list[int], bhava_signs: list[int]) -> list[int]:
    """SAV-based house strength: each house's bindus from its occupying sign.

    This is the Sarvashtakavarga VIEW of bhava strength, NOT the full BPHS
    bhava bala (which adds bhavadhipati/dig/drishti components)."""
    return [sav[s % 12] for s in bhava_signs]

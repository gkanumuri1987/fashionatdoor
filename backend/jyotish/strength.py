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
  * Abda (year-lord ~15) and masa (month-lord ~30) balas are OMITTED — they
    need epoch year tables and are rarely decisive; documented omission.
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
  paksha bala (the doubled value) — both per BPHS. For Mars..Saturn a
  simplified continuous form of the 8-avastha classification is used:
  chesta = 30 + 30*(mean_speed - actual_speed)/mean_speed, clamped to 0..60,
  so retrograde motion (negative speed) saturates at 60 (vakra) and fast
  direct motion (atichara) approaches 0..15. Mean speeds (deg/day):
  Mars 0.524, Mercury 1.383, Jupiter 0.083, Venus 1.2, Saturn 0.033.

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
              "venus": 1.2, "saturn": 0.033}

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


# ── chesta ───────────────────────────────────────────────────────────────────

def chesta_bala(graha: str, positions: dict[str, dict],
                ayana: float, paksha: float) -> float:
    if graha == "sun":
        return ayana  # BPHS: Sun's chesta = its ayana bala
    if graha == "moon":
        return paksha  # BPHS: Moon's chesta = its paksha bala
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


def drik_bala(graha: str, positions: dict[str, dict]) -> float:
    """(benefic drishti sum − malefic drishti sum) / 4; may be negative."""
    moon_waxing = _moon_is_waxing(positions)
    lon_to = positions[graha]["lon"]
    sign_to = _sign(lon_to)
    benefic_sum = 0.0
    malefic_sum = 0.0
    for other in SHADBALA_GRAHAS:
        if other == graha:
            continue
        lon_from = positions[other]["lon"]
        d = (lon_to - lon_from) % 360.0
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
        kala["total"] = sum(kala.values())

        chesta = chesta_bala(g, pos, ayana, paksha)
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

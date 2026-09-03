"""Krishnamurti Paddhati (KP) — star/sub/sub-sub lords, horary 1-249, significators.

KP refines the 27-nakshatra wheel: every star (13°20') divides into 9 SUBS
proportional to Vimshottari years (Ketu 7 … Mercury 17, total 120 per star),
starting from the star's OWN lord and following the Vimshottari cycle. Each
sub divides again the same way into sub-subs (starting from the SUB lord).

All arithmetic is analytical (proportional spans) — no lookup tables. The
horary table is walked in EXACT integer units of 1/9° (star = 120 units,
sign = 270 units, sub width = its Vimshottari years), so the classical count
of 249 segments — 27×9 = 243 subs plus the 6 subs split by a sign boundary —
falls out exactly, with no float-equality hazards.

Significators follow the standard 4-fold KP grades per house:
  a) planets in the star of the house's occupants,
  b) the occupants themselves,
  c) planets in the star of the house lord,
  d) the house lord (sign lord of the cusp).
Rahu/Ketu own no signs, so they never appear as house lords; they DO count as
occupants and as star lords. Simplified agency rule (documented): a node also
signifies wherever a planet conjoined with it (same sign) signifies — the
node acts as that planet's agent at grades a-c (grade d stays lords-only; a
conjoined house lord lends the node its houses at grade c).
"""

from __future__ import annotations

from .constants import DASHA_ORDER, DASHA_YEARS, NAKSHATRAS, SIGN_LORD, VARA_LORDS

SPAN = 360.0 / 27.0            # one star = 13°20'
_UNITS_PER_STAR = 120          # horary walk: 1 unit = SPAN/120 = 1/9 degree
_UNITS_PER_SIGN = 270          # 30° in 1/9-degree units
_UNIT_DEG = SPAN / _UNITS_PER_STAR

_HORARY_SEGMENTS = 249         # classical KP horary count (asserted at build)


def _walk_cycle(start_index: int, offset_years: float) -> tuple[str, float, float]:
    """Locate ``offset_years`` (0..120) in the Vimshottari cycle from ``start_index``.

    Returns (lord, cumulative_years_before_lord, lord_years).
    """
    cum = 0.0
    for k in range(9):
        lord = DASHA_ORDER[(start_index + k) % 9]
        years = DASHA_YEARS[lord]
        if offset_years < cum + years or k == 8:   # k==8 guards float overshoot
            return lord, cum, float(years)
        cum += years
    raise AssertionError("unreachable")


def star_sub_subsub(lon: float) -> dict:
    """Star, sub and sub-sub lords for a sidereal longitude (analytical)."""
    lon = lon % 360.0
    star = min(26, int(lon // SPAN))
    within_years = (lon - star * SPAN) / SPAN * 120.0

    star_index_in_cycle = star % 9
    sub_lord, sub_cum, sub_years = _walk_cycle(star_index_in_cycle, within_years)
    subsub_years = (within_years - sub_cum) / sub_years * 120.0
    sub_sub_lord, _, _ = _walk_cycle(DASHA_ORDER.index(sub_lord), subsub_years)

    return {
        "star_index": star,
        "star_name": NAKSHATRAS[star],
        "star_lord": DASHA_ORDER[star_index_in_cycle],
        "sub_lord": sub_lord,
        "sub_sub_lord": sub_sub_lord,
    }


def _build_horary_segments() -> list[dict]:
    """All (star, sub) segments 0°→360°, splitting subs at sign boundaries.

    Exact integer walk: star i starts at 120*i units, each sub spans its
    Vimshottari years in units, sign boundaries sit at multiples of 270.
    """
    segments: list[dict] = []
    for star in range(27):
        base = star * _UNITS_PER_STAR
        cum = 0
        for k in range(9):
            sub_lord = DASHA_ORDER[(star % 9 + k) % 9]
            start, end = base + cum, base + cum + DASHA_YEARS[sub_lord]
            cuts = ([start]
                    + [b for b in range(_UNITS_PER_SIGN, 27 * _UNITS_PER_STAR,
                                        _UNITS_PER_SIGN) if start < b < end]
                    + [end])
            for a, b in zip(cuts, cuts[1:]):
                segments.append({
                    "number": len(segments) + 1,
                    "start_lon": a * _UNIT_DEG,
                    "end_lon": b * _UNIT_DEG,
                    "sign": a // _UNITS_PER_SIGN % 12,
                    "star_index": star,
                    "star_name": NAKSHATRAS[star],
                    "star_lord": DASHA_ORDER[star % 9],
                    "sub_lord": sub_lord,
                })
            cum += DASHA_YEARS[sub_lord]
    assert len(segments) == _HORARY_SEGMENTS, (
        f"KP horary walk produced {len(segments)} segments, expected {_HORARY_SEGMENTS}")
    return segments


_SEGMENT_CACHE: list[dict] | None = None


def horary_segments() -> list[dict]:
    """The 249 KP horary segments in zodiac order (cached)."""
    global _SEGMENT_CACHE
    if _SEGMENT_CACHE is None:
        _SEGMENT_CACHE = _build_horary_segments()
    return _SEGMENT_CACHE


def horary_number_to_lon(number: int) -> float:
    """Starting sidereal longitude of KP horary number 1-249."""
    if not 1 <= number <= _HORARY_SEGMENTS:
        raise ValueError(f"KP horary number must be 1..{_HORARY_SEGMENTS}, got {number}")
    return horary_segments()[number - 1]["start_lon"]


def cusp_sublords(cusps: list[float]) -> list[dict]:
    """Star/sub/sub-sub lords for 12 Placidus cusp longitudes."""
    if len(cusps) != 12:
        raise ValueError(f"expected 12 cusps, got {len(cusps)}")
    return [{"house": h + 1, "lon": lon % 360.0, **star_sub_subsub(lon)}
            for h, lon in enumerate(cusps)]


def _house_of(lon: float, cusps: list[float]) -> int:
    """House number (1-12) containing ``lon``; house h spans cusp[h] → cusp[h+1]."""
    lon = lon % 360.0
    for h in range(12):
        start, end = cusps[h] % 360.0, cusps[(h + 1) % 12] % 360.0
        if (lon - start) % 360.0 < (end - start) % 360.0:
            return h + 1
    return 12  # degenerate cusps; keep total function


def planet_significators(positions: dict[str, dict], cusps: list[float]) -> dict:
    """Standard 4-fold KP significators from planet longitudes + Placidus cusps.

    ``positions`` is {graha: {"lon": deg, ...}} (the ``sidereal_positions``
    shape). Houses span cusp→next-cusp, wrap-aware. Nodes are never house
    lords (they own no signs) but count as occupants/star-lords, and by the
    simplified agency rule a node is appended at every grade where a planet
    sharing its sign signifies.
    """
    if len(cusps) != 12:
        raise ValueError(f"expected 12 cusps, got {len(cusps)}")

    star_lord_of = {g: star_sub_subsub(d["lon"])["star_lord"] for g, d in positions.items()}
    occupants: dict[int, list[str]] = {h: [] for h in range(1, 13)}
    for g, d in positions.items():
        occupants[_house_of(d["lon"], cusps)].append(g)
    house_lord = {h: SIGN_LORD[int(cusps[h - 1] % 360.0 // 30)] for h in range(1, 13)}

    houses: dict[int, dict[str, list[str]]] = {}
    for h in range(1, 13):
        lord = house_lord[h]
        houses[h] = {
            "a": sorted(g for g, sl in star_lord_of.items() if sl in occupants[h]),
            "b": sorted(occupants[h]),
            "c": sorted(g for g, sl in star_lord_of.items() if sl == lord),
            "d": [lord],
        }

    # Node agency: rahu/ketu inherit the grades of planets they share a sign
    # with — at grades a-c only (grade d stays lords-only, and nodes can never
    # be lords). A conjoined planet that IS a house lord lends the node its
    # houses at grade c (agent-of-the-lord), keeping d pure.
    for node in ("rahu", "ketu"):
        if node not in positions:
            continue
        node_sign = int(positions[node]["lon"] % 360.0 // 30)
        agents = [g for g, d in positions.items()
                  if g not in ("rahu", "ketu") and int(d["lon"] % 360.0 // 30) == node_sign]
        for h, levels in houses.items():
            for grade in ("a", "b", "c"):
                names = levels[grade]
                lord_agency = grade == "c" and house_lord[h] in agents
                if node not in names and (lord_agency or any(a in names for a in agents)):
                    levels[grade] = sorted(names + [node])

    planets: dict[str, list[int]] = {}
    for h, levels in houses.items():
        for names in levels.values():
            for g in names:
                planets.setdefault(g, [])
                if h not in planets[g]:
                    planets[g].append(h)
    return {"houses": houses, "planets": {g: sorted(hs) for g, hs in sorted(planets.items())}}


def ruling_planets(weekday: int, moon_lon: float, lagna_lon: float) -> dict:
    """KP ruling planets — day lord + Moon/lagna sign, star and sub lords.

    ``weekday`` follows Python's ``date.weekday()`` (Monday=0), matching
    ``constants.VARA_LORDS``.
    """
    moon = star_sub_subsub(moon_lon)
    lagna = star_sub_subsub(lagna_lon)
    return {
        "day_lord": VARA_LORDS[weekday % 7],
        "moon_sign_lord": SIGN_LORD[int(moon_lon % 360.0 // 30)],
        "moon_star_lord": moon["star_lord"],
        "moon_sub_lord": moon["sub_lord"],
        "lagna_sign_lord": SIGN_LORD[int(lagna_lon % 360.0 // 30)],
        "lagna_star_lord": lagna["star_lord"],
        "lagna_sub_lord": lagna["sub_lord"],
    }

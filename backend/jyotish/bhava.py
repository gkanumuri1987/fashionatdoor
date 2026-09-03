"""Bhava chalita — degree-based house membership (the audit's Tier-1 #3).

Whole-sign bhavas are the rasi-chart view, but a graha at 29° of a sign may
FUNCTIONALLY belong to the next bhava. Chalita resolves that:

- Bhava MADHYA (the house's most powerful point): the cusp longitudes from the
  chosen system — Sripati (Porphyry madhya, Parashara's default) or Placidus
  (KP's requirement).
- Bhava SANDHI (the boundary): the midpoint between consecutive madhyas —
  a graha sitting on a sandhi is weak for BOTH houses (flagged).
- A graha's chalita bhava is the sandhi-to-sandhi span containing it.
"""

from __future__ import annotations

_SANDHI_ORB = 1.0  # degrees from a boundary → "in sandhi" flag


def _midpoint(a: float, b: float) -> float:
    """Circular midpoint going FORWARD from a to b."""
    span = (b - a) % 360.0
    return (a + span / 2.0) % 360.0


def bhava_chalita(cusps: list[float], positions: dict[str, dict]) -> dict:
    """cusps: 12 madhya longitudes (house 1..12). Returns spans + memberships."""
    # starts[i] = sandhi between the PREVIOUS house's madhya and house i+1's
    # madhya — i.e. the START boundary of house i+1 (0-indexed i).
    starts = [_midpoint(cusps[i - 1], cusps[i]) for i in range(12)]
    houses = []
    for i in range(12):
        houses.append({"house": i + 1, "madhya": round(cusps[i], 4),
                       "start": round(starts[i], 4),
                       "end": round(starts[(i + 1) % 12], 4)})

    def _in_span(lon: float, start: float, end: float) -> bool:
        return (lon - start) % 360.0 < (end - start) % 360.0

    membership: dict[str, dict] = {}
    for g, gd in positions.items():
        lon = gd["lon"] % 360.0
        for hspan in houses:
            if _in_span(lon, hspan["start"], hspan["end"]):
                near_start = min((lon - hspan["start"]) % 360.0,
                                 (hspan["start"] - lon) % 360.0)
                near_end = min((lon - hspan["end"]) % 360.0,
                               (hspan["end"] - lon) % 360.0)
                membership[g] = {
                    "house": hspan["house"],
                    "in_sandhi": min(near_start, near_end) <= _SANDHI_ORB,
                }
                break
    return {"houses": houses, "grahas": membership}

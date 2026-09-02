#!/usr/bin/env python3
"""Print a full chart for eyeball cross-verification against Jagannatha Hora.

Usage:
    .venv/bin/python scripts/verify_chart.py 1990-05-15 10:30 17.385 78.4867 [Asia/Kolkata]
"""

import json
import sys
from datetime import date, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from jyotish.chart import compute_chart  # noqa: E402


def main() -> None:
    if len(sys.argv) < 5:
        print(__doc__)
        sys.exit(1)
    d = date.fromisoformat(sys.argv[1])
    t = time.fromisoformat(sys.argv[2])
    lat, lng = float(sys.argv[3]), float(sys.argv[4])
    tz = sys.argv[5] if len(sys.argv) > 5 else None

    chart = compute_chart(d, t, lat=lat, lng=lng, tz_name=tz)

    print(f"Engine {chart['engine_version']}  ayanamsa={chart['input']['ayanamsa']} "
          f"({chart['ayanamsa_value']:.4f}°)  UTC={chart['input']['utc']}")
    lg = chart["lagna"]
    print(f"\nLagna: {lg['sign_name']} {lg['degree_in_sign']}  "
          f"nakshatra {lg['nakshatra']['name']} pada {lg['nakshatra']['pada']}")
    print(f"\n{'Graha':<10}{'Sign':<13}{'Degree':<12}{'House':<7}{'Nakshatra':<20}{'Dignity':<14}R  C")
    for g, gd in chart["grahas"].items():
        print(f"{g:<10}{gd['sign_name']:<13}{gd['degree_in_sign']:<12}{gd['house']:<7}"
              f"{gd['nakshatra']['name']:<20}{gd['dignity']:<14}"
              f"{'R' if gd['retrograde'] else ' '}  {'C' if gd['combust'] else ' '}")

    print(f"\nPanchanga: {json.dumps(chart['panchanga']['tithi'])} "
          f"{chart['panchanga']['yoga']['name']} / {chart['panchanga']['karana']['name']}")

    print("\nVimshottari (maha):")
    for m in chart["vimshottari"]["mahadashas"]:
        print(f"  {m['lord']:<9}{m['start'][:10]} → {m['end'][:10]}")
    print(f"\nBalance at birth: {chart['vimshottari']['balance_at_birth_years']:.4f}y "
          f"of {chart['vimshottari']['mahadashas'][0]['lord']}")

    if chart["yogas"]:
        print("\nYogas: " + ", ".join(y["name"] for y in chart["yogas"]))


if __name__ == "__main__":
    main()

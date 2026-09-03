"""Muhurta chooser — scan a date range for auspicious days (a CHOOSER, not a
display; the audit's Tier-2 ask).

Per day (evaluated at local sunrise, the traditional day-start):
- Panchanga: tithi / vara / nakshatra / yoga / karana
- Objections: Rikta tithis (4, 9, 14), Vishti karana (bhadra), Panchaka
  nakshatras (Dhanishta..Revati), Vyatipata & Vaidhriti yogas, Amavasya
- Personal (when natal Moon is supplied): Tarabala (favourable taras 2,4,6,8,9)
  and Chandrabala (favourable at 1,3,6,7,10,11 from natal Moon sign)
- Verdict: score = favourable minus objections, classified good/mixed/avoid.

This is the generic daily screen; activity-specific muhurta (vivaha, griha
pravesha lagna selection) is a further refinement stage.
"""

from __future__ import annotations

from datetime import date, timedelta

from .constants import TITHIS, VARAS
from .ephemeris import houses, jd_to_utc, julian_day_ut, sidereal_positions, sunrise_sunset
from .nakshatra import nakshatra_of
from .panchanga import panchanga

_RIKTA_TITHI_IDX = {3, 8, 13, 18, 23, 28}     # Chaturthi/Navami/Chaturdashi both pakshas (0-based)
_PANCHAKA_NAKS = {22, 23, 24, 25, 26}          # Dhanishta..Revati
_BAD_YOGAS = {"Vyatipata", "Vaidhriti", "Atiganda", "Ganda", "Vyaghata"}
_GOOD_TARAS = {2, 4, 6, 8, 9}
_GOOD_CHANDRA = {1, 3, 6, 7, 10, 11}


def scan_days(start: date, days: int, lat: float, lng: float,
              natal_moon_nak: int | None = None,
              natal_moon_sign: int | None = None,
              ayanamsa: str = "lahiri") -> list[dict]:
    """Evaluate up to 60 consecutive days. Returns one entry per day."""
    from datetime import datetime, time, timezone
    out = []
    for i in range(min(days, 60)):
        d = start + timedelta(days=i)
        # Approximate local noon in UTC to find this day's sunrise.
        approx_noon = datetime.combine(d, time(12, 0), tzinfo=timezone.utc)
        jd_noon = julian_day_ut(approx_noon) - lng / 360.0
        rise_jd, _set_jd = sunrise_sunset(jd_noon, lat, lng)
        eval_jd = rise_jd if rise_jd is not None else jd_noon
        pos = sidereal_positions(eval_jd, ayanamsa=ayanamsa)
        p = panchanga(pos["sun"]["lon"], pos["moon"]["lon"], d, vara_date=d)
        nak = nakshatra_of(pos["moon"]["lon"])
        moon_sign = int(pos["moon"]["lon"] // 30)

        objections: list[str] = []
        favourable: list[str] = []
        tithi_idx0 = p["tithi"]["index"] - 1
        if tithi_idx0 in _RIKTA_TITHI_IDX:
            objections.append(f"rikta tithi ({p['tithi']['name']})")
        if tithi_idx0 == 29:
            objections.append("Amavasya")
        if p["karana"]["name"] == "Vishti":
            objections.append("Vishti karana (bhadra)")
        if nak["index"] in _PANCHAKA_NAKS:
            objections.append(f"panchaka nakshatra ({nak['name']})")
        if p["yoga"]["name"] in _BAD_YOGAS:
            objections.append(f"{p['yoga']['name']} yoga")

        # Classical PANCHAKA: (vara + tithi + nakshatra + lagna) mod 9 —
        # remainders 1 (mrityu), 2 (agni), 4 (raja), 6 (chora), 8 (roga) are
        # doshas. Vara counted Sunday=1; lagna = ascendant at sunrise.
        panchaka = None
        try:
            asc = houses(eval_jd, lat, lng, ayanamsa=ayanamsa,
                         system="whole_sign")["ascendant"]
            vara_num = ((d.weekday() + 1) % 7) + 1        # Sunday=1..Saturday=7
            total = (vara_num + (tithi_idx0 + 1) + (nak["index"] + 1)
                     + (int(asc // 30) + 1))
            rem = total % 9
            names = {1: "mrityu", 2: "agni", 4: "raja", 6: "chora", 8: "roga"}
            panchaka = {"remainder": rem, "dosha": names.get(rem),
                        "clear": rem not in names}
            if panchaka["dosha"]:
                objections.append(f"panchaka dosha ({panchaka['dosha']})")
        except Exception:  # polar / houses failure — panchaka omitted
            pass

        tara = None
        if natal_moon_nak is not None:
            tara_count = (nak["index"] - natal_moon_nak) % 27 % 9 + 1
            tara_names = ["Janma", "Sampat", "Vipat", "Kshema", "Pratyari",
                          "Sadhaka", "Vadha", "Mitra", "Ati-mitra"]
            tara = {"count": tara_count, "name": tara_names[tara_count - 1],
                    "favourable": tara_count in _GOOD_TARAS}
            (favourable if tara["favourable"] else objections).append(
                f"tarabala {tara['name']}")
        chandra = None
        if natal_moon_sign is not None:
            ccount = (moon_sign - natal_moon_sign) % 12 + 1
            chandra = {"count": ccount, "favourable": ccount in _GOOD_CHANDRA}
            (favourable if chandra["favourable"] else objections).append(
                f"chandrabala {ccount}")

        score = len(favourable) - len(objections)
        verdict = "good" if not objections else ("avoid" if score < 0 else "mixed")
        out.append({
            "date": d.isoformat(),
            "vara": p["vara"]["name"],
            "tithi": p["tithi"]["name"],
            "nakshatra": nak["name"],
            "yoga": p["yoga"]["name"],
            "karana": p["karana"]["name"],
            "panchaka": panchaka,
            "sunrise_utc": jd_to_utc(rise_jd).isoformat() if rise_jd else None,
            "tarabala": tara,
            "chandrabala": chandra,
            "objections": objections,
            "favourable": favourable,
            "verdict": verdict,
        })
    return out

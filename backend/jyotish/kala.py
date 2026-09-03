"""Time primitives — ishta kala, kala velas (Gulika/Mandi/Rahu kala/Yamaganda),
planetary horas, special lagnas, formula upagrahas.

Everything here is linear arithmetic on the sunrise-anchored day, which is why
ishta kala must be exact (it comes from the disc-centre no-refraction sunrise
in ephemeris.sunrise_sunset).

Conventions (schools differ — each is stated):
- Day = sunrise→sunset, night = sunset→next sunrise; each divided into EIGHTHS
  for the kala velas.
- Day-segment lords: first segment belongs to the day's vara lord, then the
  remaining weekday lords in weekday order; the 8th segment is lordless. Night
  segments start from the 5th weekday lord after the day lord.
- GULIKA = the START of Saturn's segment; MANDI = the MIDDLE of Saturn's
  segment (the two common schools; both exposed). Their LONGITUDE is the
  ascendant rising at that instant.
- Rahu kala / Yamaganda / Gulika kala use the classical weekday→eighth tables
  (Sunday-first indexing internally).
- Special lagnas per BPHS: Bhava Lagna advances one sign per 5 ghatis from the
  sunrise Sun; Hora Lagna one per 2.5 ghatis; Ghati Lagna one per ghati.
  Pranapada: ishta kala in palas ÷ 15 → signs added to the Sun, plus 0°/240°/
  120° for movable/fixed/dual Sun signs (BPHS 3.71).
- Formula upagrahas (BPHS chain): Dhuma = Sun+133°20'; Vyatipata = 360−Dhuma;
  Parivesha = Vyatipata+180; Indrachapa = 360−Parivesha; Upaketu =
  Indrachapa+16°40'. The chain closes: Upaketu+30° = Sun (tested).
"""

from __future__ import annotations

from .constants import SIGNS, VARA_LORDS
from .ephemeris import houses, jd_to_utc

GHATI_DAYS = 1.0 / 60.0          # 1 ghati = 24 minutes

# Weekday order for segment-lord succession (Sunday-first classical order).
_WEEKDAY_LORDS_SUN_FIRST = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]
# Planetary HORA succession (descending orbital speed).
_HORA_ORDER = ["sun", "venus", "mercury", "moon", "saturn", "jupiter", "mars"]

# Classical eighth-portion tables, Sunday-first weekday indexing, 1-based parts.
_RAHU_KALA_PART = {0: 8, 1: 2, 2: 7, 3: 5, 4: 6, 5: 4, 6: 3}
_YAMAGANDA_PART = {0: 5, 1: 4, 2: 3, 3: 2, 4: 1, 5: 7, 6: 6}
_GULIKA_KALA_PART = {0: 7, 1: 6, 2: 5, 3: 4, 4: 3, 5: 2, 6: 1}


def _sun_first(weekday_mon0: int) -> int:
    """Python weekday (Mon=0) → Sunday-first index (Sun=0)."""
    return (weekday_mon0 + 1) % 7


def ishta_kala(jd_ut: float, sunrise_jd: float) -> dict:
    """Ghatis/vighatis elapsed since local sunrise (negative → before sunrise;
    callers pass the PREVIOUS day's sunrise for pre-dawn births)."""
    ghatis = (jd_ut - sunrise_jd) / GHATI_DAYS
    return {"ghatis": round(ghatis, 6),
            "vighatis": round(ghatis * 60.0, 4),
            "palas": round(ghatis * 60.0, 4)}  # pala == vighati


def kala_velas(sunrise_jd: float, sunset_jd: float, next_sunrise_jd: float,
               weekday_mon0: int) -> dict:
    """The eight day segments + eight night segments with lords, Gulika/Mandi
    instants, and the Rahu kala / Yamaganda / Gulika kala day-periods."""
    wd = _sun_first(weekday_mon0)
    day_len = sunset_jd - sunrise_jd
    night_len = next_sunrise_jd - sunset_jd
    day_seg = day_len / 8.0
    night_seg = night_len / 8.0

    day_lords = [_WEEKDAY_LORDS_SUN_FIRST[(wd + i) % 7] for i in range(7)] + [None]
    night_start_lord = (wd + 4) % 7  # 5th weekday lord from the day lord
    night_lords = [_WEEKDAY_LORDS_SUN_FIRST[(night_start_lord + i) % 7] for i in range(7)] + [None]

    def _segments(start: float, seg: float, lords: list) -> list[dict]:
        return [{"part": i + 1, "lord": lords[i],
                 "start_jd": start + i * seg, "end_jd": start + (i + 1) * seg}
                for i in range(8)]

    day_segments = _segments(sunrise_jd, day_seg, day_lords)
    night_segments = _segments(sunset_jd, night_seg, night_lords)

    sat_day = next(s for s in day_segments if s["lord"] == "saturn")
    sat_night = next(s for s in night_segments if s["lord"] == "saturn")

    def _period(part_1based: int) -> dict:
        s = day_segments[part_1based - 1]
        return {"start_utc": jd_to_utc(s["start_jd"]).isoformat(),
                "end_utc": jd_to_utc(s["end_jd"]).isoformat()}

    return {
        "day_segments": day_segments,
        "night_segments": night_segments,
        "gulika_day_jd": sat_day["start_jd"],
        "mandi_day_jd": (sat_day["start_jd"] + sat_day["end_jd"]) / 2.0,
        "gulika_night_jd": sat_night["start_jd"],
        "mandi_night_jd": (sat_night["start_jd"] + sat_night["end_jd"]) / 2.0,
        "rahu_kala": _period(_RAHU_KALA_PART[wd]),
        "yamaganda": _period(_YAMAGANDA_PART[wd]),
        "gulika_kala": _period(_GULIKA_KALA_PART[wd]),
    }


def gulika_mandi_longitudes(velas: dict, is_day_birth: bool, lat: float, lng: float,
                            ayanamsa: str = "lahiri") -> dict:
    """Gulika/Mandi as LONGITUDES: the ascendant rising at their instants."""
    g_jd = velas["gulika_day_jd"] if is_day_birth else velas["gulika_night_jd"]
    m_jd = velas["mandi_day_jd"] if is_day_birth else velas["mandi_night_jd"]
    out = {}
    for name, jd in (("gulika", g_jd), ("mandi", m_jd)):
        try:
            asc = houses(jd, lat, lng, ayanamsa=ayanamsa, system="whole_sign")["ascendant"]
            out[name] = {"lon": round(asc, 6), "sign": int(asc // 30),
                         "sign_name": SIGNS[int(asc // 30)]["en"],
                         "jd": jd, "utc": jd_to_utc(jd).isoformat()}
        except Exception:  # pragma: no cover — polar
            out[name] = None
    return out


def hora_at(jd_ut: float, sunrise_jd: float, sunset_jd: float,
            next_sunrise_jd: float, weekday_mon0: int) -> dict:
    """Unequal planetary hora: 12 day-horas (day/12) + 12 night-horas, lords in
    hora order starting from the vara lord at sunrise."""
    wd = _sun_first(weekday_mon0)
    start_lord_idx = _HORA_ORDER.index(_WEEKDAY_LORDS_SUN_FIRST[wd])
    if jd_ut < sunset_jd:
        seg = (sunset_jd - sunrise_jd) / 12.0
        n = int((jd_ut - sunrise_jd) / seg)
    else:
        seg = (next_sunrise_jd - sunset_jd) / 12.0
        n = 12 + int((jd_ut - sunset_jd) / seg)
    n = max(0, min(23, n))
    return {"hora_number": n + 1,
            "lord": _HORA_ORDER[(start_lord_idx + n) % 7]}


def special_lagnas(sun_lon_at_sunrise: float, sun_lon_at_birth: float,
                   ghatis: float) -> dict:
    """BPHS special lagnas as linear functions of ishta kala."""
    bhava = (sun_lon_at_sunrise + ghatis * 6.0) % 360.0      # 30° / 5 ghati
    hora = (sun_lon_at_sunrise + ghatis * 12.0) % 360.0      # 30° / 2.5 ghati
    ghati_l = (sun_lon_at_sunrise + ghatis * 30.0) % 360.0   # 30° / ghati
    sun_sign = int(sun_lon_at_birth // 30)
    mobility = SIGNS[sun_sign]["mobility"]
    extra = {"movable": 0.0, "fixed": 240.0, "dual": 120.0}[mobility]
    pranapada = (sun_lon_at_birth + (ghatis * 60.0 / 15.0) * 30.0 + extra) % 360.0
    def _fmt(lon: float) -> dict:
        return {"lon": round(lon, 6), "sign": int(lon // 30),
                "sign_name": SIGNS[int(lon // 30)]["en"]}
    return {"bhava_lagna": _fmt(bhava), "hora_lagna": _fmt(hora),
            "ghati_lagna": _fmt(ghati_l), "pranapada": _fmt(pranapada)}


def formula_upagrahas(sun_lon: float) -> dict:
    """The five formula upagrahas (BPHS chain from the Sun)."""
    dhuma = (sun_lon + 133.0 + 20.0 / 60.0) % 360.0
    vyatipata = (360.0 - dhuma) % 360.0
    parivesha = (vyatipata + 180.0) % 360.0
    indrachapa = (360.0 - parivesha) % 360.0
    upaketu = (indrachapa + 16.0 + 40.0 / 60.0) % 360.0
    def _fmt(lon: float) -> dict:
        return {"lon": round(lon, 6), "sign": int(lon // 30),
                "sign_name": SIGNS[int(lon // 30)]["en"]}
    return {"dhuma": _fmt(dhuma), "vyatipata": _fmt(vyatipata),
            "parivesha": _fmt(parivesha), "indrachapa": _fmt(indrachapa),
            "upaketu": _fmt(upaketu)}

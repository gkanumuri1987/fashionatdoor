"""Birth-time rectification screening — Pranapada & Gulika (Kunda) scoring.

A SCREENING AID, not a verdict: it scans candidate minutes across the stated
uncertainty band and scores each by classical validity checks, surfacing the
minutes where the checks concentrate. Event-based fitting (dasha vs life
events) remains the astrologer's final arbiter.

Checks (documented conventions):
1. PRANAPADA CHECK (BPHS 4.7-8): a birth time is supported when the lagna
   falls in a kendra (1,4,7,10) or trikona (1,5,9) FROM the Pranapada — the
   strongest classical time-validity rule. +2 when it holds.
2. GULIKA (Kunda) CHECK: the Moon (mind entering the body) standing in
   kendra/trikona from Gulika's longitude supports the time. +1.
3. NAVAMSA-LAGNA STABILITY: candidates where the navamsa lagna also holds its
   sign for ±1 minute score +1 (a navamsa-boundary minute is fragile).
Scores are comparative WITHIN the band; ties are natural and reported.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

from .chart import compute_chart
from .ephemeris import houses, julian_day_ut
from .geo import to_utc
from .kala import ishta_kala, kala_velas, special_lagnas
from .ephemeris import sidereal_positions, sunrise_sunset
from .varga import d9

_KENDRA_TRIKONA = {1, 4, 5, 7, 9, 10}


def _house_from(sign: int, ref: int) -> int:
    return (sign - ref) % 12 + 1


def rectify(birth_date: date, birth_time: time, lat: float, lng: float,
            tz_name: str | None = None, band_minutes: int = 30,
            step_minutes: int = 2, ayanamsa: str = "lahiri") -> dict:
    """Scan [t-band, t+band] in steps; score each candidate. Capped workload:
    band<=120, step>=1."""
    band_minutes = min(band_minutes, 120)
    step_minutes = max(step_minutes, 1)

    instant = to_utc(birth_date, birth_time, tz_name=tz_name, lat=lat, lng=lng)
    base_jd = julian_day_ut(instant.utc)
    rise_jd, set_jd = sunrise_sunset(base_jd, lat, lng)
    if rise_jd is None or set_jd is None:
        return {"error": "Sunrise unavailable at this latitude — cannot score."}
    _, next_rise = sunrise_sunset(base_jd + 1.0, lat, lng)
    next_rise = next_rise or set_jd + 0.5

    # Anchor for pre-dawn candidates handled per-candidate below.
    candidates = []
    for offset in range(-band_minutes, band_minutes + 1, step_minutes):
        jd = base_jd + offset / 1440.0
        try:
            asc = houses(jd, lat, lng, ayanamsa=ayanamsa, system="whole_sign")["ascendant"]
        except Exception:
            continue
        lagna_sign = int(asc // 30)
        pos = sidereal_positions(jd, ayanamsa=ayanamsa)
        moon_sign = int(pos["moon"]["lon"] // 30)

        anchor_rise = rise_jd
        vara_shift = 0
        if jd < rise_jd:
            pr, _ = sunrise_sunset(jd - 1.0, lat, lng)
            if pr is not None:
                anchor_rise = pr
                vara_shift = -1
        ik = ishta_kala(jd, anchor_rise)
        sun_at_rise = sidereal_positions(anchor_rise, ayanamsa=ayanamsa)["sun"]["lon"]
        sl = special_lagnas(sun_at_rise, pos["sun"]["lon"], ik["ghatis"])
        pp_sign = sl["pranapada"]["sign"]

        weekday = (instant.utc + timedelta(minutes=offset)).astimezone(timezone.utc)
        vd = (birth_date + timedelta(days=vara_shift)).weekday()
        velas = kala_velas(anchor_rise, set_jd if set_jd > anchor_rise else set_jd,
                           next_rise, vd)
        is_day = anchor_rise <= jd < set_jd
        g_jd = velas["gulika_day_jd"] if is_day else velas["gulika_night_jd"]
        try:
            gulika_sign = int(houses(g_jd, lat, lng, ayanamsa=ayanamsa,
                                     system="whole_sign")["ascendant"] // 30)
        except Exception:
            gulika_sign = None

        score = 0
        reasons = []
        if _house_from(lagna_sign, pp_sign) in _KENDRA_TRIKONA:
            score += 2
            reasons.append("lagna in kendra/trikona from Pranapada (BPHS)")
        if gulika_sign is not None and _house_from(moon_sign, gulika_sign) in _KENDRA_TRIKONA:
            score += 1
            reasons.append("Moon in kendra/trikona from Gulika")
        # Navamsa-lagna stability across ±1 minute.
        try:
            n_here = d9(asc)
            n_prev = d9(houses(jd - 1 / 1440.0, lat, lng, ayanamsa=ayanamsa,
                               system="whole_sign")["ascendant"])
            n_next = d9(houses(jd + 1 / 1440.0, lat, lng, ayanamsa=ayanamsa,
                               system="whole_sign")["ascendant"])
            if n_here == n_prev == n_next:
                score += 1
                reasons.append("navamsa lagna stable at this minute")
        except Exception:
            pass

        local_t = (datetime.combine(birth_date, birth_time)
                   + timedelta(minutes=offset)).time()
        candidates.append({"offset_minutes": offset,
                           "local_time": local_t.strftime("%H:%M"),
                           "lagna_sign": lagna_sign,
                           "pranapada_sign": pp_sign,
                           "score": score, "reasons": reasons})

    best = max((c["score"] for c in candidates), default=0)
    return {
        "schema": "RectifyV1",
        "band_minutes": band_minutes,
        "step_minutes": step_minutes,
        "candidates": candidates,
        "best_score": best,
        "best_times": [c["local_time"] for c in candidates if c["score"] == best],
        "note": "Screening aid only — classical validity checks concentrate on "
                "these minutes; confirm against dasha-vs-life-events before "
                "adopting a rectified time.",
    }

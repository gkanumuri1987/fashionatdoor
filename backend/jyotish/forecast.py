"""Personal Jyothishyam — deterministic daily & weekly forecast.

NOT AI-imagined. Every judgment is computed from classical panchanga rules
applied to the person's OWN natal chart:

- TARABALA: today's nakshatra counted from the native's janma (birth) nakshatra,
  folded 1-9 → Janma/Sampat/Vipat/Kshema/Pratyak/Sadhaka/Vadha/Mitra/Atimitra.
- CHANDRABALA: the transit Moon's sign counted from the natal Moon sign
  (favourable at 1,3,6,7,10,11).
- TITHI nature: Nanda / Bhadra / Jaya / Rikta / Purna groups.
- NAKSHATRA activity-class (BPHS/Muhurta): chara/sthira/ugra/mishra/kshipra/
  mridu/tikshna — which acts each supports.
- VARA lord → presiding deity + the day's natural affairs.
- CAUTIONS: Rahu kalam window, rikta tithi, panchaka nakshatra, malefic yoga.
- DASHA: the running maha/antar lords → the graha to strengthen this period and
  its deity (the week's worship focus).
- INTERESTS: the native's chosen focus areas (career/relationship/health/
  finance/spiritual) surface the relevant houses' transit notes.

The AI layer (ai/jyothishyam.py) only phrases this warmly; the substance here.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from .chart import transit_report
from .constants import NAKSHATRAS, SIGNS, VARA_LORDS, VARAS
from .ephemeris import (jd_to_utc, julian_day_ut, sidereal_positions,
                        sunrise_sunset)
from .kala import kala_velas
from .remedy_rationale import remedy_for
from .nakshatra import nakshatra_of
from . import forecast_locale as floc

# ── Vara → deity + affairs ──────────────────────────────────────────────────
VARA_DEITY = {
    0: ("Chandra / Shiva", "emotions, mother, water, liquids, travel, the mind"),        # Mon
    1: ("Mangala / Hanuman", "courage, land & property, disputes, surgery, siblings"),    # Tue
    2: ("Budha / Vishnu", "study, communication, trade, writing, accounts"),              # Wed
    3: ("Guru / Dakshinamurthy", "wisdom, wealth, marriage, dharma, teachers, children"), # Thu
    4: ("Shukra / Lakshmi", "love, arts, comforts, vehicles, beauty, partnerships"),      # Fri
    5: ("Shani / Hanuman", "labour, discipline, service, iron, elders, karma"),           # Sat
    6: ("Surya / Rama", "authority, health, father, government, self-standing"),           # Sun
}

# ── Tithi nature (1-15 within paksha; 15 handled) ───────────────────────────
_TITHI_GROUP = {  # number 1..15 → (group, note)
    1: ("Nanda", "joyful — celebrations, prosperity"),
    6: ("Nanda", "joyful — celebrations, prosperity"),
    11: ("Nanda", "joyful — celebrations, prosperity"),
    2: ("Bhadra", "strong & healthy — steady work, foundations"),
    7: ("Bhadra", "strong & healthy — steady work, foundations"),
    12: ("Bhadra", "strong & healthy — steady work, foundations"),
    3: ("Jaya", "victorious — competition, effort, bold moves"),
    8: ("Jaya", "victorious — competition, effort, bold moves"),
    13: ("Jaya", "victorious — competition, effort, bold moves"),
    4: ("Rikta", "empty — avoid new & auspicious starts today"),
    9: ("Rikta", "empty — avoid new & auspicious starts today"),
    14: ("Rikta", "empty — avoid new & auspicious starts today"),
    5: ("Purna", "full — all-round auspicious, completions"),
    10: ("Purna", "full — all-round auspicious, completions"),
    15: ("Purna", "full — all-round auspicious, completions"),
}

# ── Nakshatra activity class (index 0-26) ───────────────────────────────────
_NAK_CLASS = {
    "chara": ({5, 6, 21, 22, 23}, "movement, travel, vehicles, change"),          # Swati,Punarvasu,Shravana,Dhanishta,Shatabhisha (0-based:14?)
    "sthira": ({3, 11, 20, 25}, "permanent things — building, planting, savings"),
    "ugra": ({1, 9, 10, 19, 24}, "bold/forceful acts, confrontation, demolition"),
    "mishra": ({2, 15}, "mixed acts, fire rituals, routine"),
    "kshipra": ({0, 7, 12}, "quick tasks, trade, arts, medicine, learning"),
    "mridu": ({4, 13, 16, 26}, "gentle acts — arts, romance, friendship, study"),
    "tikshna": ({6, 8, 17, 18}, "sharp acts — mantra, discipline, breaking ties"),
}
# Correct canonical index sets (0-based, Ashwini=0):
_NAK_CLASS = {
    "chara": ({14, 6, 21, 22, 23}, "movement, travel, vehicles, change"),         # Swati(14),Punarvasu(6),Shravana(21),Dhanishta(22),Shatabhisha(23)
    "sthira": ({3, 11, 20, 25}, "permanent things — building, planting, savings"), # Rohini,UPhalguni,UAshadha,UBhadrapada
    "ugra": ({1, 9, 10, 19, 24}, "bold/forceful acts, confrontation, demolition"), # Bharani,Magha,PPhalguni,PAshadha,PBhadrapada
    "mishra": ({2, 15}, "mixed acts, fire rituals, routine"),                      # Krittika,Vishakha
    "kshipra": ({0, 7, 12}, "quick tasks, trade, arts, medicine, learning"),       # Ashwini,Pushya,Hasta
    "mridu": ({4, 13, 16, 26}, "gentle acts — arts, romance, friendship, study"),  # Mrigashira,Chitra,Anuradha,Revati
    "tikshna": ({5, 8, 17, 18}, "sharp acts — mantra, discipline, breaking ties"), # Ardra,Ashlesha,Jyeshtha,Mula
}

_TARA = [
    ("Janma", False, "guard your body & health today"),
    ("Sampat", True, "wealth & gains favoured"),
    ("Vipat", False, "risk — postpone the important"),
    ("Kshema", True, "well-being & ease"),
    ("Pratyak", False, "obstacles — expect friction"),
    ("Sadhaka", True, "accomplishment — push your goals"),
    ("Vadha", False, "harmful — avoid new & risky acts"),
    ("Mitra", True, "friendly — support flows to you"),
    ("Atimitra", True, "very friendly — an excellent day"),
]

_PANCHAKA_NAKS = {22, 23, 24, 25, 26}
_BAD_YOGAS = {"Vishkambha", "Atiganda", "Shula", "Ganda", "Vyaghata",
              "Vajra", "Vyatipata", "Parigha", "Vaidhriti"}

# ── Dasha lord → deity to strengthen + simple remedy ────────────────────────
GRAHA_DEITY = {
    "sun": ("Surya / Lord Rama", "Offer water to the Sun at dawn; Aditya Hridayam."),
    "moon": ("Chandra / Lord Shiva", "White flowers to Shiva on Mondays; Om Namah Shivaya."),
    "mars": ("Mangala / Hanuman", "Hanuman Chalisa on Tuesdays; red flowers."),
    "mercury": ("Budha / Vishnu", "Vishnu Sahasranama; feed green gram to birds."),
    "jupiter": ("Guru / Dakshinamurthy", "Yellow to a temple on Thursdays; honour teachers."),
    "venus": ("Shukra / Lakshmi", "Lakshmi puja on Fridays; respect women & the arts."),
    "saturn": ("Shani / Hanuman", "Sesame-oil lamp to Hanuman on Saturdays; serve elders."),
    "rahu": ("Rahu / Durga", "Durga upasana; Durga Saptashati."),
    "ketu": ("Ketu / Ganesha", "Ganesha worship; Sankashti Chaturthi."),
}

INTEREST_HOUSES = {
    "career": (10, "career, work, reputation"),
    "relationship": (7, "partnership, marriage, love"),
    "health": (1, "vitality, body, energy"),
    "finance": (2, "wealth, savings, family resources"),
    "education": (5, "learning, creativity, children"),
    "spiritual": (9, "dharma, fortune, higher wisdom"),
}


def _tithi_parts(sun_lon: float, moon_lon: float) -> tuple[int, str, int]:
    elong = (moon_lon - sun_lon) % 360.0
    idx0 = min(29, int(elong // 12.0))
    paksha = "shukla" if idx0 < 15 else "krishna"
    number = idx0 % 15 + 1
    return idx0, paksha, number


def _nak_class(nak_idx: int) -> tuple[str, str]:
    for name, (members, note) in _NAK_CLASS.items():
        if nak_idx in members:
            return name, note
    return "mishra", _NAK_CLASS["mishra"][1]


def _day_forecast(chart: dict, d: date, tz: ZoneInfo, lat: float, lng: float,
                  interests: list[str], ayanamsa: str, language: str = "en") -> dict:
    noon_local = datetime.combine(d, time(12, 0), tzinfo=tz)
    jd_noon = julian_day_ut(noon_local.astimezone(timezone.utc))
    rise_jd, set_jd = sunrise_sunset(jd_noon, lat, lng)
    eval_jd = rise_jd if rise_jd else jd_noon
    pos = sidereal_positions(eval_jd, ayanamsa=ayanamsa)

    tidx, paksha, tnum = _tithi_parts(pos["sun"]["lon"], pos["moon"]["lon"])
    tithi_group = _TITHI_GROUP[tnum][0]
    tithi_note = floc.tithi_note(tithi_group, language)
    nak = nakshatra_of(pos["moon"]["lon"])
    nclass = _nak_class(nak["index"])[0]
    nclass_note = floc.class_note(nclass, language)

    natal_nak = chart["grahas"]["moon"]["nakshatra"]["index"]
    natal_moon_sign = chart["moon_sign"]
    tara_i = (nak["index"] - natal_nak) % 27 % 9
    tara_name, tara_good, _tara_note_en = _TARA[tara_i]
    tara_note = floc.tara_note(tara_name, language)
    moon_sign = int(pos["moon"]["lon"] // 30)
    chandra_house = (moon_sign - natal_moon_sign) % 12 + 1
    chandra_good = chandra_house in (1, 3, 6, 7, 10, 11)

    yoga_idx = min(26, int(((pos["sun"]["lon"] + pos["moon"]["lon"]) % 360.0) // (360.0 / 27.0)))
    from .constants import YOGAS_27
    yoga_name = YOGAS_27[yoga_idx]

    vara = d.weekday()
    deity = VARA_DEITY[vara][0]
    affairs = floc.affairs(vara, language)

    # Cautions
    cautions = []
    rahu = None
    if rise_jd and set_jd:
        try:
            _, nxt = sunrise_sunset(jd_noon + 1.0, lat, lng)
            velas = kala_velas(rise_jd, set_jd, nxt or set_jd + 0.5, vara)
            rk = velas["rahu_kala"]
            rahu = (datetime.fromisoformat(rk["start_utc"]).astimezone(tz).strftime("%H:%M")
                    + "–" + datetime.fromisoformat(rk["end_utc"]).astimezone(tz).strftime("%H:%M"))
        except Exception:
            pass
    if rahu:
        cautions.append(floc.tmpl("caution_rahu", language, win=rahu))
    if tithi_group == "Rikta":
        cautions.append(floc.tmpl("caution_rikta", language, note=tithi_note))
    if not tara_good:
        cautions.append(floc.tmpl("caution_tara", language, name=tara_name, note=tara_note))
    if not chandra_good:
        cautions.append(floc.tmpl("caution_moon", language))
    if nak["index"] in _PANCHAKA_NAKS:
        cautions.append(floc.tmpl("caution_panchaka", language, nak=nak["name"]))
    if yoga_name in _BAD_YOGAS:
        cautions.append(floc.tmpl("caution_yoga", language, yoga=yoga_name))

    # Verdicts for the two kinds of action.
    new_score = (2 if tithi_group in ("Nanda", "Jaya", "Purna") else -2) \
        + (2 if tara_good else -2) + (1 if chandra_good else -1) \
        + (-2 if (rahu and tithi_group == "Rikta") else 0)
    new_ventures = ("favourable" if new_score >= 3 else "avoid" if new_score <= -2 else "mixed")
    continuations = ("smooth" if (tara_good and chandra_good) else
                     "push through" if tara_good or chandra_good else "go slow")

    focus = []
    for it in interests:
        h = INTEREST_HOUSES.get(it)
        if not h:
            continue
        house, _label_en = h
        label = floc.house_label(it, language) or _label_en
        sign = (chart["lagna"]["sign"] + house - 1) % 12
        occupant = next((g for g, gd in pos.items()
                         if int(gd["lon"] // 30) == sign), None)
        focus.append({
            "interest": it, "house": house, "about": label,
            "note": floc.tmpl("focus_live" if occupant else "focus_quiet",
                              language, house=house, label=label),
        })

    return {
        "date": d.isoformat(),
        "weekday": floc.vara_display(vara, VARAS[vara], language),
        "vara_deity": floc.deity_display(vara, deity, language),
        "day_affairs": affairs,
        "tithi": {"name": floc.tithi_display(paksha, tnum, _tithi_name(tidx), language),
                  "group": floc.group_display(tithi_group, language),
                  "note": tithi_note},
        "nakshatra": {"name": floc.nak_name(nak["name"], nak["index"], language),
                      "class": floc.class_display(nclass, language),
                      "supports": nclass_note},
        "yoga": yoga_name,
        "tarabala": {"name": floc.tara_display(tara_name, language),
                     "favourable": tara_good, "note": tara_note},
        "chandrabala": {"house": chandra_house, "favourable": chandra_good},
        "new_ventures": new_ventures,
        "continuations": continuations,
        "cautions": cautions,
        "rahu_kalam": rahu,
        "focus": focus,
    }


def _tithi_name(idx0: int) -> str:
    from .constants import TITHIS
    return TITHIS[idx0]


def personal_forecast(chart: dict, interests: list[str] | None = None,
                      tz_name: str = "Asia/Kolkata", lat: float | None = None,
                      lng: float | None = None, as_of: date | None = None,
                      language: str = "en") -> dict:
    """Daily (today) + weekly (7 days) personal Jyothishyam for a natal chart.

    Location defaults to the natal place unless overridden (a person abroad
    gets their local panchanga)."""
    interests = interests or []
    ayanamsa = chart["input"]["ayanamsa"]
    lat = lat if lat is not None else chart["input"]["lat"]
    lng = lng if lng is not None else chart["input"]["lng"]
    tz = ZoneInfo(tz_name)
    today = as_of or datetime.now(tz).date()

    days = [_day_forecast(chart, today + timedelta(days=i), tz, lat, lng, interests, ayanamsa, language)
            for i in range(7)]

    # Week highlights.
    best = [d["date"] for d in days if d["new_ventures"] == "favourable"]
    careful = [d["date"] for d in days if d["new_ventures"] == "avoid"]

    # Dasha deity for the week (running maha, then antar).
    cur = chart.get("current_dasha") or {}
    maha = cur.get("maha")
    antar = cur.get("antar")
    maha_r = remedy_for(maha)
    antar_r = remedy_for(antar)

    # Sade sati / notable transit note.
    try:
        tr = transit_report(chart)
        sade = tr["sade_sati"]
    except Exception:
        sade = None

    return {
        "schema": "JyothishyamV1",
        "today": days[0],
        "week": days,
        "week_highlights": {
            "good_days": best, "careful_days": careful,
        },
        "period": {
            "maha_lord": maha, "antar_lord": antar,
            "week_deity": floc.remedy(maha, "deity", maha_r["deity"], language),
            "week_remedy": floc.remedy(maha, "practice", maha_r["practice"], language),
            "week_rationale": floc.remedy(maha, "rationale", maha_r["rationale"], language),
            "antar_deity": floc.remedy(antar, "deity", antar_r["deity"], language),
            "antar_remedy": floc.remedy(antar, "practice", antar_r["practice"], language),
            "antar_rationale": floc.remedy(antar, "rationale", antar_r["rationale"], language),
        },
        "sade_sati": sade,
        "note": floc.tmpl("note_footer", language),
    }

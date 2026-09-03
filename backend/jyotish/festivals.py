"""Festival rules engine + monthly panchanga calendar builder.

THE ACCURACY MODEL (why timezone matters): a festival's civil date is decided
by which tithi prevails at the OBSERVER'S local sunrise (udaya-vyapini), with
the classical exceptions — Shivaratri and Janmashtami go by the tithi at local
MIDNIGHT (nishita), Deepavali by the amavasya prevailing at local SUNSET
(pradosha). A tithi that ends at 06:40 IST has already ended the previous
evening in New York — so the same festival can fall a day apart between India
and the US, and this module computes each day's panchanga AT THE SELECTED
LOCATION'S sunrise, never by converting Indian dates.

Festival rules are (amanta masa, paksha, tithi) triples, solar-ingress days
(sankranti), or derived days (Bhogi = day before Makara sankranti; Varalakshmi
= last Friday before Shravana Purnima). Traditions filter which festivals show
and how months are labelled: telugu/kannada = amanta lunar months, tamil =
solar months (day-of-solar-month), hindi (north) = purnimanta labels noted.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from .calendar_hindu import samvatsara
from .constants import NAKSHATRAS, TITHIS, VARAS
from .ephemeris import jd_to_utc, julian_day_ut, sidereal_positions, sunrise_sunset
from .events import masa as amanta_masa
from .events import nakshatra_end, sankranti, tithi_end
from .kala import kala_velas
from .nakshatra import nakshatra_of

# Representative computation points per timezone choice.
LOCATIONS = {
    "in": {"tz": "Asia/Kolkata", "lat": 17.385, "lng": 78.4867, "label": "India"},
    "uk": {"tz": "Europe/London", "lat": 51.5074, "lng": -0.1278, "label": "United Kingdom"},
    "us_east": {"tz": "America/New_York", "lat": 40.7128, "lng": -74.006, "label": "US East"},
    "us_central": {"tz": "America/Chicago", "lat": 41.8781, "lng": -87.6298, "label": "US Central"},
    "us_west": {"tz": "America/Los_Angeles", "lat": 34.0522, "lng": -118.2437, "label": "US West"},
    "au": {"tz": "Australia/Sydney", "lat": -33.8688, "lng": 151.2093, "label": "Australia"},
}

TRADITIONS = ("telugu", "tamil", "kannada", "hindi")

# Solar (Tamil) month names by the Sun's sidereal sign.
TAMIL_MONTHS = ["Chithirai", "Vaikasi", "Aani", "Aadi", "Aavani", "Purattasi",
                "Aippasi", "Karthigai", "Margazhi", "Thai", "Maasi", "Panguni"]

# ── The major-festival table ────────────────────────────────────────────────
# kind: lunar {masa, paksha, tithi(1-15)} | solar {sign} | derived
# observance: sunrise | midnight | sunset  (which instant decides the tithi)
# regions: which traditions display it. names: en + native per tradition.
FESTIVALS: list[dict] = [
    {"key": "makara_sankranti", "kind": "solar", "sign": 9,
     "regions": ("telugu", "tamil", "kannada", "hindi"),
     "names": {"en": "Makara Sankranti / Pongal", "telugu": "మకర సంక్రాంతి",
               "tamil": "தைப்பொங்கல்", "kannada": "ಮಕರ ಸಂಕ್ರಾಂತಿ", "hindi": "मकर संक्रांति"}},
    {"key": "bhogi", "kind": "derived", "base": "makara_sankranti", "offset": -1,
     "regions": ("telugu", "tamil"),
     "names": {"en": "Bhogi", "telugu": "భోగి", "tamil": "போகி", "hindi": "भोगी"}},
    {"key": "kanuma", "kind": "derived", "base": "makara_sankranti", "offset": 1,
     "regions": ("telugu",),
     "names": {"en": "Kanuma", "telugu": "కనుమ"}},
    {"key": "vasant_panchami", "kind": "lunar", "masa": "Magha", "paksha": "shukla", "tithi": 5,
     "regions": ("hindi", "kannada"),
     "names": {"en": "Vasant Panchami", "hindi": "वसंत पंचमी", "kannada": "ವಸಂತ ಪಂಚಮಿ"}},
    {"key": "ratha_saptami", "kind": "lunar", "masa": "Magha", "paksha": "shukla", "tithi": 7,
     "regions": ("telugu", "kannada"),
     "names": {"en": "Ratha Saptami", "telugu": "రథ సప్తమి", "kannada": "ರಥ ಸಪ್ತಮಿ"}},
    {"key": "maha_shivaratri", "kind": "lunar", "masa": "Magha", "paksha": "krishna", "tithi": 14,
     "observance": "midnight",
     "regions": ("telugu", "tamil", "kannada", "hindi"),
     "names": {"en": "Maha Shivaratri", "telugu": "మహా శివరాత్రి",
               "tamil": "மகா சிவராத்திரி", "kannada": "ಮಹಾ ಶಿವರಾತ್ರಿ", "hindi": "महा शिवरात्रि"}},
    {"key": "holi", "kind": "lunar", "masa": "Phalguna", "paksha": "shukla", "tithi": 15,
     "regions": ("hindi",),
     "names": {"en": "Holi (Purnima)", "hindi": "होली"}},
    {"key": "ugadi", "kind": "lunar", "masa": "Chaitra", "paksha": "shukla", "tithi": 1,
     "regions": ("telugu", "kannada"),
     "names": {"en": "Ugadi", "telugu": "ఉగాది", "kannada": "ಯುಗಾದಿ"}},
    {"key": "rama_navami", "kind": "lunar", "masa": "Chaitra", "paksha": "shukla", "tithi": 9,
     "regions": ("telugu", "tamil", "kannada", "hindi"),
     "names": {"en": "Sri Rama Navami", "telugu": "శ్రీరామ నవమి",
               "tamil": "ராம நவமி", "kannada": "ರಾಮ ನವಮಿ", "hindi": "राम नवमी"}},
    {"key": "hanuman_jayanti", "kind": "lunar", "masa": "Chaitra", "paksha": "shukla", "tithi": 15,
     "regions": ("hindi", "tamil"),
     "names": {"en": "Hanuman Jayanti / Chitra Pournami", "hindi": "हनुमान जयंती",
               "tamil": "சித்ரா பௌர்ணமி"}},
    {"key": "mesha_sankranti", "kind": "solar", "sign": 0,
     "regions": ("tamil", "hindi"),
     "names": {"en": "Puthandu / Vishu / Baisakhi", "tamil": "புத்தாண்டு", "hindi": "बैसाखी"}},
    {"key": "akshaya_tritiya", "kind": "lunar", "masa": "Vaishakha", "paksha": "shukla", "tithi": 3,
     "regions": ("telugu", "tamil", "kannada", "hindi"),
     "names": {"en": "Akshaya Tritiya", "telugu": "అక్షయ తృతీయ",
               "tamil": "அட்சய திருதியை", "kannada": "ಅಕ್ಷಯ ತೃತೀಯ", "hindi": "अक्षय तृतीया"}},
    {"key": "guru_purnima", "kind": "lunar", "masa": "Ashadha", "paksha": "shukla", "tithi": 15,
     "regions": ("telugu", "tamil", "kannada", "hindi"),
     "names": {"en": "Guru Purnima", "telugu": "గురు పూర్ణిమ",
               "tamil": "குரு பூர்ணிமா", "kannada": "ಗುರು ಪೂರ್ಣಿಮಾ", "hindi": "गुरु पूर्णिमा"}},
    {"key": "varalakshmi_vratam", "kind": "derived_varalakshmi",
     "regions": ("telugu", "kannada"),
     "names": {"en": "Varalakshmi Vratam", "telugu": "వరలక్ష్మీ వ్రతం",
               "kannada": "ವರಮಹಾಲಕ್ಷ್ಮಿ ವ್ರತ"}},
    {"key": "raksha_bandhan", "kind": "lunar", "masa": "Shravana", "paksha": "shukla", "tithi": 15,
     "regions": ("hindi",),
     "names": {"en": "Raksha Bandhan", "hindi": "रक्षा बंधन"}},
    {"key": "janmashtami", "kind": "lunar", "masa": "Shravana", "paksha": "krishna", "tithi": 8,
     "observance": "midnight",
     "regions": ("telugu", "tamil", "kannada", "hindi"),
     "names": {"en": "Krishna Janmashtami", "telugu": "కృష్ణాష్టమి",
               "tamil": "கோகுலாஷ்டமி", "kannada": "ಕೃಷ್ಣ ಜನ್ಮಾಷ್ಟಮಿ", "hindi": "जन्माष्टमी"}},
    {"key": "vinayaka_chavithi", "kind": "lunar", "masa": "Bhadrapada", "paksha": "shukla", "tithi": 4,
     "regions": ("telugu", "tamil", "kannada", "hindi"),
     "names": {"en": "Vinayaka Chavithi / Ganesh Chaturthi", "telugu": "వినాయక చవితి",
               "tamil": "விநாயகர் சதுர்த்தி", "kannada": "ಗಣೇಶ ಚತುರ್ಥಿ", "hindi": "गणेश चतुर्थी"}},
    {"key": "navaratri_begins", "kind": "lunar", "masa": "Ashwina", "paksha": "shukla", "tithi": 1,
     "regions": ("telugu", "tamil", "kannada", "hindi"),
     "names": {"en": "Sharad Navaratri begins", "telugu": "శరన్నవరాత్రి ఆరంభం",
               "tamil": "நவராத்திரி", "kannada": "ನವರಾತ್ರಿ", "hindi": "नवरात्रि प्रारंभ"}},
    {"key": "durgashtami", "kind": "lunar", "masa": "Ashwina", "paksha": "shukla", "tithi": 8,
     "regions": ("telugu", "kannada", "hindi"),
     "names": {"en": "Durgashtami", "telugu": "దుర్గాష్టమి", "kannada": "ದುರ್ಗಾಷ್ಟಮಿ",
               "hindi": "दुर्गाष्टमी"}},
    {"key": "vijayadashami", "kind": "lunar", "masa": "Ashwina", "paksha": "shukla", "tithi": 10,
     "regions": ("telugu", "tamil", "kannada", "hindi"),
     "names": {"en": "Vijayadashami / Dussehra", "telugu": "విజయదశమి",
               "tamil": "விஜயதசமி", "kannada": "ವಿಜಯದಶಮಿ", "hindi": "दशहरा"}},
    {"key": "naraka_chaturdashi", "kind": "lunar", "masa": "Ashwina", "paksha": "krishna", "tithi": 14,
     "regions": ("telugu", "tamil", "kannada"),
     "names": {"en": "Naraka Chaturdashi", "telugu": "నరక చతుర్దశి",
               "tamil": "நரக சதுர்த்தசி", "kannada": "ನರಕ ಚತುರ್ದಶಿ"}},
    {"key": "deepavali", "kind": "lunar", "masa": "Ashwina", "paksha": "krishna", "tithi": 15,
     "observance": "sunset",
     "regions": ("telugu", "tamil", "kannada", "hindi"),
     "names": {"en": "Deepavali", "telugu": "దీపావళి", "tamil": "தீபாவளி",
               "kannada": "ದೀಪಾವಳಿ", "hindi": "दीपावली"}},
    {"key": "karthika_purnima", "kind": "lunar", "masa": "Kartika", "paksha": "shukla", "tithi": 15,
     "regions": ("telugu", "kannada", "hindi"),
     "names": {"en": "Karthika Purnima", "telugu": "కార్తీక పూర్ణిమ",
               "kannada": "ಕಾರ್ತಿಕ ಪೂರ್ಣಿಮಾ", "hindi": "कार्तिक पूर्णिमा"}},
    {"key": "vaikunta_ekadashi", "kind": "lunar", "masa": "Margashirsha", "paksha": "shukla", "tithi": 11,
     "regions": ("telugu", "tamil"),
     "names": {"en": "Vaikunta Ekadashi", "telugu": "వైకుంఠ ఏకాదశి",
               "tamil": "வைகுண்ட ஏகாதசி"}},
]


def _tithi_parts(elong: float) -> tuple[str, int, int]:
    idx0 = min(29, int((elong % 360.0) // 12.0))
    paksha = "shukla" if idx0 < 15 else "krishna"
    number = idx0 % 15 + 1          # 1..15 within the paksha
    return paksha, number, idx0


def _local(jd: float, tz: ZoneInfo) -> datetime:
    return jd_to_utc(jd).astimezone(tz)


def build_month(year: int, month: int, tradition: str = "telugu",
                location: str = "in", ayanamsa: str = "lahiri") -> dict:
    """The full calendar for one English month at one location.

    Each day: local sunrise/sunset, vara, tithi (+ local end time), nakshatra
    (+ end), amanta masa / Tamil solar month+day, Rahu kalam, festivals.
    """
    if tradition not in TRADITIONS:
        tradition = "telugu"
    loc = LOCATIONS.get(location, LOCATIONS["in"])
    tz = ZoneInfo(loc["tz"])
    lat, lng = loc["lat"], loc["lng"]

    ndays = (date(year + (month == 12), (month % 12) + 1, 1) - date(year, month, 1)).days

    # Amanta-masa cache: recompute only when a month boundary passes.
    masa_cache: dict | None = None
    # Previous-sankranti cache for Tamil solar day numbers.
    prev_sankranti: dict | None = None

    days = []
    for dnum in range(1, ndays + 1):
        d = date(year, month, dnum)
        noon_local = datetime.combine(d, time(12, 0), tzinfo=tz)
        jd_noon = julian_day_ut(noon_local.astimezone(timezone.utc))
        rise_jd, set_jd = sunrise_sunset(jd_noon, lat, lng)
        eval_jd = rise_jd if rise_jd is not None else jd_noon

        pos = sidereal_positions(eval_jd, ayanamsa=ayanamsa)
        elong = (pos["moon"]["lon"] - pos["sun"]["lon"]) % 360.0
        paksha, tithi_num, tithi_idx0 = _tithi_parts(elong)
        nak = nakshatra_of(pos["moon"]["lon"])

        # End times (local clock) + whether the end falls on the NEXT civil
        # day (+1 marker) + what follows — the printed-panchangam idiom
        # "Panchami till 14:32, then Shashthi": starts are implicit because
        # each tithi begins exactly when the previous one ends.
        t_end = t_end_next_day = next_tithi = None
        try:
            te = tithi_end(eval_jd, ayanamsa=ayanamsa)
            end_local = _local(te["ends_jd"], tz)
            t_end = end_local.strftime("%H:%M")
            t_end_next_day = end_local.date() > d
            next_tithi = TITHIS[(tithi_idx0 + 1) % 30]
        except Exception:
            pass
        n_end = n_end_next_day = None
        try:
            ne = nakshatra_end(eval_jd, ayanamsa=ayanamsa)
            n_local = _local(ne["ends_jd"], tz)
            n_end = n_local.strftime("%H:%M")
            n_end_next_day = n_local.date() > d
        except Exception:
            pass

        # Amanta masa (cached across days).
        if masa_cache is None or eval_jd >= masa_cache["end_jd"] - 1e-6:
            try:
                masa_cache = amanta_masa(eval_jd, ayanamsa=ayanamsa)
            except Exception:
                masa_cache = {"name": "?", "end_jd": eval_jd + 30, "adhika": False}
        masa_name = masa_cache["name"]

        # Tamil solar month + day.
        sun_sign = int(pos["sun"]["lon"] // 30)
        tamil_month = TAMIL_MONTHS[sun_sign]
        if prev_sankranti is None or prev_sankranti["sign_entered_idx"] != sun_sign:
            try:
                sk = sankranti(eval_jd, direction=-1, ayanamsa=ayanamsa)
                prev_sankranti = {"jd": sk["jd"], "sign_entered_idx": sun_sign}
            except Exception:
                prev_sankranti = {"jd": eval_jd - 15, "sign_entered_idx": sun_sign}
        tamil_day = int(eval_jd - prev_sankranti["jd"]) + 1

        # Good / avoid windows in LOCAL time: Abhijit muhurta (the 8th of the
        # day's 15 muhurtas — the classical daily good window) vs Rahu kalam,
        # Yamaganda, Gulika kalam.
        rahu = yama = gulika_k = abhijit = None
        if rise_jd is not None and set_jd is not None:
            try:
                _, nxt = sunrise_sunset(jd_noon + 1.0, lat, lng)
                velas = kala_velas(rise_jd, set_jd, nxt or set_jd + 0.5, d.weekday())

                def _win(w: dict) -> str:
                    a = datetime.fromisoformat(w["start_utc"]).astimezone(tz)
                    b = datetime.fromisoformat(w["end_utc"]).astimezone(tz)
                    return f"{a.strftime('%H:%M')}–{b.strftime('%H:%M')}"

                rahu = _win(velas["rahu_kala"])
                yama = _win(velas["yamaganda"])
                gulika_k = _win(velas["gulika_kala"])
                day_len = set_jd - rise_jd
                ab_start = rise_jd + 7.0 * day_len / 15.0
                ab_end = rise_jd + 8.0 * day_len / 15.0
                abhijit = (_local(ab_start, tz).strftime("%H:%M") + "–"
                           + _local(ab_end, tz).strftime("%H:%M"))
            except Exception:
                pass

        days.append({
            "date": d.isoformat(), "day": dnum, "weekday": d.weekday(),
            "vara": VARAS[d.weekday()],
            "sunrise": _local(rise_jd, tz).strftime("%H:%M") if rise_jd else None,
            "sunset": _local(set_jd, tz).strftime("%H:%M") if set_jd else None,
            "tithi": {"name": TITHIS[tithi_idx0], "paksha": paksha,
                      "number": tithi_num, "ends": t_end,
                      "ends_next_day": t_end_next_day, "next": next_tithi},
            "nakshatra": {"name": nak["name"], "ends": n_end,
                          "ends_next_day": n_end_next_day},
            "moon_phase": ("full" if (paksha == "shukla" and tithi_num == 15)
                           else "new" if (paksha == "krishna" and tithi_num == 15)
                           else None),
            "good_time": {"abhijit": abhijit},
            "avoid_times": {"rahu_kalam": rahu, "yamaganda": yama,
                            "gulika_kalam": gulika_k},
            "masa": masa_name, "masa_adhika": bool(masa_cache.get("adhika")),
            "tamil_month": tamil_month, "tamil_day": tamil_day,
            "festivals": [],
            "_jd_sunrise": eval_jd, "_jd_sunset": set_jd, "_jd_noon": jd_noon,
        })

    _attach_festivals(days, tradition, tz, lat, lng, ayanamsa)

    for day in days:  # strip internals
        for k in ("_jd_sunrise", "_jd_sunset", "_jd_noon"):
            day.pop(k, None)

    masas_in_month: list[str] = []
    for day in days:
        label = ("Adhika " + day["masa"]) if day["masa_adhika"] else day["masa"]
        if label not in masas_in_month:
            masas_in_month.append(label)

    mid_jd = julian_day_ut(datetime(year, month, 15, tzinfo=timezone.utc))
    scheme = "tamil_solar" if tradition == "tamil" else "telugu_lunar"
    return {
        "schema": "PanchangaMonthV1",
        "year": year, "month": month,
        "tradition": tradition, "location": loc["label"], "timezone": loc["tz"],
        "samvatsara": samvatsara(mid_jd, scheme)["name"],
        "masas": masas_in_month,
        "days": days,
        "note": ("Tithi and nakshatra are as prevailing at LOCAL sunrise "
                 f"({loc['label']}); Shivaratri/Janmashtami follow the local "
                 "midnight tithi and Deepavali the local sunset amavasya — so "
                 "dates can differ by a day between countries, by design."),
    }


def _attach_festivals(days: list[dict], tradition: str, tz: ZoneInfo,
                      lat: float, lng: float, ayanamsa: str) -> None:
    solar_hits: dict[str, int] = {}

    for i, day in enumerate(days):
        for f in FESTIVALS:
            if tradition not in f["regions"]:
                continue
            hit = False
            if f["kind"] == "lunar":
                obs = f.get("observance", "sunrise")
                jd_check = day["_jd_sunrise"]
                if obs == "midnight":
                    jd_check = day["_jd_noon"] + 0.5   # local midnight after this day
                elif obs == "sunset" and day["_jd_sunset"]:
                    jd_check = day["_jd_sunset"]
                pos = sidereal_positions(jd_check, ayanamsa=ayanamsa)
                elong = (pos["moon"]["lon"] - pos["sun"]["lon"]) % 360.0
                paksha, num, _ = _tithi_parts(elong)
                if paksha == f["paksha"] and num == f["tithi"] and day["masa"] == f["masa"] \
                        and not day["masa_adhika"]:
                    # Udaya rule: the FIRST matching civil day takes the festival.
                    already = any(f["key"] in [x["key"] for x in prev["festivals"]]
                                  for prev in days[:i])
                    hit = not already
            elif f["kind"] == "solar":
                # The civil day containing the ingress into f["sign"].
                try:
                    sk = sankranti(day["_jd_sunrise"] - 1.0, direction=1, ayanamsa=ayanamsa)
                    ingress_local = jd_to_utc(sk["jd"]).astimezone(tz).date()
                    if (ingress_local.isoformat() == day["date"]
                            and int(sk.get("sign_entered", -1) if isinstance(sk.get("sign_entered"), int)
                                    else -1) in (f["sign"], -1)):
                        # verify sign by sun position shortly after ingress
                        s_pos = sidereal_positions(sk["jd"] + 0.01, ayanamsa=ayanamsa)
                        if int(s_pos["sun"]["lon"] // 30) == f["sign"]:
                            hit = True
                            solar_hits[f["key"]] = i
                except Exception:
                    pass
            if hit:
                day["festivals"].append({
                    "key": f["key"],
                    "name": f["names"].get(tradition, f["names"]["en"]),
                    "name_en": f["names"]["en"],
                })

    # Derived festivals (offsets from a solar hit; Varalakshmi Friday rule).
    for f in FESTIVALS:
        if tradition not in f["regions"]:
            continue
        if f["kind"] == "derived" and f["base"] in solar_hits:
            j = solar_hits[f["base"]] + f["offset"]
            if 0 <= j < len(days):
                days[j]["festivals"].append({"key": f["key"],
                                             "name": f["names"].get(tradition, f["names"]["en"]),
                                             "name_en": f["names"]["en"]})
        if f["kind"] == "derived_varalakshmi":
            # Last Friday strictly before Shravana Purnima.
            purnima_i = next((i for i, dy in enumerate(days)
                              if dy["masa"] == "Shravana" and dy["tithi"]["paksha"] == "shukla"
                              and dy["tithi"]["number"] == 15), None)
            if purnima_i is not None:
                for j in range(purnima_i - 1, -1, -1):
                    if days[j]["weekday"] == 4:  # Friday
                        days[j]["festivals"].append({
                            "key": f["key"],
                            "name": f["names"].get(tradition, f["names"]["en"]),
                            "name_en": f["names"]["en"]})
                        break

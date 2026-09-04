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
from .constants import NAKSHATRAS, TITHIS, VARAS, YOGAS_27, karana_name
from .ephemeris import jd_to_utc, julian_day_ut, sidereal_positions, sunrise_sunset
from .events import masa as amanta_masa
from .events import karana_end, nakshatra_end, sankranti, tithi_end, yoga_end
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
    "ca": {"tz": "America/Toronto", "lat": 43.6532, "lng": -79.3832, "label": "Canada"},
    "gulf": {"tz": "Asia/Dubai", "lat": 25.2048, "lng": 55.2708, "label": "Gulf (UAE)"},
    "sg": {"tz": "Asia/Singapore", "lat": 1.3521, "lng": 103.8198, "label": "Singapore"},
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


def _clear_of(good: tuple, bad: tuple) -> tuple | None:
    """Return the largest sub-interval of `good` that does NOT overlap `bad`
    (both (start, end) datetimes), or None if `bad` covers `good` entirely.
    Used to void/trim Abhijit muhurta where it coincides with Rahu kalam."""
    g0, g1 = good
    b0, b1 = bad
    if b1 <= g0 or b0 >= g1:      # no overlap
        return good
    pieces = []
    if b0 > g0:                    # clear stretch before the bad window
        pieces.append((g0, min(g1, b0)))
    if b1 < g1:                    # clear stretch after the bad window
        pieces.append((max(g0, b1), g1))
    pieces = [p for p in pieces if p[1] > p[0]]
    if not pieces:
        return None
    return max(pieces, key=lambda p: p[1] - p[0])


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

        # Yoga + karana (the remaining panchanga limbs — for the day detail view).
        yoga_idx = min(26, int(((pos["sun"]["lon"] + pos["moon"]["lon"]) % 360.0)
                               // (360.0 / 27.0)))
        karana_idx = min(59, int(elong // 6.0))
        y_end = k_end = None
        try:
            y_end = _local(yoga_end(eval_jd, ayanamsa=ayanamsa)["ends_jd"], tz).strftime("%H:%M")
        except Exception:
            pass
        try:
            k_end = _local(karana_end(eval_jd, ayanamsa=ayanamsa)["ends_jd"], tz).strftime("%H:%M")
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
        abhijit_void = False  # Abhijit voided by Rahu kalam overlap
        if rise_jd is not None and set_jd is not None:
            try:
                _, nxt = sunrise_sunset(jd_noon + 1.0, lat, lng)
                velas = kala_velas(rise_jd, set_jd, nxt or set_jd + 0.5, d.weekday())

                def _dt(iso: str) -> datetime:
                    return datetime.fromisoformat(iso).astimezone(tz)

                def _win(w: dict) -> str:
                    return f"{_dt(w['start_utc']).strftime('%H:%M')}–{_dt(w['end_utc']).strftime('%H:%M')}"

                rahu = _win(velas["rahu_kala"])
                yama = _win(velas["yamaganda"])
                gulika_k = _win(velas["gulika_kala"])
                day_len = set_jd - rise_jd
                ab_s = _local(rise_jd + 7.0 * day_len / 15.0, tz)
                ab_e = _local(rise_jd + 8.0 * day_len / 15.0, tz)
                # Abhijit muhurta is classically VOID when it coincides with Rahu
                # kalam — never present an auspicious window that sits inside the
                # day's inauspicious one. Trim Abhijit to the part clear of Rahu
                # kalam; if nothing meaningful remains (< 6 min), it is void today.
                r_s = _dt(velas["rahu_kala"]["start_utc"])
                r_e = _dt(velas["rahu_kala"]["end_utc"])
                clear = _clear_of((ab_s, ab_e), (r_s, r_e))
                if clear is None or (clear[1] - clear[0]) < timedelta(minutes=6):
                    abhijit = None
                    abhijit_void = True
                else:
                    abhijit = (clear[0].strftime("%H:%M") + "–"
                               + clear[1].strftime("%H:%M"))
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
            "yoga": {"name": YOGAS_27[yoga_idx], "ends": y_end},
            "karana": {"name": karana_name(karana_idx), "ends": k_end},
            "moon_phase": ("full" if (paksha == "shukla" and tithi_num == 15)
                           else "new" if (paksha == "krishna" and tithi_num == 15)
                           else None),
            "good_time": {"abhijit": abhijit, "abhijit_void": abhijit_void},
            "avoid_times": {"rahu_kalam": rahu, "yamaganda": yama,
                            "gulika_kalam": gulika_k},
            "masa": masa_name, "masa_adhika": bool(masa_cache.get("adhika")),
            "tamil_month": tamil_month, "tamil_day": tamil_day,
            "festivals": [],
            "_jd_sunrise": eval_jd, "_jd_sunset": set_jd, "_jd_noon": jd_noon,
        })

    _attach_festivals(days, tradition, tz, lat, lng, ayanamsa)
    for day in days:
        localize_day(day, tradition)

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


# ── Native-script panchanga vocabulary per tradition ────────────────────────
# Tithi stems indexed 1-15 (shukla/krishna share stems; 15 = Purnima/Amavasya
# handled separately), nakshatras 0-26, masas by amanta name, varas Mon-first.

TITHI_LOCAL: dict[str, list[str]] = {
    "telugu": ["పాడ్యమి", "విదియ", "తదియ", "చవితి", "పంచమి", "షష్ఠి", "సప్తమి",
               "అష్టమి", "నవమి", "దశమి", "ఏకాదశి", "ద్వాదశి", "త్రయోదశి", "చతుర్దశి"],
    "tamil": ["பிரதமை", "துவிதியை", "திருதியை", "சதுர்த்தி", "பஞ்சமி", "சஷ்டி",
              "சப்தமி", "அஷ்டமி", "நவமி", "தசமி", "ஏகாதசி", "துவாதசி",
              "திரயோதசி", "சதுர்த்தசி"],
    "kannada": ["ಪಾಡ್ಯ", "ಬಿದಿಗೆ", "ತದಿಗೆ", "ಚೌತಿ", "ಪಂಚಮಿ", "ಷಷ್ಠಿ", "ಸಪ್ತಮಿ",
                "ಅಷ್ಟಮಿ", "ನವಮಿ", "ದಶಮಿ", "ಏಕಾದಶಿ", "ದ್ವಾದಶಿ", "ತ್ರಯೋದಶಿ", "ಚತುರ್ದಶಿ"],
    "hindi": ["प्रतिपदा", "द्वितीया", "तृतीया", "चतुर्थी", "पंचमी", "षष्ठी", "सप्तमी",
              "अष्टमी", "नवमी", "दशमी", "एकादशी", "द्वादशी", "त्रयोदशी", "चतुर्दशी"],
}
FULL_NEW_LOCAL = {
    "telugu": {"full": "పౌర్ణమి", "new": "అమావాస్య", "shukla": "శుక్ల", "krishna": "బహుళ"},
    "tamil": {"full": "பௌர்ணமி", "new": "அமாவாசை", "shukla": "வளர்பிறை", "krishna": "தேய்பிறை"},
    "kannada": {"full": "ಹುಣ್ಣಿಮೆ", "new": "ಅಮಾವಾಸ್ಯೆ", "shukla": "ಶುಕ್ಲ", "krishna": "ಕೃಷ್ಣ"},
    "hindi": {"full": "पूर्णिमा", "new": "अमावस्या", "shukla": "शुक्ल", "krishna": "कृष्ण"},
}
NAKSHATRA_LOCAL: dict[str, list[str]] = {
    "telugu": ["అశ్విని", "భరణి", "కృత్తిక", "రోహిణి", "మృగశిర", "ఆరుద్ర", "పునర్వసు",
               "పుష్యమి", "ఆశ్లేష", "మఖ", "పుబ్బ", "ఉత్తర", "హస్త", "చిత్త", "స్వాతి",
               "విశాఖ", "అనూరాధ", "జ్యేష్ఠ", "మూల", "పూర్వాషాఢ", "ఉత్తరాషాఢ",
               "శ్రవణం", "ధనిష్ఠ", "శతభిషం", "పూర్వాభాద్ర", "ఉత్తరాభాద్ర", "రేవతి"],
    "tamil": ["அசுவினி", "பரணி", "கார்த்திகை", "ரோகிணி", "மிருகசீரிடம்", "திருவாதிரை",
              "புனர்பூசம்", "பூசம்", "ஆயில்யம்", "மகம்", "பூரம்", "உத்திரம்", "அஸ்தம்",
              "சித்திரை", "சுவாதி", "விசாகம்", "அனுஷம்", "கேட்டை", "மூலம்", "பூராடம்",
              "உத்திராடம்", "திருவோணம்", "அவிட்டம்", "சதயம்", "பூரட்டாதி",
              "உத்திரட்டாதி", "ரேவதி"],
    "kannada": ["ಅಶ್ವಿನಿ", "ಭರಣಿ", "ಕೃತ್ತಿಕಾ", "ರೋಹಿಣಿ", "ಮೃಗಶಿರ", "ಆರ್ದ್ರಾ", "ಪುನರ್ವಸು",
                "ಪುಷ್ಯ", "ಆಶ್ಲೇಷಾ", "ಮಘಾ", "ಪುಬ್ಬ", "ಉತ್ತರಾ", "ಹಸ್ತ", "ಚಿತ್ರಾ", "ಸ್ವಾತಿ",
                "ವಿಶಾಖಾ", "ಅನುರಾಧಾ", "ಜ್ಯೇಷ್ಠಾ", "ಮೂಲಾ", "ಪೂರ್ವಾಷಾಢ", "ಉತ್ತರಾಷಾಢ",
                "ಶ್ರವಣ", "ಧನಿಷ್ಠಾ", "ಶತಭಿಷಾ", "ಪೂರ್ವಾಭಾದ್ರ", "ಉತ್ತರಾಭಾದ್ರ", "ರೇವತಿ"],
    "hindi": ["अश्विनी", "भरणी", "कृत्तिका", "रोहिणी", "मृगशिरा", "आर्द्रा", "पुनर्वसु",
              "पुष्य", "आश्लेषा", "मघा", "पूर्वा फाल्गुनी", "उत्तरा फाल्गुनी", "हस्त",
              "चित्रा", "स्वाती", "विशाखा", "अनुराधा", "ज्येष्ठा", "मूल", "पूर्वाषाढ़ा",
              "उत्तराषाढ़ा", "श्रवण", "धनिष्ठा", "शतभिषा", "पूर्वाभाद्रपदा",
              "उत्तराभाद्रपदा", "रेवती"],
}
MASA_LOCAL: dict[str, dict[str, str]] = {
    "telugu": {"Chaitra": "చైత్రం", "Vaishakha": "వైశాఖం", "Jyeshtha": "జ్యేష్ఠం",
               "Ashadha": "ఆషాఢం", "Shravana": "శ్రావణం", "Bhadrapada": "భాద్రపదం",
               "Ashwina": "ఆశ్వయుజం", "Kartika": "కార్తీకం", "Margashirsha": "మార్గశిరం",
               "Pausha": "పుష్యం", "Magha": "మాఘం", "Phalguna": "ఫాల్గుణం"},
    "kannada": {"Chaitra": "ಚೈತ್ರ", "Vaishakha": "ವೈಶಾಖ", "Jyeshtha": "ಜ್ಯೇಷ್ಠ",
                "Ashadha": "ಆಷಾಢ", "Shravana": "ಶ್ರಾವಣ", "Bhadrapada": "ಭಾದ್ರಪದ",
                "Ashwina": "ಆಶ್ವಯುಜ", "Kartika": "ಕಾರ್ತೀಕ", "Margashirsha": "ಮಾರ್ಗಶಿರ",
                "Pausha": "ಪುಷ್ಯ", "Magha": "ಮಾಘ", "Phalguna": "ಫಾಲ್ಗುಣ"},
    "hindi": {"Chaitra": "चैत्र", "Vaishakha": "वैशाख", "Jyeshtha": "ज्येष्ठ",
              "Ashadha": "आषाढ़", "Shravana": "श्रावण", "Bhadrapada": "भाद्रपद",
              "Ashwina": "आश्विन", "Kartika": "कार्तिक", "Margashirsha": "मार्गशीर्ष",
              "Pausha": "पौष", "Magha": "माघ", "Phalguna": "फाल्गुन"},
    "tamil": {},  # Tamil uses SOLAR months — TAMIL_MONTHS_LOCAL below.
}
TAMIL_MONTHS_LOCAL = ["சித்திரை", "வைகாசி", "ஆனி", "ஆடி", "ஆவணி", "புரட்டாசி",
                      "ஐப்பசி", "கார்த்திகை", "மார்கழி", "தை", "மாசி", "பங்குனி"]
VARA_LOCAL: dict[str, list[str]] = {  # Mon-first, matching constants.VARAS
    "telugu": ["సోమ", "మంగళ", "బుధ", "గురు", "శుక్ర", "శని", "ఆది"],
    "tamil": ["திங்கள்", "செவ்வாய்", "புதன்", "வியாழன்", "வெள்ளி", "சனி", "ஞாயிறு"],
    "kannada": ["ಸೋಮ", "ಮಂಗಳ", "ಬುಧ", "ಗುರು", "ಶುಕ್ರ", "ಶನಿ", "ಭಾನು"],
    "hindi": ["सोम", "मंगल", "बुध", "गुरु", "शुक्र", "शनि", "रवि"],
}


def localize_day(day: dict, tradition: str) -> dict:
    """Attach native-script names to a computed day (non-destructive extras)."""
    fn = FULL_NEW_LOCAL.get(tradition, FULL_NEW_LOCAL["telugu"])
    num, paksha = day["tithi"]["number"], day["tithi"]["paksha"]
    if num == 15:
        tithi_local = fn["full"] if paksha == "shukla" else fn["new"]
    else:
        tithi_local = f"{fn[paksha]} {TITHI_LOCAL[tradition][num - 1]}"
    nak_idx = NAKSHATRAS.index(day["nakshatra"]["name"]) if day["nakshatra"]["name"] in NAKSHATRAS else None
    day["tithi"]["local"] = tithi_local
    if day["tithi"].get("next"):
        # localize the "then" name too (strip paksha word for brevity)
        nxt = day["tithi"]["next"]
        stem = nxt.split(" ", 1)[-1]
        try:
            i = ["Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi",
                 "Saptami", "Ashtami", "Navami", "Dashami", "Ekadashi", "Dwadashi",
                 "Trayodashi", "Chaturdashi"].index(stem)
            day["tithi"]["next_local"] = TITHI_LOCAL[tradition][i]
        except ValueError:
            day["tithi"]["next_local"] = (fn["full"] if nxt == "Purnima"
                                          else fn["new"] if nxt == "Amavasya" else nxt)
    if nak_idx is not None:
        day["nakshatra"]["local"] = NAKSHATRA_LOCAL[tradition][nak_idx]
    day["vara_local"] = VARA_LOCAL[tradition][day["weekday"]]
    if tradition == "tamil":
        ti = TAMIL_MONTHS.index(day["tamil_month"])
        day["masa_local"] = TAMIL_MONTHS_LOCAL[ti]
    else:
        day["masa_local"] = MASA_LOCAL[tradition].get(day["masa"], day["masa"])
    return day

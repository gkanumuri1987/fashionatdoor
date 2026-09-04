"""Localized presentation strings for the personal Jyothishyam (forecast).

The forecast ENGINE (forecast.py) stays language-agnostic — this is a pure
presentation lookup so the daily + weekly forecast renders in the user's
language (English / Telugu / Hindi). `en` matches the engine's own wording, so
English output is unchanged; `te`/`hi` are freshly written, everyday-language
translations. Every accessor falls back to `en`, so a missing key never breaks
a forecast.
"""

from __future__ import annotations

# Weekday (0=Mon … 6=Sun) → what the day's planet favours.
AFFAIRS = {
    0: {"en": "emotions, mother, water, liquids, travel, the mind",
        "te": "భావోద్వేగాలు, తల్లి, నీరు, ద్రవాలు, ప్రయాణం, మనసు",
        "hi": "भावनाएँ, माता, जल, तरल, यात्रा, मन"},
    1: {"en": "courage, land & property, disputes, surgery, siblings",
        "te": "ధైర్యం, భూమి & ఆస్తి, వివాదాలు, శస్త్రచికిత్స, తోబుట్టువులు",
        "hi": "साहस, भूमि व संपत्ति, विवाद, शल्यक्रिया, भाई-बहन"},
    2: {"en": "study, communication, trade, writing, accounts",
        "te": "చదువు, సంభాషణ, వ్యాపారం, రచన, లెక్కలు",
        "hi": "अध्ययन, संवाद, व्यापार, लेखन, लेखा"},
    3: {"en": "wisdom, wealth, marriage, dharma, teachers, children",
        "te": "జ్ఞానం, సంపద, వివాహం, ధర్మం, గురువులు, పిల్లలు",
        "hi": "ज्ञान, धन, विवाह, धर्म, गुरु, संतान"},
    4: {"en": "love, arts, comforts, vehicles, beauty, partnerships",
        "te": "ప్రేమ, కళలు, సౌకర్యాలు, వాహనాలు, సౌందర్యం, భాగస్వామ్యాలు",
        "hi": "प्रेम, कला, सुख-सुविधा, वाहन, सौंदर्य, साझेदारी"},
    5: {"en": "labour, discipline, service, iron, elders, karma",
        "te": "శ్రమ, క్రమశిక్షణ, సేవ, ఇనుము, పెద్దలు, కర్మ",
        "hi": "श्रम, अनुशासन, सेवा, लोहा, बुज़ुर्ग, कर्म"},
    6: {"en": "authority, health, father, government, self-standing",
        "te": "అధికారం, ఆరోగ్యం, తండ్రి, ప్రభుత్వం, ఆత్మగౌరవం",
        "hi": "अधिकार, स्वास्थ्य, पिता, सरकार, आत्म-प्रतिष्ठा"},
}

# Tithi group → its nature note.
TITHI_NOTE = {
    "Nanda": {"en": "joyful — celebrations, prosperity",
              "te": "ఆనందకరం — వేడుకలు, శ్రేయస్సు",
              "hi": "आनंददायी — उत्सव, समृद्धि"},
    "Bhadra": {"en": "strong & healthy — steady work, foundations",
               "te": "బలం & ఆరోగ్యం — స్థిరమైన పని, పునాదులు",
               "hi": "बल व स्वास्थ्य — स्थिर कार्य, नींव"},
    "Jaya": {"en": "victorious — competition, effort, bold moves",
             "te": "విజయకరం — పోటీ, ప్రయత్నం, ధైర్యమైన చర్యలు",
             "hi": "विजयी — प्रतिस्पर्धा, प्रयास, साहसिक कदम"},
    "Rikta": {"en": "empty — avoid new & auspicious starts today",
              "te": "శూన్యం — నేడు కొత్త & శుభ ప్రారంభాలు మానండి",
              "hi": "रिक्त — आज नए व शुभ आरंभ टालें"},
    "Purna": {"en": "full — all-round auspicious, completions",
              "te": "పూర్ణం — అన్నివిధాలా శుభం, పూర్తులు",
              "hi": "पूर्ण — सर्वत्र शुभ, समापन"},
}

# Nakshatra activity class → what it supports.
CLASS_NOTE = {
    "chara": {"en": "movement, travel, vehicles, change",
              "te": "కదలిక, ప్రయాణం, వాహనాలు, మార్పు",
              "hi": "गति, यात्रा, वाहन, परिवर्तन"},
    "sthira": {"en": "permanent things — building, planting, savings",
               "te": "శాశ్వత విషయాలు — నిర్మాణం, నాటడం, పొదుపు",
               "hi": "स्थायी कार्य — निर्माण, रोपण, बचत"},
    "ugra": {"en": "bold/forceful acts, confrontation, demolition",
             "te": "ధైర్య/బలవంతపు చర్యలు, ఘర్షణ, కూల్చివేత",
             "hi": "साहसी/प्रबल कार्य, टकराव, ध्वंस"},
    "mishra": {"en": "mixed acts, fire rituals, routine",
               "te": "మిశ్రమ చర్యలు, అగ్ని కర్మలు, దినచర్య",
               "hi": "मिश्रित कार्य, अग्नि कर्म, नित्यक्रम"},
    "kshipra": {"en": "quick tasks, trade, arts, medicine, learning",
                "te": "త్వరిత పనులు, వ్యాపారం, కళలు, వైద్యం, నేర్చుకోవడం",
                "hi": "त्वरित कार्य, व्यापार, कला, चिकित्सा, अध्ययन"},
    "mridu": {"en": "gentle acts — arts, romance, friendship, study",
              "te": "సున్నితమైన చర్యలు — కళలు, ప్రేమ, స్నేహం, చదువు",
              "hi": "कोमल कार्य — कला, प्रेम, मित्रता, अध्ययन"},
    "tikshna": {"en": "sharp acts — mantra, discipline, breaking ties",
                "te": "తీక్ష్ణ చర్యలు — మంత్రం, క్రమశిక్షణ, బంధాలు తెంచడం",
                "hi": "तीक्ष्ण कार्य — मंत्र, अनुशासन, संबंध-विच्छेद"},
}

# Tarabala name → its note.
TARA_NOTE = {
    "Janma": {"en": "guard your body & health today",
              "te": "నేడు మీ శరీరం & ఆరోగ్యం జాగ్రత్త",
              "hi": "आज अपने शरीर व स्वास्थ्य का ध्यान रखें"},
    "Sampat": {"en": "wealth & gains favoured",
               "te": "సంపద & లాభాలకు అనుకూలం",
               "hi": "धन व लाभ के अनुकूल"},
    "Vipat": {"en": "risk — postpone the important",
              "te": "ప్రమాదం — ముఖ్యమైనవి వాయిదా వేయండి",
              "hi": "जोखिम — महत्वपूर्ण कार्य टालें"},
    "Kshema": {"en": "well-being & ease",
               "te": "క్షేమం & సౌలభ్యం",
               "hi": "कल्याण व सुगमता"},
    "Pratyak": {"en": "obstacles — expect friction",
                "te": "అడ్డంకులు — ఘర్షణ ఆశించండి",
                "hi": "बाधाएँ — टकराव संभव"},
    "Sadhaka": {"en": "accomplishment — push your goals",
                "te": "సాధన — మీ లక్ష్యాలను ముందుకు నెట్టండి",
                "hi": "सिद्धि — अपने लक्ष्य आगे बढ़ाएँ"},
    "Vadha": {"en": "harmful — avoid new & risky acts",
              "te": "హానికరం — కొత్త & ప్రమాదకర చర్యలు మానండి",
              "hi": "हानिकारक — नए व जोखिमपूर्ण कार्य टालें"},
    "Mitra": {"en": "friendly — support flows to you",
              "te": "మిత్రత్వం — మీకు మద్దతు లభిస్తుంది",
              "hi": "मैत्रीपूर्ण — आपको सहयोग मिलेगा"},
    "Atimitra": {"en": "very friendly — an excellent day",
                 "te": "అతిమిత్రత్వం — అద్భుతమైన రోజు",
                 "hi": "अति मैत्रीपूर्ण — उत्तम दिन"},
}

# Interest key → the life area (house label) it reads.
HOUSE_LABEL = {
    "career": {"en": "career, work, reputation",
               "te": "వృత్తి, పని, కీర్తి", "hi": "करियर, कार्य, प्रतिष्ठा"},
    "relationship": {"en": "partnership, marriage, love",
                     "te": "భాగస్వామ్యం, వివాహం, ప్రేమ", "hi": "साझेदारी, विवाह, प्रेम"},
    "health": {"en": "vitality, body, energy",
               "te": "జీవశక్తి, శరీరం, శక్తి", "hi": "जीवनशक्ति, शरीर, ऊर्जा"},
    "finance": {"en": "wealth, savings, family resources",
                "te": "సంపద, పొదుపు, కుటుంబ వనరులు", "hi": "धन, बचत, पारिवारिक संसाधन"},
    "education": {"en": "learning, creativity, children",
                  "te": "విద్య, సృజనాత్మకత, పిల్లలు", "hi": "शिक्षा, सृजनशीलता, संतान"},
    "spiritual": {"en": "dharma, fortune, higher wisdom",
                  "te": "ధర్మం, అదృష్టం, ఉన్నత జ్ఞానం", "hi": "धर्म, भाग्य, उच्च ज्ञान"},
}

# Sentence templates ({placeholders} filled by the engine).
TEMPLATES = {
    "focus_live": {
        "en": "A graha transits your {house}th ({label}) today — a live day for it.",
        "te": "నేడు మీ {house}వ ఇంటిపై ({label}) ఒక గ్రహం సంచరిస్తోంది — దీనికి చురుకైన రోజు.",
        "hi": "आज आपके {house}वें भाव ({label}) पर एक ग्रह गोचर कर रहा है — इसके लिए सक्रिय दिन।"},
    "focus_quiet": {
        "en": "Your {house}th of {label} is quiet today; steady progress.",
        "te": "{label} సంబంధించిన మీ {house}వ ఇల్లు నేడు ప్రశాంతం; స్థిరమైన పురోగతి.",
        "hi": "{label} का आपका {house}वाँ भाव आज शांत है; स्थिर प्रगति।"},
    "caution_rahu": {
        "en": "Rahu kalam {win} — start nothing important in this window.",
        "te": "రాహు కాలం {win} — ఈ సమయంలో ముఖ్యమైనది ఏదీ ప్రారంభించవద్దు.",
        "hi": "राहु काल {win} — इस समय कोई महत्वपूर्ण कार्य आरंभ न करें।"},
    "caution_rikta": {
        "en": "{note} — hold off launches; good for clearing & endings.",
        "te": "{note} — కొత్త ప్రారంభాలు వాయిదా వేయండి; శుభ్రపరచడం & ముగింపులకు మంచిది.",
        "hi": "{note} — नई शुरुआत टालें; सफ़ाई व समापन के लिए अच्छा।"},
    "caution_tara": {
        "en": "Tarabala {name}: {note}.",
        "te": "తారాబలం {name}: {note}.",
        "hi": "ताराबल {name}: {note}।"},
    "caution_moon": {
        "en": "Moon is not supportive of your sign today — keep plans light.",
        "te": "నేడు చంద్రుడు మీ రాశికి అనుకూలం కాదు — ప్రణాళికలు తేలికగా ఉంచండి.",
        "hi": "आज चंद्रमा आपकी राशि के अनुकूल नहीं — योजनाएँ हल्की रखें।"},
    "caution_panchaka": {
        "en": "Panchaka ({nak}) — avoid roofing, travel south, buying fuel/metal.",
        "te": "పంచక ({nak}) — పైకప్పు వేయడం, దక్షిణ దిశ ప్రయాణం, ఇంధనం/లోహం కొనడం మానండి.",
        "hi": "पंचक ({nak}) — छत डालना, दक्षिण यात्रा, ईंधन/धातु खरीदना टालें।"},
    "caution_yoga": {
        "en": "{yoga} yoga — an inauspicious combination; be measured.",
        "te": "{yoga} యోగం — అశుభ కలయిక; జాగ్రత్తగా ఉండండి.",
        "hi": "{yoga} योग — अशुभ संयोग; संयमित रहें।"},
    "note_footer": {
        "en": "Computed from live panchanga (tithi, nakshatra, yoga, vara) read "
              "against your birth Moon and running dasha — not invented.",
        "te": "ప్రత్యక్ష పంచాంగం (తిథి, నక్షత్రం, యోగం, వారం) మీ జన్మ చంద్రుడు & "
              "నడుస్తున్న దశతో పోల్చి లెక్కించబడింది — ఊహ కాదు.",
        "hi": "प्रत्यक्ष पंचांग (तिथि, नक्षत्र, योग, वार) को आपके जन्म चंद्रमा व "
              "चल रही दशा के सापेक्ष पढ़कर गणना — कल्पित नहीं।"},
}


def _pick(entry: dict | None, language: str) -> str | None:
    if not entry:
        return None
    return entry.get(language) or entry.get("en")


def affairs(weekday: int, language: str) -> str:
    return _pick(AFFAIRS.get(weekday), language) or ""


def tithi_note(group: str, language: str) -> str:
    return _pick(TITHI_NOTE.get(group), language) or ""


def class_note(klass: str, language: str) -> str:
    return _pick(CLASS_NOTE.get(klass), language) or ""


def tara_note(name: str, language: str) -> str:
    return _pick(TARA_NOTE.get(name), language) or ""


def house_label(interest: str, language: str) -> str:
    return _pick(HOUSE_LABEL.get(interest), language) or ""


def tmpl(key: str, language: str, **kw) -> str:
    s = _pick(TEMPLATES.get(key), language) or ""
    try:
        return s.format(**kw)
    except (KeyError, IndexError):
        return s


# ── Panchanga NAMES (reuse festivals' native-script tables for nak/tithi/vara;
#    author the small jyotish-specific sets here). Language "en" keeps the
#    romanized names the engine already produces. ────────────────────────────
_TRAD = {"te": "telugu", "hi": "hindi"}   # language → festivals tradition key

TARA_NAME = {
    "Janma": {"te": "జన్మ", "hi": "जन्म"}, "Sampat": {"te": "సంపత్", "hi": "संपत्"},
    "Vipat": {"te": "విపత్", "hi": "विपत्"}, "Kshema": {"te": "క్షేమ", "hi": "क्षेम"},
    "Pratyak": {"te": "ప్రత్యక్", "hi": "प्रत्यक्"}, "Sadhaka": {"te": "సాధక", "hi": "साधक"},
    "Vadha": {"te": "వధ", "hi": "वध"}, "Mitra": {"te": "మిత్ర", "hi": "मित्र"},
    "Atimitra": {"te": "అతిమిత్ర", "hi": "अतिमित्र"},
}
GROUP_NAME = {
    "Nanda": {"te": "నంద", "hi": "नंदा"}, "Bhadra": {"te": "భద్ర", "hi": "भद्रा"},
    "Jaya": {"te": "జయ", "hi": "जया"}, "Rikta": {"te": "రిక్త", "hi": "रिक्ता"},
    "Purna": {"te": "పూర్ణ", "hi": "पूर्णा"},
}
CLASS_NAME = {
    "chara": {"te": "చర", "hi": "चर"}, "sthira": {"te": "స్థిర", "hi": "स्थिर"},
    "ugra": {"te": "ఉగ్ర", "hi": "उग्र"}, "mishra": {"te": "మిశ్ర", "hi": "मिश्र"},
    "kshipra": {"te": "క్షిప్ర", "hi": "क्षिप्र"}, "mridu": {"te": "మృదు", "hi": "मृदु"},
    "tikshna": {"te": "తీక్ష్ణ", "hi": "तीक्ष्ण"},
}
DEITY = {   # weekday 0-6 → "planet / deity"
    0: {"te": "చంద్ర / శివుడు", "hi": "चंद्र / शिव"},
    1: {"te": "మంగళ / హనుమాన్", "hi": "मंगल / हनुमान"},
    2: {"te": "బుధ / విష్ణువు", "hi": "बुध / विष्णु"},
    3: {"te": "గురు / దక్షిణామూర్తి", "hi": "गुरु / दक्षिणामूर्ति"},
    4: {"te": "శుక్ర / లక్ష్మి", "hi": "शुक्र / लक्ष्मी"},
    5: {"te": "శని / హనుమాన్", "hi": "शनि / हनुमान"},
    6: {"te": "సూర్య / రాముడు", "hi": "सूर्य / राम"},
}


def _pick2(entry: dict | None, language: str, fallback: str) -> str:
    if not entry:
        return fallback
    return entry.get(language) or fallback


def nak_name(en_name: str, index: int, language: str) -> str:
    trad = _TRAD.get(language)
    if trad and isinstance(index, int) and 0 <= index < 27:
        try:
            from . import festivals as _fest
            return _fest.NAKSHATRA_LOCAL[trad][index]
        except Exception:
            pass
    return en_name


def tithi_display(paksha: str, number: int, en_name: str, language: str) -> str:
    trad = _TRAD.get(language)
    if not trad:
        return en_name
    try:
        from . import festivals as _fest
        fn = _fest.FULL_NEW_LOCAL[trad]
        if number == 15:
            return fn["full"] if paksha == "shukla" else fn["new"]
        return f"{fn[paksha]} {_fest.TITHI_LOCAL[trad][number - 1]}"
    except Exception:
        return en_name


def vara_display(weekday: int, en_name: str, language: str) -> str:
    trad = _TRAD.get(language)
    if trad:
        try:
            from . import festivals as _fest
            return _fest.VARA_LOCAL[trad][weekday]
        except Exception:
            pass
    return en_name


def deity_display(weekday: int, en_name: str, language: str) -> str:
    return _pick2(DEITY.get(weekday), language, en_name)


def tara_display(name: str, language: str) -> str:
    return _pick2(TARA_NAME.get(name), language, name)


def group_display(group: str, language: str) -> str:
    return _pick2(GROUP_NAME.get(group), language, group)


def class_display(klass: str, language: str) -> str:
    return _pick2(CLASS_NAME.get(klass), language, klass)


# ── Dasha-period remedy (weekly summary) — deity / practice / rationale ──────
PERIOD = {
    "sun": {
        "deity": {"te": "సూర్య / రాముడు", "hi": "सूर्य / राम"},
        "practice": {"te": "సూర్యోదయ సమయంలో సూర్యునికి నీరు అర్పించండి; ఆదిత్య హృదయం పఠించండి.",
                     "hi": "सूर्योदय के समय सूर्य को जल अर्पित करें; आदित्य हृदय का पाठ करें।"},
        "rationale": {"te": "సూర్యోదయానికి ముందు లేచి ఉదయపు వెలుతురు తీసుకోవడం మీ శరీర గడియారాన్ని సరిచేస్తుంది — మనఃస్థితి, శక్తి, విటమిన్-డి పెరుగుతాయి. స్తోత్ర పఠనం నెమ్మదైన శ్వాసతో ఒత్తిడిని తగ్గిస్తుంది; స్థిరమైన ఉదయపు దినచర్య క్రమశిక్షణను, ఆత్మవిశ్వాసాన్ని బలపరుస్తుంది.",
                      "hi": "सूर्योदय से पहले उठकर सुबह की रोशनी लेना आपकी सर्केडियन घड़ी को संतुलित करता है — मनोदशा, ऊर्जा व विटामिन-डी बढ़ते हैं। स्तोत्र-पाठ धीमी साँस से तनाव घटाता है; स्थिर सुबह की दिनचर्या अनुशासन व आत्मविश्वास को मज़बूत करती है।"}},
    "moon": {
        "deity": {"te": "చంద్ర / శివుడు", "hi": "चंद्र / शिव"},
        "practice": {"te": "సోమవారాల్లో శివునికి తెల్ల పూలు అర్పించండి; ఓం నమః శివాయ జపించండి.",
                     "hi": "सोमवार को शिव को श्वेत पुष्प अर्पित करें; ॐ नमः शिवाय जपें।"},
        "rationale": {"te": "లయబద్ధమైన జపం శ్వాసను, హృదయ స్పందనను నెమ్మదిస్తుంది; ప్రశాంతపరిచే పారాసింపథెటిక్ వ్యవస్థను క్రియాశీలం చేస్తుంది — ఆందోళనను తగ్గిస్తుంది. వారంవారీ ఆచారం భావోద్వేగ మనసుకు స్థిరమైన ఆధారాన్ని ఇస్తుంది.",
                      "hi": "लयबद्ध जप साँस व हृदयगति धीमी कर शांत करने वाली पैरासिम्पैथेटिक प्रणाली को सक्रिय करता है — चिंता घटती है। साप्ताहिक अनुष्ठान भावनात्मक मन को स्थिर आधार देता है।"}},
    "mars": {
        "deity": {"te": "మంగళ / హనుమాన్", "hi": "मंगल / हनुमान"},
        "practice": {"te": "మంగళవారాల్లో హనుమాన్ చాలీసా పఠించండి; క్రమశిక్షణతో శారీరక సేవ చేయండి.",
                     "hi": "मंगलवार को हनुमान चालीसा पढ़ें; अनुशासित शारीरिक सेवा करें।"},
        "rationale": {"te": "అశాంత మార్స్ శక్తిని క్రమశిక్షణతో వ్యాయామం లేదా సేవ వైపు మళ్లించడం కోపనిర్వహణకు నిరూపిత సూత్రం — శారీరక శ్రమ ఒత్తిడి హార్మోన్లను తగ్గించి పట్టుదలను పెంచుతుంది. చాలీసా బిగ్గరగా చదవడం నరాలను స్థిరపరిచే శ్వాస వ్యాయామం.",
                      "hi": "अशांत मंगल-ऊर्जा को अनुशासित व्यायाम या सेवा में लगाना क्रोध-प्रबंधन का सिद्ध तरीका है — शारीरिक श्रम तनाव-हार्मोन घटाकर सहनशक्ति बढ़ाता है। चालीसा ऊँचे स्वर में पढ़ना नसों को स्थिर करने वाला साँस-व्यायाम है।"}},
    "mercury": {
        "deity": {"te": "బుధ / విష్ణువు", "hi": "बुध / विष्णु"},
        "practice": {"te": "పక్షులకు పెసలు అందించండి; విష్ణు సహస్రనామం పఠించండి.",
                     "hi": "पक्षियों को हरा मूँग खिलाएँ; विष्णु सहस्रनाम का पाठ करें।"},
        "rationale": {"te": "ఆహారం అందించడం, దానం చేయడం 'హెల్పర్స్ హై'ని కలిగిస్తాయి — మనఃస్థితిని, సామాజిక అనుబంధాన్ని పెంచే డోపమైన్-ఆక్సిటోసిన్ ఉత్సాహం. శ్లోకాలు కంఠస్థం చేయడం మౌఖిక జ్ఞాపకశక్తికి, మానసిక చురుకుదనానికి మంచి వ్యాయామం.",
                      "hi": "खिलाना व दान करना 'हेल्पर्स हाई' जगाते हैं — मनोदशा व सामाजिक जुड़ाव बढ़ाने वाला डोपामिन-ऑक्सीटोसिन उभार। श्लोक कंठस्थ करना मौखिक स्मृति व मानसिक फुर्ती का सच्चा अभ्यास है।"}},
    "jupiter": {
        "deity": {"te": "గురు / దక్షిణామూర్తి", "hi": "गुरु / दक्षिणामूर्ति"},
        "practice": {"te": "గురువారాల్లో ఆలయంలో పసుపు వస్తువులు అర్పించండి; గురువులను గౌరవించండి.",
                     "hi": "गुरुवार को मंदिर में पीली वस्तुएँ अर्पित करें; गुरुजनों का सम्मान करें।"},
        "rationale": {"te": "గురువుల పట్ల కృతజ్ఞత, క్రమబద్ధమైన దానం జీవిత సంతృప్తికి బలమైన సూచికలు — దృష్టిని, వివేకాన్ని విస్తరిస్తాయి. పసుపు, పసుపు ఆహారాలకు నిజమైన శోథనిరోధక ప్రయోజనాలు కూడా.",
                      "hi": "गुरुजनों के प्रति कृतज्ञता व नियमित दान जीवन-संतोष के मज़बूत संकेतक हैं — दृष्टि व विवेक बढ़ाते हैं। हल्दी व पीले भोजन के सूजनरोधी लाभ भी सच्चे हैं।"}},
    "venus": {
        "deity": {"te": "శుక్ర / లక్ష్మి", "hi": "शुक्र / लक्ष्मी"},
        "practice": {"te": "శుక్రవారాల్లో లక్ష్మీ పూజ చేయండి; కళలను, సంబంధాలను పోషించండి.",
                     "hi": "शुक्रवार को लक्ष्मी पूजा करें; कला व संबंधों को संजोएँ।"},
        "rationale": {"te": "సౌందర్యం, కళ, సంగీతంతో మమేకం కావడం డోపమైన్‌ను, శ్రేయస్సును పెంచుతుంది; భాగస్వామ్యంలో కృతజ్ఞత, సామరస్యం పెంపొందించడం దానిని బలపరుస్తుంది — ఇది శుక్రుని రంగం.",
                      "hi": "सौंदर्य, कला व संगीत से जुड़ना डोपामिन व कल्याण बढ़ाता है; साझेदारी में कृतज्ञता व सामंजस्य उसे मज़बूत करते हैं — यही शुक्र का क्षेत्र है।"}},
    "saturn": {
        "deity": {"te": "శని / హనుమాన్", "hi": "शनि / हनुमान"},
        "practice": {"te": "శనివారాల్లో హనుమాన్‌కు నువ్వుల నూనె దీపం వెలిగించండి; పెద్దలకు, అవసరమైనవారికి సేవ చేయండి.",
                     "hi": "शनिवार को हनुमान को तिल-तेल का दीपक जलाएँ; बुज़ुर्गों व ज़रूरतमंदों की सेवा करें।"},
        "rationale": {"te": "సంరక్షణ, సేవ, స్వచ్ఛంద సేవ తక్కువ నిరాశతో, దీర్ఘాయువుతో బలంగా ముడిపడి ఉంటాయి. శని కోరే వినయపూర్వక, ఓపికైన దినచర్య కష్టాన్ని నైపుణ్యంగా మార్చే క్రమశిక్షణను నిర్మిస్తుంది.",
                      "hi": "देखभाल, सेवा व स्वयंसेवा कम अवसाद व अधिक आयु से जुड़ी हैं। शनि जिस विनम्र, धैर्यपूर्ण दिनचर्या की माँग करता है, वह कठिनाई को कुशलता में बदलने वाला अनुशासन गढ़ती है।"}},
    "rahu": {
        "deity": {"te": "రాహు / దుర్గ", "hi": "राहु / दुर्गा"},
        "practice": {"te": "దుర్గా ఉపాసన చేయండి; దుర్గా సప్తశతి పఠించండి.",
                     "hi": "दुर्गा उपासना करें; दुर्गा सप्तशती का पाठ करें।"},
        "rationale": {"te": "క్రమబద్ధమైన భక్తి అభ్యాసం రాహు సూచించే చెదిరిన దృష్టిని, ఆందోళనను ఎదుర్కొంటుంది — ఆచారం నియంత్రణ భావాన్ని పునరుద్ధరించి ఒత్తిడిని తగ్గిస్తుంది.",
                      "hi": "नियमित भक्ति-अभ्यास राहु द्वारा दर्शाई बिखरी एकाग्रता व चिंता का सामना करता है — अनुष्ठान नियंत्रण का भाव लौटाकर तनाव घटाता है।"}},
    "ketu": {
        "deity": {"te": "కేతు / గణేశుడు", "hi": "केतु / गणेश"},
        "practice": {"te": "గణేశ పూజతో పనులు ప్రారంభించండి; సంకష్టి చతుర్థి పాటించండి.",
                     "hi": "गणेश पूजा से कार्य आरंभ करें; संकष्टी चतुर्थी का व्रत रखें।"},
        "rationale": {"te": "పనిని చిన్న స్థిరపరిచే ఆచారంతో ప్రారంభించడం ఏకాగ్రతను పెంచి వాయిదాను తగ్గిస్తుంది. కేతు రంగం విరక్తి; మైండ్‌ఫుల్‌నెస్ మనసును వదిలిపెట్టడంలో, స్థిరపడటంలో సాయపడుతుంది.",
                      "hi": "कार्य को छोटे स्थिरता-अनुष्ठान से आरंभ करना एकाग्रता बढ़ाकर टालमटोल घटाता है। केतु का क्षेत्र वैराग्य है; माइंडफुलनेस मन को छोड़ना व स्थिर होना सिखाती है।"}},
}


def remedy(graha: str | None, field: str, en_value: str, language: str) -> str:
    if not graha or language == "en":
        return en_value
    entry = PERIOD.get(graha, {}).get(field)
    return _pick2(entry, language, en_value)

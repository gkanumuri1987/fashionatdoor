"use client";

/** Lightweight trilingual UI i18n — English / Telugu / Hindi.
 *  The selected language drives ALL UI text AND the default language of AI
 *  readings/narratives. Persisted per browser in localStorage. */

import { createContext, useContext, useEffect, useState } from "react";

export type Lang = "en" | "te" | "hi";
export const LANG_LABELS: Record<Lang, string> = { en: "English", te: "తెలుగు", hi: "हिन्दी" };

type Entry = Record<Lang, string>;

const T: Record<string, Entry> = {
  app_title: { en: "Jyotish AI", te: "జ్యోతిష్ AI", hi: "ज्योतिष AI" },
  tagline: {
    en: "Vedic birth chart — computed with Swiss Ephemeris, never guessed by AI",
    te: "వేద జన్మ కుండలి — స్విస్ ఎఫెమెరిస్‌తో ఖచ్చితంగా లెక్కించబడింది, AI ఊహ కాదు",
    hi: "वैदिक जन्म कुंडली — स्विस एफेमेरिस से सटीक गणना, AI का अनुमान नहीं",
  },
  nav_kundli: { en: "Kundli", te: "కుండలి", hi: "कुंडली" },
  nav_milan: { en: "Kundli Milan", te: "కుండలి మిలన్", hi: "कुंडली मिलान" },
  nav_palm: { en: "Palmistry link", te: "హస్తసాముద్రికం లింక్", hi: "हस्तरेखा लिंक" },
  back_to_chart: { en: "← Birth chart", te: "← జన్మ కుండలి", hi: "← जन्म कुंडली" },

  share_link: { en: "Share this link (valid 48h):", te: "ఈ లింక్‌ను పంపండి (48 గం. వరకు చెల్లుతుంది):", hi: "यह लिंक भेजें (48 घंटे मान्य):" },
  copy: { en: "Copy", te: "కాపీ", hi: "कॉपी" },
  copied: { en: "Copied ✓", te: "కాపీ అయింది ✓", hi: "कॉपी हो गया ✓" },
  copy_failed: { en: "Copy failed — select the link text and copy manually.", te: "కాపీ కాలేదు — లింక్‌ను సెలెక్ట్ చేసి మీరే కాపీ చేయండి.", hi: "कॉपी नहीं हुआ — लिंक चुनकर स्वयं कॉपी करें।" },
  share_whatsapp: { en: "WhatsApp", te: "వాట్సాప్", hi: "व्हाट्सएप" },
  share_native: { en: "Share…", te: "షేర్ చేయండి…", hi: "शेयर करें…" },
  palm_share_msg: {
    en: "Take a photo of your palm at this link and get your palm reading:",
    te: "ఈ లింక్‌లో మీ అరచేతి ఫోటో తీసి మీ హస్తసాముద్రిక ఫలితం పొందండి:",
    hi: "इस लिंक पर अपनी हथेली की फोटो लें और हस्तरेखा फल पाएँ:",
  },

  dob: { en: "Date of birth", te: "పుట్టిన తేదీ", hi: "जन्म तिथि" },
  tob: { en: "Time of birth", te: "పుట్టిన సమయం", hi: "जन्म समय" },
  time_exact: { en: "Time is exact", te: "సమయం ఖచ్చితం", hi: "समय सटीक है" },
  time_approx: { en: "Approximate (±30 min)", te: "సుమారుగా (±30 నిమి.)", hi: "अनुमानित (±30 मिनट)" },
  time_unknown: { en: "Unknown", te: "తెలియదు", hi: "अज्ञात" },
  pob: { en: "Place of birth", te: "పుట్టిన ప్రదేశం", hi: "जन्म स्थान" },
  place_ph: { en: "City, country…", te: "నగరం, దేశం…", hi: "शहर, देश…" },
  ayanamsa: { en: "Ayanamsa", te: "అయనాంశ", hi: "अयनांश" },
  accuracy_warning: {
    en: "The ascendant moves a full sign roughly every 2 hours — with an inexact birth time, lagna-based results (houses, dasha timing) carry uncertainty.",
    te: "లగ్నం సుమారు ప్రతి 2 గంటలకు ఒక రాశి మారుతుంది — పుట్టిన సమయం ఖచ్చితంగా తెలియకపోతే లగ్న ఆధారిత ఫలితాలు (భావాలు, దశా కాలాలు) అనిశ్చితంగా ఉంటాయి.",
    hi: "लग्न लगभग हर 2 घंटे में एक राशि बदलता है — जन्म समय सटीक न होने पर लग्न-आधारित फल (भाव, दशा काल) अनिश्चित रहते हैं।",
  },
  generate: { en: "Generate Kundli", te: "కుండలి తయారు చేయండి", hi: "कुंडली बनाएँ" },
  computing: { en: "Computing…", te: "లెక్కిస్తోంది…", hi: "गणना हो रही है…" },
  pick_place: { en: "Pick a birth place from the suggestions.", te: "సూచనల నుండి పుట్టిన ప్రదేశాన్ని ఎంచుకోండి.", hi: "सुझावों में से जन्म स्थान चुनें।" },
  generic_error: { en: "Something went wrong", te: "ఏదో తప్పు జరిగింది", hi: "कुछ गड़बड़ हो गई" },

  lagna: { en: "Lagna", te: "లగ్నం", hi: "लग्न" },
  moon: { en: "Moon", te: "చంద్రుడు", hi: "चंद्र" },
  tab_chart: { en: "Chart", te: "కుండలి", hi: "कुंडली" },
  tab_planets: { en: "Planets", te: "గ్రహాలు", hi: "ग्रह" },
  tab_dasha: { en: "Dasha", te: "దశలు", hi: "दशा" },
  tab_panchanga: { en: "Panchanga", te: "పంచాంగం", hi: "पंचांग" },
  tab_reading: { en: "Reading", te: "ఫలితం", hi: "फल" },
  south_indian: { en: "South Indian", te: "దక్షిణ భారత", hi: "दक्षिण भारतीय" },
  north_indian: { en: "North Indian", te: "ఉత్తర భారత", hi: "उत्तर भारतीय" },

  tab_advanced: { en: "Advanced", te: "అధునాతనం", hi: "उन्नत" },
  jaimini_title: { en: "Jaimini", te: "జైమిని", hi: "जैमिनी" },
  chara_karakas: { en: "Chara Karakas", te: "చర కారకాలు", hi: "चर कारक" },
  ishta_devata: { en: "Ishta Devata (from Karakamsa)", te: "ఇష్ట దేవత (కారకాంశ నుండి)", hi: "इष्ट देवता (कारकांश से)" },
  arudha_lagna: { en: "Arudha Lagna", te: "ఆరూఢ లగ్నం", hi: "आरूढ़ लग्न" },
  upapada: { en: "Upapada", te: "ఉపపద", hi: "उपपद" },
  bhava_chalita_title: { en: "Bhava Chalita (degree-based houses)", te: "భావ చలిత (డిగ్రీ ఆధారిత భావాలు)", hi: "भाव चलित (अंश आधारित भाव)" },
  in_sandhi: { en: "in sandhi (weak for both houses)", te: "సంధిలో (రెండు భావాలకూ బలహీనం)", hi: "संधि में (दोनों भावों के लिए कमज़ोर)" },
  kp_title: { en: "KP — Star / Sub lords", te: "KP — నక్షత్ర / ఉప అధిపతులు", hi: "KP — नक्षत्र / उप स्वामी" },
  dasha_system: { en: "Dasha system", te: "దశా విధానం", hi: "दशा प्रणाली" },
  loading_dasha: { en: "Computing periods…", te: "దశలు లెక్కిస్తోంది…", hi: "दशाएँ गणना हो रही हैं…" },
  nav_vastu: { en: "Vastu", te: "వాస్తు", hi: "वास्तु" },
  vastu_title: { en: "Vastu Analysis", te: "వాస్తు విశ్లేషణ", hi: "वास्तु विश्लेषण" },
  vastu_sub: { en: "Upload your floor plan — rooms are judged by classical placement rules, never guessed.", te: "మీ ఇంటి ప్లాన్ అప్‌లోడ్ చేయండి — గదులు సంప్రదాయ వాస్తు నియమాల ప్రకారం ఖచ్చితంగా అంచనా వేయబడతాయి.", hi: "अपना फ्लोर प्लान अपलोड करें — कमरों का मूल्यांकन शास्त्रीय नियमों से होता है, अनुमान से नहीं।" },
  vastu_top_dir: { en: "The TOP of the plan faces", te: "ప్లాన్ పై భాగం ఏ దిక్కు", hi: "प्लान का ऊपरी भाग किस दिशा में" },
  vastu_pick: { en: "📐 Choose floor plan image", te: "📐 ప్లాన్ చిత్రం ఎంచుకోండి", hi: "📐 प्लान चित्र चुनें" },
  vastu_analyze: { en: "Analyze Vastu", te: "వాస్తు విశ్లేషించండి", hi: "वास्तु विश्लेषण करें" },
  vastu_busy: { en: "Reading the floor plan…", te: "ప్లాన్ చదువుతోంది…", hi: "प्लान पढ़ा जा रहा है…" },
  vastu_score: { en: "Vastu score", te: "వాస్తు స్కోరు", hi: "वास्तु स्कोर" },
  vastu_room: { en: "Room", te: "గది", hi: "कमरा" },
  vastu_zone: { en: "Zone", te: "దిక్కు", hi: "दिशा" },
  vastu_verdict: { en: "Verdict", te: "ఫలితం", hi: "निर्णय" },
  vastu_not_stored: { en: "Your plan was analyzed in memory and was not stored.", te: "మీ ప్లాన్ మెమరీలో మాత్రమే విశ్లేషించబడింది, నిల్వ చేయబడలేదు.", hi: "आपका प्लान केवल मेमोरी में विश्लेषित हुआ, संग्रहीत नहीं हुआ।" },
  palm_page_desc: {
    en: "Create a private link, send it to anyone — they photograph their palm and the reading appears right there. The link lives for 48 hours; photos are never stored.",
    te: "ఒక ప్రైవేట్ లింక్ సృష్టించి ఎవరికైనా పంపండి — వారు అరచేతి ఫోటో తీస్తే ఫలితం అక్కడే కనిపిస్తుంది. లింక్ 48 గంటలు చెల్లుతుంది; ఫోటోలు నిల్వ చేయబడవు.",
    hi: "एक निजी लिंक बनाएँ और किसी को भी भेजें — वे हथेली की फोटो लेंगे और फल वहीं दिखेगा। लिंक 48 घंटे मान्य; फोटो कभी संग्रहीत नहीं होते।",
  },
  palm_mint_btn: { en: "✋ Create palm link", te: "✋ లింక్ సృష్టించండి", hi: "✋ लिंक बनाएँ" },
  nav_calendar: { en: "Calendar", te: "క్యాలెండర్", hi: "कैलेंडर" },
  cal_title: { en: "Panchanga Calendar", te: "పంచాంగ క్యాలెండర్", hi: "पंचांग कैलेंडर" },
  cal_month: { en: "Month", te: "నెల", hi: "महीना" },
  cal_year: { en: "Year", te: "సంవత్సరం", hi: "वर्ष" },
  cal_tradition: { en: "Tradition", te: "సంప్రదాయం", hi: "परंपरा" },
  cal_location: { en: "Country / timezone", te: "దేశం / సమయమండలం", hi: "देश / समय क्षेत्र" },
  cal_download_pdf: { en: "Download PDF", te: "PDF డౌన్‌లోడ్", hi: "PDF डाउनलोड" },
  cal_download_ics: { en: "Add to calendar", te: "క్యాలెండర్‌కు జోడించండి", hi: "कैलेंडर में जोड़ें" },
  cal_good: { en: "Good time (Abhijit)", te: "శుభ సమయం (అభిజిత్)", hi: "शुभ समय (अभिजीत)" },
  cal_avoid: { en: "Avoid: Rahu · Yamaganda · Gulika", te: "వర్జ్యం: రాహుకాలం · యమగండం · గుళిక", hi: "वर्जित: राहुकाल · यमगंड · गुलिक" },
  cal_then: { en: "then", te: "తర్వాత", hi: "फिर" },
  cal_detail_tithi: { en: "Tithi", te: "తిథి", hi: "तिथि" },
  cal_detail_nakshatra: { en: "Nakshatra", te: "నక్షత్రం", hi: "नक्षत्र" },
  cal_detail_yoga: { en: "Yoga", te: "యోగం", hi: "योग" },
  cal_detail_karana: { en: "Karana", te: "కరణం", hi: "करण" },
  cal_detail_sun: { en: "Sunrise / Sunset", te: "సూర్యోదయం / అస్తమయం", hi: "सूर्योदय / सूर्यास्त" },
  cal_rahu: { en: "Rahu kalam", te: "రాహుకాలం", hi: "राहुकाल" },
  cal_yamaganda: { en: "Yamaganda", te: "యమగండం", hi: "यमगंड" },
  cal_gulika: { en: "Gulika kalam", te: "గుళిక కాలం", hi: "गुलिक काल" },
  cal_abhijit: { en: "Abhijit muhurta", te: "అభిజిత్ ముహూర్తం", hi: "अभिजीत मुहूर्त" },
  cal_ends: { en: "till", te: "వరకు", hi: "तक" },
  ay_info_title: { en: "What is Ayanamsa?", te: "అయనాంశ అంటే ఏమిటి?", hi: "अयनांश क्या है?" },
  ay_info_body: {
    en: "Vedic astrology reads the REAL star positions (sidereal). The seasons-based Western zodiac has drifted ~24° from the stars over centuries — Ayanamsa is that correction. Every kundli needs one; schools differ only by fractions of a degree, which matters just at sign/pada boundaries.",
    te: "వేద జ్యోతిషం నిజమైన నక్షత్ర స్థానాలను (సైడీరియల్) చదువుతుంది. రుతువుల ఆధారిత పాశ్చాత్య రాశిచక్రం శతాబ్దాలుగా నక్షత్రాల నుండి ~24° జరిగింది — ఆ సవరణే అయనాంశ. ప్రతి కుండలికి ఇది అవసరం; పద్ధతుల మధ్య తేడా డిగ్రీలో కొద్ది భాగమే — రాశి/పాద సరిహద్దుల్లో మాత్రమే ఇది ప్రభావం చూపుతుంది.",
    hi: "वैदिक ज्योतिष वास्तविक तारा-स्थितियाँ (सायडेरियल) पढ़ता है। ऋतु-आधारित पश्चिमी राशिचक्र सदियों में तारों से ~24° खिसक चुका है — वही सुधार अयनांश है। हर कुंडली को यह चाहिए; पद्धतियों में अंतर डिग्री के अंश भर का है, जो केवल राशि/पद की सीमाओं पर असर डालता है।",
  },
  ay_lahiri: {
    en: "Lahiri (Chitrapaksha) — India's official standard, used by nearly all panchangams, temples and software. If unsure, choose this.",
    te: "లహరి (చిత్రపక్ష) — భారత ప్రభుత్వ అధికారిక ప్రమాణం; దాదాపు అన్ని పంచాంగాలు, దేవాలయాలు, సాఫ్ట్‌వేర్లు దీన్నే వాడతాయి. సందేహం ఉంటే ఇదే ఎంచుకోండి.",
    hi: "लाहिरी (चित्रपक्ष) — भारत का आधिकारिक मानक; लगभग सभी पंचांग, मंदिर और सॉफ्टवेयर इसी का उपयोग करते हैं। संदेह हो तो यही चुनें।",
  },
  ay_raman: {
    en: "Raman — B.V. Raman's school, ~1.4° behind Lahiri. Pick only if your family astrologer follows Raman.",
    te: "రామన్ — బి.వి. రామన్ పద్ధతి, లహరి కంటే ~1.4° వెనుక. మీ కుటుంబ జ్యోతిష్యులు రామన్ పద్ధతి పాటిస్తేనే ఎంచుకోండి.",
    hi: "रमन — बी.वी. रमन की पद्धति, लाहिरी से ~1.4° पीछे। तभी चुनें जब आपके ज्योतिषी रमन पद्धति मानते हों।",
  },
  ay_kp: {
    en: "KP (Krishnamurti) — a few arc-minutes from Lahiri; required for the KP system's sub-lord techniques.",
    te: "KP (కృష్ణమూర్తి) — లహరికి కొన్ని ఆర్క్-నిమిషాల తేడా; KP పద్ధతి సబ్-లార్డ్ విధానానికి ఇది తప్పనిసరి.",
    hi: "KP (कृष्णमूर्ति) — लाहिरी से कुछ आर्क-मिनट का अंतर; KP पद्धति की सब-लॉर्ड तकनीकों के लिए आवश्यक।",
  },
  ay_recommend: { en: "Not sure? Keep Lahiri — it matches the panchangam your family already uses.",
                  te: "తెలియకపోతే లహరినే ఉంచండి — మీ ఇంట్లో వాడే పంచాంగంతో ఇది సరిపోతుంది.",
                  hi: "निश्चित नहीं? लाहिरी ही रखें — यह आपके घर के पंचांग से मेल खाता है।" },
  recommended: { en: "recommended", te: "సిఫార్సు", hi: "अनुशंसित" },
  why_receipts: { en: "Why? — see the chart receipts", te: "ఎందుకు? — కుండలి ఆధారాలు చూడండి", hi: "क्यों? — कुंडली के प्रमाण देखें" },
  verdict_supportive: { en: "supportive", te: "అనుకూలం", hi: "अनुकूल" },
  verdict_mixed: { en: "mixed", te: "మిశ్రమం", hi: "मिश्रित" },
  verdict_challenging: { en: "challenging", te: "సవాలుతో కూడినది", hi: "चुनौतीपूर्ण" },
  sec_personality: { en: "Personality", te: "వ్యక్తిత్వం", hi: "व्यक्तित्व" },
  sec_career: { en: "Career", te: "వృత్తి", hi: "करियर" },
  sec_wealth: { en: "Wealth", te: "ధనం", hi: "धन" },
  sec_relationships: { en: "Relationships", te: "బంధాలు", hi: "रिश्ते" },
  sec_health: { en: "Health", te: "ఆరోగ్యం", hi: "स्वास्थ्य" },
  sec_dharma: { en: "Dharma", te: "ధర్మం", hi: "धर्म" },
  sec_dasha_outlook: { en: "Current Period", te: "ప్రస్తుత దశ", hi: "वर्तमान दशा" },
  sec_remedies: { en: "Remedies", te: "పరిహారాలు", hi: "उपाय" },
  consulting: { en: "Consulting the classics…", te: "శాస్త్రాలను సంప్రదిస్తోంది…", hi: "शास्त्रों से परामर्श हो रहा है…" },
  reading_hint: {
    en: "Pick a section — the reading is written from your computed chart and classical dictums (BPHS, Phaladeepika, Saravali, Puranic archetypes).",
    te: "ఒక విభాగాన్ని ఎంచుకోండి — ఫలితం మీ లెక్కించిన కుండలి మరియు శాస్త్ర వచనాల (BPHS, ఫలదీపిక, సారావళి, పురాణ కథలు) ఆధారంగా రాయబడుతుంది.",
    hi: "एक खंड चुनें — फल आपकी गणना की गई कुंडली और शास्त्र वचनों (BPHS, फलदीपिका, सारावली, पुराण कथाओं) के आधार पर लिखा जाता है।",
  },
  disclaimer: {
    en: "For guidance and reflection — not a substitute for professional advice.",
    te: "మార్గదర్శనం, ఆత్మపరిశీలన కోసం మాత్రమే — నిపుణుల సలహాకు ప్రత్యామ్నాయం కాదు.",
    hi: "मार्गदर्शन और चिंतन के लिए — विशेषज्ञ सलाह का विकल्प नहीं।",
  },

  milan_title: { en: "Kundli Milan", te: "కుండలి మిలన్", hi: "कुंडली मिलान" },
  milan_tagline: {
    en: "Ashtakoota 36-guna matching + Manglik analysis — computed, never guessed",
    te: "అష్టకూట 36-గుణ మిలన్ + మాంగళిక విశ్లేషణ — ఖచ్చితంగా లెక్కించబడింది",
    hi: "अष्टकूट 36-गुण मिलान + मांगलिक विश्लेषण — सटीक गणना, अनुमान नहीं",
  },
  boy_groom: { en: "Boy / Groom", te: "వరుడు", hi: "वर" },
  girl_bride: { en: "Girl / Bride", te: "వధువు", hi: "वधू" },
  matching: { en: "Matching…", te: "మిలన్ జరుగుతోంది…", hi: "मिलान हो रहा है…" },
  match_btn: { en: "Match Kundlis", te: "కుండలి మిలన్ చేయండి", hi: "कुंडली मिलाएँ" },
  fill_both: { en: "Fill both birth details and pick places from the suggestions.", te: "ఇద్దరి జనన వివరాలు నింపి, సూచనల నుండి ప్రదేశాలను ఎంచుకోండి.", hi: "दोनों के जन्म विवरण भरें और सुझावों से स्थान चुनें।" },
  koota: { en: "Koota", te: "కూటమి", hi: "कूट" },
  boy_col: { en: "Boy", te: "వరుడు", hi: "वर" },
  girl_col: { en: "Girl", te: "వధువు", hi: "वधू" },
  points: { en: "Points", te: "పాయింట్లు", hi: "अंक" },
  dosha: { en: "dosha", te: "దోషం", hi: "दोष" },
  exception: { en: "exception", te: "మినహాయింపు", hi: "अपवाद" },
  writing: { en: "Writing…", te: "రాస్తోంది…", hi: "लिखा जा रहा है…" },
  ai_compat: { en: "AI compatibility reading", te: "AI అనుకూలత ఫలితం", hi: "AI अनुकूलता फल" },
  verdict_excellent: { en: "Excellent match", te: "అత్యుత్తమ మిలన్", hi: "उत्कृष्ट मिलान" },
  verdict_very_good: { en: "Very good match", te: "చాలా మంచి మిలన్", hi: "बहुत अच्छा मिलान" },
  verdict_acceptable: { en: "Acceptable match", te: "ఆమోదయోగ్య మిలన్", hi: "स्वीकार्य मिलान" },
  verdict_below: { en: "Below traditional threshold", te: "సాంప్రదాయ కనీస స్థాయి కంటే తక్కువ", hi: "पारंपरिक न्यूनतम से कम" },

  palm_title: { en: "Palm Reading", te: "హస్తసాముద్రికం", hi: "हस्तरेखा फल" },
  palm_sub: { en: "Photograph your palm — the reading appears right here.", te: "మీ అరచేతి ఫోటో తీయండి — ఫలితం ఇక్కడే కనిపిస్తుంది.", hi: "अपनी हथेली की फोटो लें — फल यहीं दिखेगा।" },
  link_expired: { en: "Link expired", te: "లింక్ గడువు ముగిసింది", hi: "लिंक की अवधि समाप्त" },
  link_expired_sub: { en: "This palm-reading link is no longer valid. Ask for a fresh link.", te: "ఈ లింక్ ఇక చెల్లదు. కొత్త లింక్ అడగండి.", hi: "यह लिंक अब मान्य नहीं है। नया लिंक माँगें।" },
  loading: { en: "Loading…", te: "లోడ్ అవుతోంది…", hi: "लोड हो रहा है…" },
  retake: { en: "Please retake:", te: "దయచేసి మళ్లీ తీయండి:", hi: "कृपया फिर से लें:" },
  palm_instructions: {
    en: "Open your palm flat, fill the frame, use bright even light. Dominant hand first; add the other hand as a second photo if you like.",
    te: "అరచేతిని చాపి ఫ్రేమ్ నిండా పెట్టండి, మంచి వెలుతురులో తీయండి. ముందుగా ఎక్కువ వాడే చేయి; కావాలంటే రెండో చేతిని రెండో ఫోటోగా జోడించండి.",
    hi: "हथेली को सीधा खोलें, फ्रेम भरें, अच्छी रोशनी में लें। पहले प्रमुख हाथ; चाहें तो दूसरे हाथ की दूसरी फोटो जोड़ें।",
  },
  change_photos: { en: "Change photo(s)", te: "ఫోటో(లు) మార్చండి", hi: "फोटो बदलें" },
  take_photo: { en: "📷 Take / choose photo", te: "📷 ఫోటో తీయండి / ఎంచుకోండి", hi: "📷 फोटो लें / चुनें" },
  reading_language: { en: "Reading language", te: "ఫలిత భాష", hi: "फल की भाषा" },
  consent_text: {
    en: "I consent to my palm photo being analyzed. The photo is processed in memory and not stored; only the written reading is kept, and this link expires within 48 hours.",
    te: "నా అరచేతి ఫోటోను విశ్లేషించడానికి అంగీకరిస్తున్నాను. ఫోటో మెమరీలో మాత్రమే ప్రాసెస్ అవుతుంది, నిల్వ చేయబడదు; రాసిన ఫలితం మాత్రమే ఉంచబడుతుంది, ఈ లింక్ 48 గంటల్లో ముగుస్తుంది.",
    hi: "मैं अपनी हथेली की फोटो के विश्लेषण की सहमति देता/देती हूँ। फोटो केवल मेमोरी में प्रोसेस होती है, संग्रहीत नहीं होती; केवल लिखित फल रखा जाता है, और यह लिंक 48 घंटे में समाप्त हो जाता है।",
  },
  reading_palm: { en: "Reading your palm…", te: "మీ అరచేతిని చదువుతోంది…", hi: "आपकी हथेली पढ़ी जा रही है…" },
  get_reading: { en: "Get my reading", te: "నా ఫలితం పొందండి", hi: "मेरा फल पाएँ" },
  photo_not_stored: { en: "Your photo was analyzed in memory and was not stored.", te: "మీ ఫోటో మెమరీలో మాత్రమే విశ్లేషించబడింది, నిల్వ చేయబడలేదు.", hi: "आपकी फोटो केवल मेमोरी में विश्लेषित हुई, संग्रहीत नहीं हुई।" },

  sign_in: { en: "Sign in", te: "సైన్ ఇన్", hi: "साइन इन" },
  sign_out: { en: "Sign out", te: "సైన్ అవుట్", hi: "साइन आउट" },
  sign_in_email: { en: "Sign in with email", te: "ఇమెయిల్‌తో సైన్ ఇన్", hi: "ईमेल से साइन इन" },
  send_code: { en: "Send code", te: "కోడ్ పంపండి", hi: "कोड भेजें" },
  verify_code: { en: "Verify code", te: "కోడ్ ధృవీకరించండి", hi: "कोड सत्यापित करें" },
  code_sent: { en: "Code sent — check your email.", te: "కోడ్ పంపబడింది — మీ ఇమెయిల్ చూడండి.", hi: "कोड भेजा गया — अपना ईमेल देखें।" },
  code_ph: { en: "6-digit code", te: "6-అంకెల కోడ్", hi: "6-अंकों का कोड" },

  saved_profiles: { en: "Saved profiles", te: "సేవ్ చేసిన ప్రొఫైల్స్", hi: "सहेजी प्रोफ़ाइलें" },
  save_current: { en: "Save current", te: "ప్రస్తుతది సేవ్ చేయండి", hi: "वर्तमान सहेजें" },
  saved_ok: { en: "Saved.", te: "సేవ్ అయింది.", hi: "सहेजा गया।" },
  no_profiles: { en: "No saved profiles yet.", te: "ఇంకా సేవ్ చేసిన ప్రొఫైల్స్ లేవు.", hi: "अभी कोई सहेजी प्रोफ़ाइल नहीं।" },
  name_ph: { en: "Name (e.g. Amma)", te: "పేరు (ఉదా. అమ్మ)", hi: "नाम (जैसे अम्मा)" },
};

interface LangCtx { lang: Lang; setLang: (l: Lang) => void; t: (key: string) => string }
const Ctx = createContext<LangCtx>({ lang: "en", setLang: () => {}, t: (k) => T[k]?.en ?? k });

export function LangProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<Lang>("en");
  useEffect(() => {
    try {
      const saved = localStorage.getItem("jyotish_lang");
      if (saved === "te" || saved === "hi" || saved === "en") setLangState(saved);
    } catch { /* private mode */ }
  }, []);
  const setLang = (l: Lang) => {
    setLangState(l);
    try { localStorage.setItem("jyotish_lang", l); } catch { /* best-effort */ }
  };
  const t = (key: string) => T[key]?.[lang] ?? T[key]?.en ?? key;
  return <Ctx.Provider value={{ lang, setLang, t }}>{children}</Ctx.Provider>;
}

export function useLang(): LangCtx {
  return useContext(Ctx);
}

export function LangSwitcher() {
  const { lang, setLang } = useLang();
  return (
    <div className="flex gap-1 rounded-lg border border-[var(--line)] p-0.5 text-xs">
      {(Object.keys(LANG_LABELS) as Lang[]).map((l) => (
        <button key={l} onClick={() => setLang(l)}
                className={`rounded-md px-2 py-1 ${lang === l ? "bg-[var(--gold)] font-semibold text-[var(--on-gold)]" : "text-[var(--ink-soft)]"}`}>
          {LANG_LABELS[l]}
        </button>
      ))}
    </div>
  );
}

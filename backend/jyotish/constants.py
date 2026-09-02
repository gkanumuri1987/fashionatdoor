"""Static Jyotish tables — signs, grahas, nakshatras, lords, dignities, panchanga names.

Rule sources: Brihat Parashara Hora Shastra (BPHS) for dignities/vargas/dashas,
standard Panchang tables for tithi/yoga/karana. All entries are freshly authored
tables of facts (not translation text).
"""

# ── Signs (rashi) ────────────────────────────────────────────────────────────
SIGNS = [
    {"index": 0, "name": "Mesha", "en": "Aries", "element": "fire", "mobility": "movable"},
    {"index": 1, "name": "Vrishabha", "en": "Taurus", "element": "earth", "mobility": "fixed"},
    {"index": 2, "name": "Mithuna", "en": "Gemini", "element": "air", "mobility": "dual"},
    {"index": 3, "name": "Karka", "en": "Cancer", "element": "water", "mobility": "movable"},
    {"index": 4, "name": "Simha", "en": "Leo", "element": "fire", "mobility": "fixed"},
    {"index": 5, "name": "Kanya", "en": "Virgo", "element": "earth", "mobility": "dual"},
    {"index": 6, "name": "Tula", "en": "Libra", "element": "air", "mobility": "movable"},
    {"index": 7, "name": "Vrischika", "en": "Scorpio", "element": "water", "mobility": "fixed"},
    {"index": 8, "name": "Dhanu", "en": "Sagittarius", "element": "fire", "mobility": "dual"},
    {"index": 9, "name": "Makara", "en": "Capricorn", "element": "earth", "mobility": "movable"},
    {"index": 10, "name": "Kumbha", "en": "Aquarius", "element": "air", "mobility": "fixed"},
    {"index": 11, "name": "Meena", "en": "Pisces", "element": "water", "mobility": "dual"},
]

SIGN_LORD = ["mars", "venus", "mercury", "moon", "sun", "mercury",
             "venus", "mars", "jupiter", "saturn", "saturn", "jupiter"]

# ── Grahas ───────────────────────────────────────────────────────────────────
GRAHAS = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]
GRAHA_NAMES = {
    "sun": "Surya", "moon": "Chandra", "mars": "Mangala", "mercury": "Budha",
    "jupiter": "Guru", "venus": "Shukra", "saturn": "Shani", "rahu": "Rahu", "ketu": "Ketu",
}

# Exaltation: graha -> (sign index, deep degree). Debilitation is the 7th sign from it.
EXALTATION = {
    "sun": (0, 10.0), "moon": (1, 3.0), "mars": (9, 28.0), "mercury": (5, 15.0),
    "jupiter": (3, 5.0), "venus": (11, 27.0), "saturn": (6, 20.0),
    # Nodal exaltation follows the common Taurus/Scorpio convention.
    "rahu": (1, 20.0), "ketu": (7, 20.0),
}

OWN_SIGNS = {
    "sun": [4], "moon": [3], "mars": [0, 7], "mercury": [2, 5],
    "jupiter": [8, 11], "venus": [1, 6], "saturn": [9, 10],
    "rahu": [], "ketu": [],
}

# Moolatrikona: graha -> (sign, start_deg, end_deg). Widely used BPHS table.
MOOLATRIKONA = {
    "sun": (4, 0.0, 20.0), "moon": (1, 3.0, 30.0), "mars": (0, 0.0, 12.0),
    "mercury": (5, 16.0, 20.0), "jupiter": (8, 0.0, 10.0),
    "venus": (6, 0.0, 15.0), "saturn": (10, 0.0, 20.0),
}

# Naisargika (natural) friendship. graha -> {"friends": [...], "enemies": [...]};
# everything else is neutral.
NATURAL_FRIENDS = {
    "sun": {"friends": ["moon", "mars", "jupiter"], "enemies": ["venus", "saturn"]},
    "moon": {"friends": ["sun", "mercury"], "enemies": []},
    "mars": {"friends": ["sun", "moon", "jupiter"], "enemies": ["mercury"]},
    "mercury": {"friends": ["sun", "venus"], "enemies": ["moon"]},
    "jupiter": {"friends": ["sun", "moon", "mars"], "enemies": ["mercury", "venus"]},
    "venus": {"friends": ["mercury", "saturn"], "enemies": ["sun", "moon"]},
    "saturn": {"friends": ["mercury", "venus"], "enemies": ["sun", "moon", "mars"]},
    # Convention: Rahu behaves like Saturn, Ketu like Mars.
    "rahu": {"friends": ["mercury", "venus"], "enemies": ["sun", "moon", "mars"]},
    "ketu": {"friends": ["sun", "moon", "jupiter"], "enemies": ["mercury"]},
}

# Combustion thresholds (degrees from Sun). (normal, retrograde) where they differ.
COMBUSTION_DEG = {
    "moon": (12.0, 12.0), "mars": (17.0, 17.0), "mercury": (14.0, 12.0),
    "jupiter": (11.0, 11.0), "venus": (10.0, 8.0), "saturn": (15.0, 15.0),
}

# Graha drishti (full sign aspects). All grahas aspect the 7th; specials below.
SPECIAL_ASPECTS = {"mars": [4, 8], "jupiter": [5, 9], "saturn": [3, 10]}

# ── Nakshatras ───────────────────────────────────────────────────────────────
NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

# Vimshottari lord cycle starting at Ashwini. Repeats every 9 nakshatras.
DASHA_ORDER = ["ketu", "venus", "sun", "moon", "mars", "rahu", "jupiter", "saturn", "mercury"]
DASHA_YEARS = {
    "ketu": 7, "venus": 20, "sun": 6, "moon": 10, "mars": 7,
    "rahu": 18, "jupiter": 16, "saturn": 19, "mercury": 17,
}
VIMSHOTTARI_TOTAL_YEARS = 120
# Traditional solar year used by Vimshottari implementations (matches JHora default).
DASHA_YEAR_DAYS = 365.25

def nakshatra_lord(nak_index: int) -> str:
    return DASHA_ORDER[nak_index % 9]

# ── Panchanga names ──────────────────────────────────────────────────────────
_TITHI_BASE = ["Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi",
               "Saptami", "Ashtami", "Navami", "Dashami", "Ekadashi", "Dwadashi",
               "Trayodashi", "Chaturdashi"]
TITHIS = ([f"Shukla {t}" for t in _TITHI_BASE] + ["Purnima"]
          + [f"Krishna {t}" for t in _TITHI_BASE] + ["Amavasya"])

YOGAS_27 = ["Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda",
            "Sukarman", "Dhriti", "Shula", "Ganda", "Vriddhi", "Dhruva",
            "Vyaghata", "Harshana", "Vajra", "Siddhi", "Vyatipata", "Variyana",
            "Parigha", "Shiva", "Siddha", "Sadhya", "Shubha", "Shukla",
            "Brahma", "Indra", "Vaidhriti"]

MOVABLE_KARANAS = ["Bava", "Balava", "Kaulava", "Taitila", "Garija", "Vanija", "Vishti"]

def karana_name(karana_index: int) -> str:
    """karana_index 0..59 over the lunar month (each = 6 deg of Moon-Sun elongation)."""
    if karana_index == 0:
        return "Kimstughna"
    if karana_index >= 57:
        return ["Shakuni", "Chatushpada", "Naga"][karana_index - 57]
    return MOVABLE_KARANAS[(karana_index - 1) % 7]

# Vara (weekday) — index matches Python date.weekday() (Monday=0).
VARAS = ["Somavara", "Mangalavara", "Budhavara", "Guruvara",
         "Shukravara", "Shanivara", "Ravivara"]
VARA_LORDS = ["moon", "mars", "mercury", "jupiter", "venus", "saturn", "sun"]

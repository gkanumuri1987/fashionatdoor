"""Parihaaram + an HONEST rational basis for each remedy.

Integrity note: we do NOT claim pseudo-physics (gemstones emitting healing
rays, planets beaming energy). Instead each traditional parihaaram is paired
with its GENUINE psychological / behavioural / wellness mechanism — the reason
a modern, rational mind can see why the practice helps. These mechanisms are
real and studied: circadian alignment, ritual-driven stress reduction, the
prosocial 'helper's high', gratitude, mantra as paced breathing/meditation,
routine building discipline. The graha simply names the life-domain the
practice strengthens.
"""

from __future__ import annotations

# graha -> {deity, practice, rationale}
REMEDY = {
    "sun": {
        "deity": "Surya / Lord Rama",
        "practice": "Offer water to the rising Sun at dawn; recite Aditya Hridayam.",
        "rationale": ("Rising before sunrise and taking in early morning light "
                      "resets your circadian clock — clinically shown to lift "
                      "mood, energy and vitamin-D synthesis. A recited stotra is "
                      "structured, slow breathing that lowers stress. Building a "
                      "steady dawn routine measurably strengthens discipline and "
                      "self-confidence — the very qualities the Sun signifies."),
    },
    "moon": {
        "deity": "Chandra / Lord Shiva",
        "practice": "Offer white flowers to Shiva on Mondays; chant Om Namah Shivaya.",
        "rationale": ("Rhythmic chanting slows the breath and heart rate and "
                      "activates the calming parasympathetic system — meditation "
                      "and mantra are well-documented to reduce anxiety. A weekly "
                      "ritual gives the emotional mind (the Moon's domain) a "
                      "reliable anchor and sense of steadiness."),
    },
    "mars": {
        "deity": "Mangala / Hanuman",
        "practice": "Recite the Hanuman Chalisa on Tuesdays; do disciplined physical service.",
        "rationale": ("Channelling restless Mars energy into disciplined "
                      "exercise or service is a proven anger-management principle "
                      "— physical activity burns stress hormones and builds "
                      "resilience. Reciting the Chalisa aloud is itself a "
                      "vocal-breathing workout that steadies the nerves."),
    },
    "mercury": {
        "deity": "Budha / Lord Vishnu",
        "practice": "Feed green gram to birds; recite Vishnu Sahasranama.",
        "rationale": ("Small acts of feeding and charity trigger the measurable "
                      "'helper's high' — a dopamine-and-oxytocin lift that "
                      "improves mood and social connection, Mercury's domain. "
                      "Memorising verses is a genuine workout for verbal memory "
                      "and mental agility."),
    },
    "jupiter": {
        "deity": "Guru / Dakshinamurthy",
        "practice": "Offer yellow items at a temple on Thursdays; honour your teachers.",
        "rationale": ("Gratitude toward mentors and structured giving are among "
                      "the most robust predictors of life satisfaction in "
                      "psychology research — they widen perspective and wisdom, "
                      "Jupiter's gifts. Turmeric and yellow foods carry real "
                      "anti-inflammatory benefits too."),
    },
    "venus": {
        "deity": "Shukra / Lakshmi",
        "practice": "Offer Lakshmi puja on Fridays; nurture the arts and your relationships.",
        "rationale": ("Engaging with beauty, art and music raises dopamine and "
                      "wellbeing, and deliberately cultivating gratitude and "
                      "harmony in a partnership is clinically shown to strengthen "
                      "it — exactly the relational and creative life Venus "
                      "governs."),
    },
    "saturn": {
        "deity": "Shani / Hanuman",
        "practice": "Light a sesame-oil lamp to Hanuman on Saturdays; serve elders and the needy.",
        "rationale": ("Caregiving, service and volunteering correlate strongly "
                      "with lower depression and even longer life. The humble, "
                      "patient routine Saturn asks for builds the discipline and "
                      "endurance that turn hardship into mastery."),
    },
    "rahu": {
        "deity": "Rahu / Durga",
        "practice": "Take up Durga upasana; read the Durga Saptashati.",
        "rationale": ("A structured devotional practice counters the scattered "
                      "focus and free-floating anxiety Rahu signifies — ritual "
                      "restores a felt sense of control, which lowers stress "
                      "hormones and steadies decision-making."),
    },
    "ketu": {
        "deity": "Ketu / Ganesha",
        "practice": "Begin ventures with Ganesha worship; observe Sankashti Chaturthi.",
        "rationale": ("Opening a task with a short grounding ritual improves "
                      "focus and reduces procrastination. Ketu's domain is "
                      "detachment, and mindfulness practice is measurably "
                      "effective at helping the mind let go and settle."),
    },
}


def remedy_for(graha: str) -> dict:
    return REMEDY.get(graha, {"deity": "", "practice": "", "rationale": ""})

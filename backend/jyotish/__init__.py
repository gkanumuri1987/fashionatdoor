"""Deterministic Jyotish (Vedic astrology) engine.

HARD RULE: this package must never import any AI SDK. Every value it produces
is computed arithmetic over Swiss Ephemeris positions. The AI layer consumes
this package's output as given facts — never the other way around.
"""

ENGINE_VERSION = "1.0.0"

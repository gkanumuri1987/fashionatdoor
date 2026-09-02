"""AI interpretation layer.

HARD RULE (mirror of jyotish/__init__.py): this package never computes an
astronomical or astrological value. It receives the deterministic engine's
ChartV1/MilanV1 output as given facts, retrieves matching classical dictums,
and writes prose. Guardrails scrub every output.
"""

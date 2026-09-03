"""Divisional charts (vargas) per BPHS.

Each function maps a sidereal longitude → varga SIGN index (0=Aries..11=Pisces).
`all_vargas(lon)` returns the standard shodasavarga subset we ship.

Sign parity: "odd" = Aries, Gemini, ... (sign index even → 1st/3rd/... sign,
i.e. sign_num = index+1 is odd when index is even).
"""

from __future__ import annotations

_EPS = 1e-9


def _sign(lon: float) -> int:
    return int((lon % 360.0) // 30)


def _deg(lon: float) -> float:
    return (lon % 360.0) % 30.0


def _part(lon: float, n: int) -> int:
    """Which 1/n division of the sign the longitude falls in (0-based)."""
    return min(n - 1, int((_deg(lon) + _EPS) / (30.0 / n)))


def _is_odd_sign(sign: int) -> bool:
    return sign % 2 == 0  # Aries(0) is the 1st (odd) sign


def d1(lon: float) -> int:
    return _sign(lon)


def d2(lon: float) -> int:
    """Hora: odd signs — first half Sun's hora (Leo), second Moon's (Cancer); even reversed."""
    first_half = _deg(lon) < 15.0
    if _is_odd_sign(_sign(lon)):
        return 4 if first_half else 3
    return 3 if first_half else 4


def d3(lon: float) -> int:
    """Drekkana: 1st/5th/9th from the sign itself."""
    return (_sign(lon) + 4 * _part(lon, 3)) % 12


def d7(lon: float) -> int:
    s = _sign(lon)
    start = s if _is_odd_sign(s) else (s + 6) % 12
    return (start + _part(lon, 7)) % 12


def d9(lon: float) -> int:
    """Navamsa. Equivalent to element-start rule (fire→Aries, earth→Cap, air→Libra, water→Cancer)."""
    return (_sign(lon) * 9 + _part(lon, 9)) % 12


def d10(lon: float) -> int:
    s = _sign(lon)
    start = s if _is_odd_sign(s) else (s + 8) % 12
    return (start + _part(lon, 10)) % 12


def d12(lon: float) -> int:
    return (_sign(lon) + _part(lon, 12)) % 12


_MOBILITY_START_D16 = {"movable": 0, "fixed": 4, "dual": 8}      # Aries / Leo / Sagittarius
_MOBILITY_START_D20 = {"movable": 0, "fixed": 8, "dual": 4}      # Aries / Sagittarius / Leo
_MOBILITY_START_D45 = {"movable": 0, "fixed": 4, "dual": 8}


def _mobility(sign: int) -> str:
    return ("movable", "fixed", "dual")[sign % 3]


def d16(lon: float) -> int:
    return (_MOBILITY_START_D16[_mobility(_sign(lon))] + _part(lon, 16)) % 12


def d20(lon: float) -> int:
    return (_MOBILITY_START_D20[_mobility(_sign(lon))] + _part(lon, 20)) % 12


def d24(lon: float) -> int:
    start = 4 if _is_odd_sign(_sign(lon)) else 3   # Leo / Cancer
    return (start + _part(lon, 24)) % 12


_ELEMENT_START_D27 = [0, 3, 6, 9]  # fire→Aries, earth→Cancer, air→Libra, water→Capricorn


def d27(lon: float) -> int:
    return (_ELEMENT_START_D27[_sign(lon) % 4] + _part(lon, 27)) % 12


# Trimsamsa boundaries: (upper_degree, sign) — BPHS irregular division.
_D30_ODD = [(5.0, 0), (10.0, 10), (18.0, 8), (25.0, 2), (30.0, 6)]
_D30_EVEN = [(5.0, 1), (12.0, 5), (20.0, 11), (25.0, 9), (30.0, 7)]


def d30(lon: float) -> int:
    table = _D30_ODD if _is_odd_sign(_sign(lon)) else _D30_EVEN
    deg = _deg(lon)
    for upper, sign in table:
        if deg + _EPS < upper:  # boundary rounds UP, same convention as _part
            return sign
    return table[-1][1]


def d40(lon: float) -> int:
    start = 0 if _is_odd_sign(_sign(lon)) else 6   # Aries / Libra
    return (start + _part(lon, 40)) % 12


def d45(lon: float) -> int:
    return (_MOBILITY_START_D45[_mobility(_sign(lon))] + _part(lon, 45)) % 12


def d60(lon: float) -> int:
    return (_sign(lon) + _part(lon, 60)) % 12


VARGA_FUNCS = {
    "D1": d1, "D2": d2, "D3": d3, "D7": d7, "D9": d9, "D10": d10, "D12": d12,
    "D16": d16, "D20": d20, "D24": d24, "D27": d27, "D30": d30, "D40": d40,
    "D45": d45, "D60": d60,
}


def all_vargas(lon: float) -> dict[str, int]:
    return {k: f(lon) for k, f in VARGA_FUNCS.items()}

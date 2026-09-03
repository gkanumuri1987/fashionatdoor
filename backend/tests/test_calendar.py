"""Hindu calendar math tests — eras, samvatsara cycle, ahargana, Julian note."""

from datetime import datetime, timezone

import pytest

from jyotish.calendar_hindu import (SAMVATSARA_NAMES, julian_calendar_note,
                                    kali_ahargana, saka_year, samvatsara,
                                    vikrama_year)
from jyotish.ephemeris import julian_day_ut


def _jd(y, m, d):
    return julian_day_ut(datetime(y, m, d, tzinfo=timezone.utc))


def test_ahargana_positive_and_increasing():
    a = kali_ahargana(_jd(2024, 1, 1))
    b = kali_ahargana(_jd(2024, 6, 1))
    assert a > 0
    assert b > a
    assert abs((b - a) - 152.0) < 1e-6  # Jan 1 → Jun 1 2024 (leap) = 152 days


def test_saka_vikrama_2024_06_01():
    jd = _jd(2024, 6, 1)
    assert saka_year(jd) == 1946
    assert vikrama_year(jd) == 2081


def test_saka_vikrama_before_mesha_sankranti():
    # Feb 2024 precedes the Apr 2024 Mesha sankranti → previous era year.
    jd = _jd(2024, 2, 1)
    assert saka_year(jd) == 1945
    assert vikrama_year(jd) == 2080


def test_samvatsara_names_table():
    assert len(SAMVATSARA_NAMES) == 60
    assert len(set(SAMVATSARA_NAMES)) == 60
    assert SAMVATSARA_NAMES[0] == "Prabhava"
    assert SAMVATSARA_NAMES[38] == "Vishvavasu"
    assert SAMVATSARA_NAMES[59] == "Akshaya"


def test_samvatsara_telugu_2025_is_vishvavasu():
    s = samvatsara(_jd(2025, 6, 1), scheme="telugu_lunar")
    assert s["name"] == "Vishvavasu"
    assert s["index"] == 38


def test_samvatsara_tamil_solar():
    s = samvatsara(_jd(2025, 6, 1), scheme="tamil_solar")
    assert s["name"] == "Vishvavasu"
    assert s["scheme"] == "tamil_solar"


def test_samvatsara_north_jupiter_within_one():
    s = samvatsara(_jd(2025, 6, 1), scheme="north_jupiter")
    # Calibrated to the 2025-26 anchor within ±1 (mod 60) of Vishvavasu (38).
    delta = min((s["index"] - 38) % 60, (38 - s["index"]) % 60)
    assert delta <= 1
    assert "differ" in s["note"]  # the honesty note about north/south divergence


def test_samvatsara_unknown_scheme():
    with pytest.raises(ValueError):
        samvatsara(_jd(2025, 6, 1), scheme="nope")


def test_julian_note_fires_pre_1582():
    note = julian_calendar_note(1500, 1, 1)
    assert note is not None and "JULIAN" in note
    assert julian_calendar_note(1582, 10, 14) is not None
    assert julian_calendar_note(1582, 10, 15) is None
    assert julian_calendar_note(2000, 1, 1) is None

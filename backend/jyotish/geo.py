"""Birth place/time → exact UTC instant.

The single biggest source of wrong charts is timezone handling. Rules:

- NEVER apply a zone's *current* UTC offset to a historical date. Always resolve
  the offset through zoneinfo, which carries the full IANA history (India's
  pre-1955 local times, the 1942-45 wartime +6:30 DST, every DST transition).
- lat/lng → IANA zone via timezonefinder when the caller doesn't supply one.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

_TZF = None  # lazy singleton — timezonefinder loads a large polygon index


def tz_from_latlng(lat: float, lng: float) -> str:
    """Resolve the IANA timezone name for coordinates. Raises if unresolvable."""
    global _TZF
    if _TZF is None:
        from timezonefinder import TimezoneFinder
        _TZF = TimezoneFinder()
    tz = _TZF.timezone_at(lat=lat, lng=lng)
    if not tz:
        raise ValueError(f"Could not resolve a timezone for lat={lat}, lng={lng}")
    return tz


@dataclass(frozen=True)
class BirthInstant:
    utc: datetime          # tz-aware UTC datetime
    tz_name: str           # IANA zone used
    utc_offset_hours: float  # offset that was in force at the birth instant


def to_utc(d: date, t: time, tz_name: str | None = None,
           lat: float | None = None, lng: float | None = None) -> BirthInstant:
    """Convert local birth date+time to the exact UTC instant.

    Ambiguous local times (clocks rolled back) resolve to the FIRST occurrence
    (fold=0); nonexistent local times (spring-forward gap) follow zoneinfo's
    standard shift. Both are flagged upstream by the time-accuracy field.
    """
    if tz_name is None:
        if lat is None or lng is None:
            raise ValueError("Either tz_name or lat/lng is required")
        tz_name = tz_from_latlng(lat, lng)
    zone = ZoneInfo(tz_name)
    local = datetime.combine(d, t).replace(tzinfo=zone, fold=0)
    utc_dt = local.astimezone(timezone.utc)
    offset = local.utcoffset() or timedelta(0)
    return BirthInstant(utc=utc_dt, tz_name=tz_name,
                        utc_offset_hours=offset.total_seconds() / 3600.0)

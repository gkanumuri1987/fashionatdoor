"""Pydantic contract for ChartV1 — validated at the API boundary and in tests.

The engine itself builds plain dicts (keeps it dependency-light); this schema
is the guarantee that the shape never drifts silently.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class NakshatraInfo(BaseModel):
    index: int = Field(ge=0, le=26)
    name: str
    pada: int = Field(ge=1, le=4)
    lord: str
    fraction_elapsed: float = Field(ge=0.0, lt=1.0)


class GrahaInfo(BaseModel):
    name: str
    lon: float = Field(ge=0.0, lt=360.0)
    sign: int = Field(ge=0, le=11)
    sign_name: str
    degree_in_sign: str
    house: int = Field(ge=1, le=12)
    retrograde: bool
    combust: bool
    dignity: str
    nakshatra: NakshatraInfo
    vargas: dict[str, int]
    # v1.1: strength + state annotations
    avasthas: Optional[dict] = None
    functional: Optional[dict] = None
    shadbala: Optional[dict] = None


class LagnaInfo(BaseModel):
    lon: float = Field(ge=0.0, lt=360.0)
    sign: int = Field(ge=0, le=11)
    sign_name: str
    degree_in_sign: str
    nakshatra: NakshatraInfo
    lord: str


class BhavaInfo(BaseModel):
    house: int = Field(ge=1, le=12)
    sign: int = Field(ge=0, le=11)
    sign_name: str
    lord: str
    cusp: float
    occupants: list[str]


class AntardashaInfo(BaseModel):
    lord: str
    start_jd: float
    end_jd: float
    start: str
    end: str


class MahadashaInfo(AntardashaInfo):
    years: int
    antardashas: list[AntardashaInfo]


class VimshottariInfo(BaseModel):
    system: Literal["vimshottari"]
    moon_nakshatra: str
    balance_at_birth_years: float
    mahadashas: list[MahadashaInfo] = Field(min_length=9, max_length=9)


class ChartInput(BaseModel):
    date: str
    time: str
    lat: float
    lng: float
    tz: str
    utc: str
    utc_offset_hours: float
    time_accuracy: str
    ayanamsa: str
    house_system: str
    node_type: str


class ChartV1(BaseModel):
    schema_: str = Field(alias="schema")
    engine_version: str
    input: ChartInput
    ayanamsa_value: float
    julian_day_ut: float
    lagna: LagnaInfo
    mc: float
    grahas: dict[str, GrahaInfo]
    bhavas: list[BhavaInfo] = Field(min_length=12, max_length=12)
    aspects: list[dict]
    panchanga: dict
    yogas: list[dict]
    vimshottari: VimshottariInfo
    current_dasha: Optional[dict]
    moon_sign: int
    moon_sign_name: str
    # v1.1: judgment layer
    sunrise_utc: Optional[str] = None
    sunset_utc: Optional[str] = None
    is_day_birth: Optional[bool] = None
    functional_lords: Optional[dict] = None
    shadbala: Optional[dict] = None
    shadbala_summary: Optional[dict] = None
    ashtakavarga: Optional[dict] = None
    graha_yuddha: Optional[list] = None

    model_config = {"populate_by_name": True}

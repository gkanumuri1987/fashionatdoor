"""FashionAtDoor Jyotish API — FastAPI service.

Phase 1 surface: health + chart computation + transit report. Auth (Supabase),
persistence, AI readings, matching, and palmistry land in later phases.
"""

from __future__ import annotations

import logging
from datetime import date as _date
from datetime import datetime, time as _time, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from jyotish import ENGINE_VERSION
from jyotish.chart import compute_chart, transit_report

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fashionatdoor")

app = FastAPI(title="FashionAtDoor Jyotish API", version=ENGINE_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChartRequest(BaseModel):
    date: str = Field(description="Birth date, YYYY-MM-DD")
    time: str = Field(description="Birth time, HH:MM or HH:MM:SS (local)")
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    tz: str | None = Field(default=None, description="IANA zone; derived from lat/lng if omitted")
    ayanamsa: str = Field(default="lahiri", pattern="^(lahiri|raman|kp)$")
    house_system: str = Field(default="whole_sign", pattern="^(whole_sign|placidus|sripati)$")
    node_type: str = Field(default="true", pattern="^(true|mean)$")
    time_accuracy: str = Field(default="exact", pattern="^(exact|approximate|unknown)$")

    @field_validator("date")
    @classmethod
    def _valid_date(cls, v: str) -> str:
        _date.fromisoformat(v)
        return v

    @field_validator("time")
    @classmethod
    def _valid_time(cls, v: str) -> str:
        _time.fromisoformat(v)
        return v


@app.get("/health")
def health():
    return {"ok": True, "engine_version": ENGINE_VERSION}


@app.post("/api/chart")
def chart(body: ChartRequest):
    try:
        result = compute_chart(
            _date.fromisoformat(body.date), _time.fromisoformat(body.time),
            lat=body.lat, lng=body.lng, tz_name=body.tz,
            ayanamsa=body.ayanamsa, house_system=body.house_system,
            node_type=body.node_type, time_accuracy=body.time_accuracy,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:  # pragma: no cover — surface, never swallow
        logger.error("chart computation failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Chart computation failed")
    return result


class TransitRequest(BaseModel):
    chart: dict
    as_of: str | None = None  # ISO datetime, UTC assumed if naive


@app.post("/api/transits")
def transits(body: TransitRequest):
    as_of = None
    if body.as_of:
        as_of = datetime.fromisoformat(body.as_of)
        if as_of.tzinfo is None:
            as_of = as_of.replace(tzinfo=timezone.utc)
    try:
        return transit_report(body.chart, as_of)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid chart payload: {exc}")

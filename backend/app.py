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


from json import JSONDecodeError, dump as _json_dump, load as _json_load
from pathlib import Path as _Path

_GEO_CACHE_FILE = _Path(__file__).resolve().parent / "output" / "geocode_cache.json"
_geo_cache: dict[str, list] | None = None


def _load_geo_cache() -> dict[str, list]:
    global _geo_cache
    if _geo_cache is None:
        try:
            with open(_GEO_CACHE_FILE) as f:
                _geo_cache = _json_load(f)
        except (OSError, JSONDecodeError):
            _geo_cache = {}
    return _geo_cache


def _save_geo_cache() -> None:
    try:
        _GEO_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(_GEO_CACHE_FILE, "w") as f:
            _json_dump(_geo_cache, f)
    except OSError as exc:  # cache is best-effort
        logger.warning("geocode cache write failed: %s", exc)


@app.get("/api/geocode")
def geocode(q: str):
    """Place search via Nominatim (OpenStreetMap), file-cached so repeat
    cities never re-hit the API. Returns [{name, lat, lng}]."""
    q = q.strip().lower()
    if len(q) < 2:
        return []
    cache = _load_geo_cache()
    if q in cache:
        return cache[q]
    import httpx
    try:
        resp = httpx.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": q, "format": "json", "limit": 6, "addressdetails": 0},
            headers={"User-Agent": "fashionatdoor-jyotish/1.0"},
            timeout=10.0,
        )
        resp.raise_for_status()
        results = [
            {"name": r["display_name"], "lat": float(r["lat"]), "lng": float(r["lon"])}
            for r in resp.json()
        ]
    except Exception as exc:
        logger.warning("geocode failed for %r: %s", q, exc)
        raise HTTPException(status_code=502, detail="Place lookup failed — try again")
    cache[q] = results
    _save_geo_cache()
    return results


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

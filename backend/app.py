"""FashionAtDoor Jyotish API — FastAPI service.

Phase 1 surface: health + chart computation + transit report. Auth (Supabase),
persistence, AI readings, matching, and palmistry land in later phases.
"""

from __future__ import annotations

import logging
from datetime import date as _date
from datetime import datetime, time as _time, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from jyotish import ENGINE_VERSION
from jyotish.chart import compute_chart, transit_report
from jyotish.milan import match as milan_match

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fashionatdoor")

app = FastAPI(title="FashionAtDoor Jyotish API", version=ENGINE_VERSION)

import os as _os

_cors = [o.strip() for o in
         _os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors,
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


class MatchRequest(BaseModel):
    boy: ChartRequest
    girl: ChartRequest


@app.post("/api/match")
def match_endpoint(body: MatchRequest):
    def _chart(r: ChartRequest) -> dict:
        return compute_chart(
            _date.fromisoformat(r.date), _time.fromisoformat(r.time),
            lat=r.lat, lng=r.lng, tz_name=r.tz, ayanamsa=r.ayanamsa,
            house_system=r.house_system, node_type=r.node_type,
            time_accuracy=r.time_accuracy,
        )
    try:
        boy, girl = _chart(body.boy), _chart(body.girl)
        result = milan_match(boy, girl)
        result["boy_chart"] = boy
        result["girl_chart"] = girl
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:  # pragma: no cover
        logger.error("match failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Match computation failed")


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


# ── AI readings (interpretation only — never computes) ───────────────────────

class ReadingRequest(BaseModel):
    chart: dict
    section: str = Field(pattern="^(personality|career|wealth|relationships|health|dharma|dasha_outlook|remedies)$")
    language: str = Field(default="en", pattern="^(en|te|hi)$")


@app.post("/api/reading")
def reading(body: ReadingRequest):
    from ai.reading import generate_reading
    result = generate_reading(body.chart, body.section, body.language)
    if result.get("_error"):
        raise HTTPException(status_code=502, detail=result["_error_message"])
    return result


class MatchNarrativeRequest(BaseModel):
    milan: dict
    language: str = Field(default="en", pattern="^(en|te|hi)$")


@app.post("/api/match/narrative")
def match_narrative(body: MatchNarrativeRequest):
    from ai.reading import generate_match_narrative
    result = generate_match_narrative(body.milan, body.language)
    if result.get("_error"):
        raise HTTPException(status_code=502, detail=result["_error_message"])
    return result


# ── Palmistry sessions (tokenized shareable link) ────────────────────────────

@app.post("/api/palm/sessions")
def palm_create():
    from store import palm_sessions
    s = palm_sessions.create_session()
    return {"token": s["token"], "path": f"/palm/{s['token']}",
            "expires_at": s["expires_at"]}


@app.get("/api/palm/sessions/{token}")
def palm_get(token: str):
    from store import palm_sessions
    s = palm_sessions.get_session(token)
    if s is None:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    return s


@app.post("/api/palm/sessions/{token}/upload")
async def palm_upload(token: str, request: Request,
                      language: str = "en"):
    """Accepts multipart images (fields named photo/photo2 or any files).
    RETENTION: image bytes live only in memory for this request — analyzed,
    then discarded. Only derived JSON is stored."""
    from store import palm_sessions
    if palm_sessions.get_session(token) is None:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    from imaging import MAX_UPLOAD_BYTES, normalize_image
    form = await request.form()
    images: list[bytes] = []
    problems: list[str] = []
    for value in form.values():
        if not hasattr(value, "read"):
            continue
        raw = await value.read()
        if not raw:
            continue
        if len(raw) > MAX_UPLOAD_BYTES:
            problems.append(f"a photo is {len(raw) // (1024*1024)} MB — please "
                            "use your camera app's smaller size or retake")
            continue
        norm = normalize_image(raw)
        if norm is None:
            problems.append("a photo is in a format this device couldn't read "
                            "— please retake with the camera or use JPG/PNG")
            continue
        images.append(norm)
    if not images:
        raise HTTPException(status_code=400,
                            detail="; ".join(problems) or "No photo received")
    if language not in ("en", "te", "hi"):
        language = "en"

    from ai.palm import analyze_palm
    result = analyze_palm(images[:2], language=language)
    if result.get("_error"):
        raise HTTPException(status_code=502, detail=result["_error_message"])
    s = palm_sessions.save_result(token, result)
    return s


# ── Tier-2: alternate dasha systems ─────────────────────────────────────────

class DashaRequest(BaseModel):
    chart: dict
    system: str = Field(default="yogini",
                        pattern="^(yogini|ashtottari|kalachakra|narayana|vimshottari_360)$")


@app.post("/api/dashas")
def alternate_dashas(body: DashaRequest):
    """Alternate dasha systems computed from an existing ChartV1:
    yogini | ashtottari | kalachakra | narayana | vimshottari_360 (savana year)."""
    from jyotish.dasha_advanced import (kalachakra, narayana_dasha,
                                        vimshottari_with_year)
    from jyotish.dasha_extra import ashtottari_dasha, yogini_dasha
    try:
        moon_lon = body.chart["grahas"]["moon"]["lon"]
        sun_lon = body.chart["grahas"]["sun"]["lon"]
        birth_jd = body.chart["julian_day_ut"]
        positions = {g: {"lon": gd["lon"]} for g, gd in body.chart["grahas"].items()}
        lagna_sign = body.chart["lagna"]["sign"]
    except (KeyError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid chart payload: {exc}")
    if body.system == "yogini":
        return yogini_dasha(moon_lon, birth_jd)
    if body.system == "kalachakra":
        return kalachakra(moon_lon, birth_jd)
    if body.system == "narayana":
        return narayana_dasha(lagna_sign, positions, birth_jd)
    if body.system == "vimshottari_360":
        return vimshottari_with_year(moon_lon, birth_jd, year_days=360.0)
    lagna_lord = body.chart["lagna"]["lord"]
    lagna_lord_sign = body.chart["grahas"].get(lagna_lord, {}).get("sign")
    rahu_sign = body.chart["grahas"]["rahu"]["sign"]
    return ashtottari_dasha(moon_lon, sun_lon, birth_jd,
                            rahu_sign=rahu_sign, lagna_lord_sign=lagna_lord_sign)


# ── Tier-2: muhurta chooser ─────────────────────────────────────────────────

class MuhurtaRequest(BaseModel):
    start_date: str = Field(description="YYYY-MM-DD")
    days: int = Field(default=14, ge=1, le=60)
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    natal_moon_nakshatra: int | None = Field(default=None, ge=0, le=26)
    natal_moon_sign: int | None = Field(default=None, ge=0, le=11)
    ayanamsa: str = Field(default="lahiri", pattern="^(lahiri|raman|kp)$")


@app.post("/api/muhurta")
def muhurta(body: MuhurtaRequest):
    from jyotish.muhurta import scan_days
    try:
        start = _date.fromisoformat(body.start_date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"days": scan_days(start, body.days, body.lat, body.lng,
                              natal_moon_nak=body.natal_moon_nakshatra,
                              natal_moon_sign=body.natal_moon_sign,
                              ayanamsa=body.ayanamsa)}


# ── Tier-2: Vastu floor-plan analysis ───────────────────────────────────────

from fastapi import File, Form, UploadFile

_VASTU_DIRECTIONS = {"N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                     "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"}


@app.post("/api/vastu")
async def vastu_analyze(plan: UploadFile = File(...),
                        top_direction: str = Form("N"),
                        language: str = Form("en")):
    """Floor plan photo + which compass direction the image's TOP faces.
    The image is analyzed in memory and never stored."""
    if top_direction not in _VASTU_DIRECTIONS:
        raise HTTPException(status_code=400, detail="top_direction must be a compass point (N, NE, …)")
    if language not in ("en", "te", "hi"):
        language = "en"
    from imaging import MAX_UPLOAD_BYTES, normalize_image
    raw = await plan.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Plan image missing")
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400,
                            detail=f"Plan image is {len(raw) // (1024*1024)} MB — "
                                   "please use a smaller export or photo")
    norm = normalize_image(raw)
    if norm is None:
        raise HTTPException(status_code=400,
                            detail="Could not read this image format — please "
                                   "upload a JPG or PNG of the floor plan")
    from ai.vastu import analyze_floor_plan
    result = analyze_floor_plan(norm, top_direction, language=language,
                                mime_type="image/jpeg")
    if result.get("_error"):
        raise HTTPException(status_code=502, detail=result["_error_message"])
    return result


# ── Tier-2: Western tropical chart ──────────────────────────────────────────

@app.post("/api/western")
def western(body: ChartRequest):
    from jyotish.western import western_chart
    try:
        return western_chart(
            _date.fromisoformat(body.date), _time.fromisoformat(body.time),
            lat=body.lat, lng=body.lng, tz_name=body.tz,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:  # pragma: no cover
        logger.error("western chart failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Western chart computation failed")


# ── Tier-2: Varshaphal (Tajika annual chart) ────────────────────────────────

class VarshaphalRequest(BaseModel):
    chart: dict
    year_number: int = Field(ge=1, le=120)


@app.post("/api/varshaphal")
def varshaphal_endpoint(body: VarshaphalRequest):
    from jyotish.varshaphal import varshaphal
    try:
        return varshaphal(body.chart, body.year_number)
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid chart payload: {exc}")
    except Exception as exc:  # pragma: no cover
        logger.error("varshaphal failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Varshaphal computation failed")


# ── Rectification screening ─────────────────────────────────────────────────

class RectifyRequest(BaseModel):
    date: str
    time: str
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    tz: str | None = None
    band_minutes: int = Field(default=30, ge=2, le=120)
    step_minutes: int = Field(default=2, ge=1, le=30)


@app.post("/api/rectify")
def rectify_endpoint(body: RectifyRequest):
    from jyotish.rectify import rectify
    try:
        return rectify(_date.fromisoformat(body.date), _time.fromisoformat(body.time),
                       lat=body.lat, lng=body.lng, tz_name=body.tz,
                       band_minutes=body.band_minutes, step_minutes=body.step_minutes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ── Presentation contract (deterministic — no AI) ───────────────────────────

class ReadingPageRequest(BaseModel):
    chart: dict
    language: str = Field(default="en", pattern="^(en|te|hi)$")


@app.post("/api/reading-page")
def reading_page_endpoint(body: ReadingPageRequest):
    """ReadingPageV1: strength bars, receipted claims, resolved verdicts,
    dasha timeline, glosses, uncertainty — all computed, none written by AI."""
    from ai.presentation import reading_page
    try:
        return reading_page(body.chart, body.language)
    except (KeyError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid chart payload: {exc}")


# ── Traditional (Surya Siddhanta) vs drik comparison ────────────────────────

@app.post("/api/siddhanta-compare")
def siddhanta_compare(body: TransitRequest):
    """Side-by-side classical Surya-Siddhanta vs Swiss-Ephemeris positions for
    the chart's birth instant (transparency view; drik remains the default)."""
    from jyotish.siddhanta import compare_with_drik
    try:
        jd = body.chart["julian_day_ut"]
        ay = body.chart["input"]["ayanamsa"]
        return compare_with_drik(jd, ayanamsa=ay)
    except (KeyError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid chart payload: {exc}")

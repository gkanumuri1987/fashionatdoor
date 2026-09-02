# FashionAtDoor — Jyotish AI

Indian (Vedic/Hindu) astrology application: birth chart (kundli) computation, AI life
readings grounded in classical texts and Puranic archetypes, Kundli Milan matching,
and a shareable palmistry photo-analysis flow.

## Core architectural rule — two layers, never mixed

1. **Deterministic layer (`backend/jyotish/`, zero AI imports):** every number —
   planetary longitudes, ascendant, houses, nakshatra/pada, divisional charts (vargas),
   Vimshottari dasha, yogas, panchanga. Pure Python over Swiss Ephemeris, unit-tested.
   Output is one canonical **ChartV1 JSON**.
2. **AI layer (`backend/ai/`):** receives the computed chart JSON as *given facts* plus
   retrieved classical dictums, and writes the reading. It never computes, never guesses
   a date, never invents a planetary position.

## Stack

- **Backend:** FastAPI (Python 3.13), Swiss Ephemeris via `pyswisseph`
- **Frontend:** Next.js 16 (App Router), Tailwind
- **DB/Auth:** Supabase
- **AI:** Gemini (interpretation + palm vision only — never chart math)

## Dev setup

```bash
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/pytest tests/            # engine must be green before anything else
.venv/bin/uvicorn app:app --reload --port 8000
```

## Ephemeris notes

- Default computation uses the built-in **Moshier** analytical ephemeris (no data
  files needed, ~0.1″ planetary accuracy). If Swiss Ephemeris data files (`*.se1`)
  are placed in `backend/ephe/`, the engine upgrades to them automatically.
- Sidereal default: **Lahiri (Chitrapaksha)**. `raman` and `kp` (Krishnamurti)
  are selectable per request.
- **Licence:** Swiss Ephemeris / pyswisseph is AGPL-3.0. Before commercial hosted
  launch: open-source the server, buy Astrodienst's commercial licence, or swap
  `jyotish/ephemeris.py` for an MIT alternative. Tracked as a launch blocker.

## Correctness bar

Golden tests in `backend/tests/` pin engine output; charts are cross-verified
manually against **Jagannatha Hora** (see `scripts/verify_chart.py`). A failing
engine test blocks all downstream work.

"""
api.py — FastAPI REST server for solar profiles data.

Run:
    uvicorn solar_profiles.api:app --reload --port 8000

Endpoints:
    GET /countries
    GET /profile/{country}
    GET /summary/{country}
    GET /compare?countries=Germany,France,Japan
    GET /top?n=10&metric=daily_energy
    GET /search?q=land
    GET /health
"""
from __future__ import annotations

from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd

from .core import SolarProfiles, HOUR_COLS

app = FastAPI(
    title="🌞 Global Solar Profiles API",
    description=(
        "PVWatts-equivalent solar AC power generation profiles for **197 countries**, "
        "January 1st, 24-hour local-time resolution. "
        "4 kW DC system, standard crystalline silicon module, 14% system losses."
    ),
    version="1.0.0",
    contact={"name": "Solar Profiles", "url": "https://github.com/YOUR_USERNAME/solar-profiles"},
    license_info={"name": "MIT"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Load data once at startup
_sp = SolarProfiles()


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/health", tags=["meta"])
def health():
    """Health check."""
    return {"status": "ok", "countries_loaded": len(_sp.countries)}


@app.get("/countries", tags=["data"])
def list_countries():
    """Return all available country names."""
    return {"count": len(_sp.countries), "countries": _sp.countries}


@app.get("/profile/{country}", tags=["data"])
def get_profile(country: str):
    """
    24-hour AC power profile (W) for a single country in local time.
    Hour 0 = midnight, Hour 12 = noon.
    """
    try:
        arr = _sp.hourly_array(country)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {
        "country": country,
        "date": "January 1",
        "time_reference": "local solar time (midnight=0, noon=12)",
        "unit": "watts_ac",
        "system_capacity_dc_kw": 4.0,
        "hourly_profile": {f"{h:02d}:00": round(float(arr[h]), 2) for h in range(24)},
    }


@app.get("/summary/{country}", tags=["data"])
def get_summary(country: str):
    """Full metadata + summary statistics for a country."""
    try:
        return _sp.summary(country)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/compare", tags=["data"])
def compare_countries(
    countries: str = Query(
        ...,
        description="Comma-separated list of country names, e.g. Germany,France,Japan",
        examples={"default": {"value": "Germany,France,Japan"}},
    )
):
    """
    Compare hourly AC power profiles for multiple countries side-by-side.
    Returns a table with one row per hour.
    """
    country_list = [c.strip() for c in countries.split(",") if c.strip()]
    if len(country_list) < 2:
        raise HTTPException(status_code=400, detail="Provide at least 2 comma-separated countries.")
    if len(country_list) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 countries per request.")
    try:
        df = _sp.compare(country_list)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {
        "countries": country_list,
        "unit": "watts_ac",
        "data": df.to_dict(orient="records"),
    }


@app.get("/top", tags=["data"])
def top_countries(
    n: int = Query(10, ge=1, le=197, description="Number of top countries to return"),
    metric: str = Query(
        "daily_energy",
        description="Ranking metric: daily_energy | peak_ac | daylight_hours",
    ),
):
    """Return the top-N countries ranked by a solar metric."""
    try:
        df = _sp.top_n(n=n, metric=metric)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"metric": metric, "top_n": n, "results": df.to_dict(orient="records")}


@app.get("/search", tags=["data"])
def search_countries(q: str = Query(..., description="Partial country name to search")):
    """Case-insensitive partial search across country names."""
    matches = _sp.search(q)
    return {"query": q, "matches": matches, "count": len(matches)}


@app.get("/all", tags=["data"])
def get_all():
    """Return the full dataset as JSON (all countries, all hours)."""
    df = _sp.dataframe.reset_index()
    return {"count": len(df), "data": df.to_dict(orient="records")}

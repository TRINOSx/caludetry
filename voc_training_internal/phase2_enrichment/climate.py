"""
Phase 2 — Climate History Enrichment

Fetches historical weather data for the project location and time range.
Merges with sensor data to provide context for VOC patterns.

Data sources:
  - OpenWeatherMap History API (requires API key)
  - Open-Meteo (free, no key needed — fallback)

Output: climate_{project_id}.csv
  timestamp | temp_air | humidity_air | wind_speed | wind_dir |
  pressure | precipitation | cloud_cover | uv_index | dew_point
"""
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import ProjectConfig


def _retry_get(url: str, params: dict = None, max_retries: int = 3, timeout: int = 30) -> requests.Response:
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, params=params, timeout=timeout)
            resp.raise_for_status()
            return resp
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** (attempt + 1))


def fetch_open_meteo(
    lat: float,
    lon: float,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """
    Fetch hourly climate data from Open-Meteo (free, no API key).
    This is the primary/fallback source.
    """
    # Format dates as YYYY-MM-DD
    start = start_date[:10]
    end = end_date[:10] if end_date else datetime.now().strftime("%Y-%m-%d")

    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start,
        "end_date": end,
        "hourly": ",".join([
            "temperature_2m", "relative_humidity_2m", "dew_point_2m",
            "precipitation", "rain", "surface_pressure",
            "cloud_cover", "wind_speed_10m", "wind_direction_10m",
            "soil_temperature_0cm", "soil_temperature_6cm",
            "soil_moisture_0_to_1cm", "soil_moisture_1_to_3cm",
            "et0_fao_evapotranspiration",
        ]),
        "timezone": "UTC",
    }

    print(f"[climate] Fetching Open-Meteo: {start} to {end} at ({lat}, {lon})")
    resp = _retry_get(url, params=params, timeout=60)
    data = resp.json()

    if "hourly" not in data:
        print(f"[climate] Warning: no hourly data returned. Response: {list(data.keys())}")
        return pd.DataFrame()

    hourly = data["hourly"]
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(hourly.get("time", [])),
        "temp_air_c": hourly.get("temperature_2m", []),
        "humidity_air_pct": hourly.get("relative_humidity_2m", []),
        "dew_point_c": hourly.get("dew_point_2m", []),
        "precipitation_mm": hourly.get("precipitation", []),
        "rain_mm": hourly.get("rain", []),
        "pressure_hpa": hourly.get("surface_pressure", []),
        "cloud_cover_pct": hourly.get("cloud_cover", []),
        "wind_speed_ms": hourly.get("wind_speed_10m", []),
        "wind_direction_deg": hourly.get("wind_direction_10m", []),
        "soil_temp_0cm_c": hourly.get("soil_temperature_0cm", []),
        "soil_temp_6cm_c": hourly.get("soil_temperature_6cm", []),
        "soil_moisture_0_1cm": hourly.get("soil_moisture_0_to_1cm", []),
        "soil_moisture_1_3cm": hourly.get("soil_moisture_1_to_3cm", []),
        "evapotranspiration_mm": hourly.get("et0_fao_evapotranspiration", []),
    })

    print(f"[climate] Fetched {len(df)} hourly records")
    return df


def fetch_openweather_history(
    lat: float,
    lon: float,
    start_unix: int,
    end_unix: int,
    api_key: str,
) -> pd.DataFrame:
    """
    Fetch historical weather from OpenWeatherMap (requires paid API).
    Used as supplementary source if API key is provided.
    """
    if not api_key:
        return pd.DataFrame()

    url = "https://history.openweathermap.org/data/2.5/history/city"
    params = {
        "lat": lat,
        "lon": lon,
        "type": "hour",
        "start": start_unix,
        "end": end_unix,
        "appid": api_key,
    }

    print(f"[climate] Fetching OpenWeatherMap history...")
    try:
        resp = _retry_get(url, params=params, timeout=60)
        data = resp.json()

        rows = []
        for entry in data.get("list", []):
            main = entry.get("main", {})
            wind = entry.get("wind", {})
            rows.append({
                "timestamp": datetime.fromtimestamp(entry["dt"]),
                "temp_air_c": main.get("temp", 0) - 273.15,  # K to C
                "humidity_air_pct": main.get("humidity", 0),
                "pressure_hpa": main.get("pressure", 0),
                "wind_speed_ms": wind.get("speed", 0),
                "wind_direction_deg": wind.get("deg", 0),
            })

        df = pd.DataFrame(rows)
        print(f"[climate] OpenWeather: {len(df)} records")
        return df
    except Exception as e:
        print(f"[climate] OpenWeather failed: {e}")
        return pd.DataFrame()


def run_climate_enrichment(config: ProjectConfig) -> Path:
    """
    Fetch and save climate history for the project.

    Returns path to climate CSV.
    """
    out_path = config.enriched_dir / f"climate_{config.project_id}.csv"

    if out_path.exists():
        print(f"[climate] Already exists: {out_path}")
        return out_path

    # Primary: Open-Meteo (free)
    end_date = config.end_date or datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    df = fetch_open_meteo(
        config.latitude, config.longitude,
        config.start_date, end_date,
    )

    if df.empty:
        print("[climate] No data fetched. Creating empty placeholder.")
        df = pd.DataFrame(columns=[
            "timestamp", "temp_air_c", "humidity_air_pct", "dew_point_c",
            "precipitation_mm", "pressure_hpa", "wind_speed_ms",
        ])

    config.ensure_dirs()
    df.to_csv(out_path, index=False)
    print(f"[climate] Saved → {out_path}")
    return out_path

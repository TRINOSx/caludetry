"""
Phase 2 — Google AlphaEarth / Earth Engine Enrichment

Fetches geospatial data for the project location:
  - Soil type classification
  - NDVI vegetation index (historical)
  - Land use / land cover
  - Elevation and slope
  - Historical burn scars / deforestation

Uses Google Earth Engine API if credentials are available,
otherwise falls back to publicly available datasets.

Output: alpha_earth_{project_id}.json
"""
import json
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import ProjectConfig


def fetch_soil_data(lat: float, lon: float) -> dict:
    """
    Fetch soil type data from SoilGrids REST API (ISRIC).
    Free, no API key needed.
    """
    url = "https://rest.isric.org/soilgrids/v2.0/properties/query"
    params = {
        "lon": lon,
        "lat": lat,
        "property": ["clay", "sand", "silt", "phh2o", "soc", "nitrogen", "cec", "ocd"],
        "depth": ["0-5cm", "5-15cm", "15-30cm"],
        "value": ["mean"],
    }

    print(f"[alpha_earth] Fetching SoilGrids data at ({lat}, {lon})...")
    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        # Parse soil properties
        soil = {"source": "ISRIC SoilGrids v2.0"}
        for prop in data.get("properties", {}).get("layers", []):
            name = prop["name"]
            depths = prop.get("depths", [])
            soil[name] = {}
            for d in depths:
                depth_label = d["label"]
                values = d.get("values", {})
                soil[name][depth_label] = values.get("mean")

        print(f"[alpha_earth] SoilGrids: {len(soil) - 1} properties")
        return soil

    except Exception as e:
        print(f"[alpha_earth] SoilGrids error: {e}")
        return {"source": "SoilGrids", "error": str(e)}


def fetch_elevation(lat: float, lon: float) -> dict:
    """Fetch elevation data from Open-Elevation API."""
    url = "https://api.open-elevation.com/api/v1/lookup"
    params = {"locations": f"{lat},{lon}"}

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [{}])
        elev = results[0].get("elevation", 0) if results else 0
        return {"elevation_m": elev, "source": "Open-Elevation"}
    except Exception as e:
        return {"elevation_m": 0, "error": str(e)}


def fetch_ndvi_proxy(lat: float, lon: float, config: ProjectConfig) -> dict:
    """
    Get NDVI data. If GEE project is configured, use Earth Engine.
    Otherwise return placeholder for manual integration.
    """
    if config.google_earth_engine_project:
        # GEE integration would go here
        # Requires: pip install earthengine-api
        # ee.Initialize(project=config.google_earth_engine_project)
        return {
            "source": "Google Earth Engine",
            "note": "GEE integration configured. Run with earthengine-api installed.",
            "project": config.google_earth_engine_project,
            "datasets": [
                "COPERNICUS/S2_SR_HARMONIZED",  # Sentinel-2 NDVI
                "MODIS/061/MOD13Q1",             # MODIS vegetation indices
                "LANDSAT/LC09/C02/T1_L2",        # Landsat 9
            ],
        }

    return {
        "source": "placeholder",
        "note": "Set google_earth_engine_project in config for real NDVI data",
        "ndvi_typical_range": [0.2, 0.8],
        "datasets_available": [
            "Sentinel-2 (10m, 5-day revisit)",
            "MODIS (250m, daily)",
            "Landsat 9 (30m, 16-day revisit)",
        ],
    }


def fetch_land_cover(lat: float, lon: float) -> dict:
    """
    Fetch land cover classification from ESA WorldCover.
    Placeholder — requires GEE or direct tile download.
    """
    return {
        "source": "ESA WorldCover 2021",
        "note": "10m resolution global land cover",
        "classes": {
            10: "Tree cover",
            20: "Shrubland",
            30: "Grassland",
            40: "Cropland",
            50: "Built-up",
            60: "Bare / sparse vegetation",
            70: "Snow and ice",
            80: "Permanent water bodies",
            90: "Herbaceous wetland",
            95: "Mangroves",
            100: "Moss and lichen",
        },
        "query_location": {"lat": lat, "lon": lon},
    }


def run_alpha_earth_enrichment(config: ProjectConfig) -> Path:
    """
    Fetch and save geospatial data for the project location.
    Returns path to JSON file.
    """
    out_path = config.enriched_dir / f"alpha_earth_{config.project_id}.json"

    if out_path.exists():
        print(f"[alpha_earth] Already exists: {out_path}")
        return out_path

    config.ensure_dirs()

    data = {
        "location": {
            "latitude": config.latitude,
            "longitude": config.longitude,
            "name": config.location_name,
        },
    }

    # Soil data (free)
    data["soil"] = fetch_soil_data(config.latitude, config.longitude)

    # Elevation (free)
    data["elevation"] = fetch_elevation(config.latitude, config.longitude)

    # NDVI / Satellite
    data["vegetation"] = fetch_ndvi_proxy(config.latitude, config.longitude, config)

    # Land cover
    data["land_cover"] = fetch_land_cover(config.latitude, config.longitude)

    data["_meta"] = {
        "generated_at": __import__("datetime").datetime.now().isoformat(),
    }

    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"[alpha_earth] Saved → {out_path}")
    return out_path

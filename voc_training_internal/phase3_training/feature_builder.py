"""
Phase 3 — Feature Builder

Combines ALL data sources into a unified feature matrix for ML training:
  - Phase 1: Raw sensor readings (26 channels) + auto-tags
  - Phase 2: Climate, seed VOC, microorganism, agrochemical, geospatial enrichment

Output: training_features_{project_id}.csv
  Each row = one time-step with:
    [26 sensor channels] + [climate context] + [enrichment features] + [labels]

Feature groups:
  1. Sensor raw (26 channels)
  2. Sensor derived (ratios, deltas, rolling stats)
  3. Climate context (temp, humidity, rain, wind, pressure)
  4. Soil context (N, P, K, pH, EC, moisture)
  5. Time features (hour, day_of_week, day_of_year, moon_phase)
  6. VOC target labels (from enrichment: expected compounds for current conditions)
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import ProjectConfig, ALL_SENSOR_CHANNELS


def load_phase1_data(config: ProjectConfig) -> pd.DataFrame:
    """Load tagged sensor data from Phase 1."""
    tagged_pattern = config.raw_dir / f"sensor_readings_{config.project_id}_tagged.csv"
    if tagged_pattern.exists():
        return pd.read_csv(tagged_pattern)

    # Fallback to untagged
    raw_pattern = config.raw_dir / f"sensor_readings_{config.project_id}.csv"
    if raw_pattern.exists():
        return pd.read_csv(raw_pattern)

    raise FileNotFoundError(f"No Phase 1 data found in {config.raw_dir}")


def load_enrichment_json(path: Path) -> dict:
    """Safely load enrichment JSON."""
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add time-based features from timestamp."""
    if "timestamp" not in df.columns:
        return df

    ts = pd.to_datetime(df["timestamp"], errors="coerce")
    df["hour"] = ts.dt.hour
    df["day_of_week"] = ts.dt.dayofweek
    df["day_of_year"] = ts.dt.dayofyear
    df["is_daytime"] = ((ts.dt.hour >= 6) & (ts.dt.hour < 20)).astype(int)

    # Cyclical encoding for hour (sin/cos)
    df["hour_sin"] = np.sin(2 * np.pi * ts.dt.hour / 24)
    df["hour_cos"] = np.cos(2 * np.pi * ts.dt.hour / 24)
    df["day_sin"] = np.sin(2 * np.pi * ts.dt.dayofyear / 365)
    df["day_cos"] = np.cos(2 * np.pi * ts.dt.dayofyear / 365)

    return df


def add_sensor_derived(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived features from sensor channels."""
    # Gas ratios (biologically meaningful)
    if "dfrobot_etoh" in df.columns and "dfrobot_hcho" in df.columns:
        df["ratio_etoh_hcho"] = df["dfrobot_etoh"] / (df["dfrobot_hcho"] + 1e-6)

    if "dfrobot_co" in df.columns and "dfrobot_ch4" in df.columns:
        df["ratio_co_ch4"] = df["dfrobot_co"] / (df["dfrobot_ch4"] + 1e-6)

    if "dfrobot_h2s" in df.columns and "dfrobot_h2" in df.columns:
        df["ratio_h2s_h2"] = df["dfrobot_h2s"] / (df["dfrobot_h2"] + 1e-6)

    if "dfrobot_voc" in df.columns and "dfrobot_co" in df.columns:
        df["ratio_voc_co"] = df["dfrobot_voc"] / (df["dfrobot_co"] + 1e-6)

    # TGS cross-sensitivity pattern (defense VOC indicator)
    tgs_cols = [c for c in df.columns if c.startswith("tgs_")]
    if len(tgs_cols) >= 2:
        df["tgs_mean"] = df[tgs_cols].mean(axis=1)
        df["tgs_std"] = df[tgs_cols].std(axis=1)
        df["tgs_min"] = df[tgs_cols].min(axis=1)

    # BME688 derived
    if "bme688_temperature" in df.columns and "bme688_humidity" in df.columns:
        # Vapor pressure deficit (VPD) — key for plant stress
        T = df["bme688_temperature"]
        RH = df["bme688_humidity"]
        svp = 0.6108 * np.exp(17.27 * T / (T + 237.3))
        df["vpd_kpa"] = svp * (1 - RH / 100)

    if "bme688_gas_resistance" in df.columns:
        df["bme688_gas_log"] = np.log1p(df["bme688_gas_resistance"])

    # Soil fertility index
    soil_cols = ["soil_nitrogen", "soil_phosphorus", "soil_potassium"]
    present_soil = [c for c in soil_cols if c in df.columns]
    if present_soil:
        df["soil_npk_index"] = df[present_soil].sum(axis=1) / len(present_soil)

    # Rolling statistics for key channels (VOC dynamics)
    for col in ["dfrobot_voc", "dfrobot_etoh", "dfrobot_h2s", "bme688_gas_resistance"]:
        if col in df.columns:
            df[f"{col}_roll5_mean"] = df[col].rolling(5, min_periods=1).mean()
            df[f"{col}_roll5_std"] = df[col].rolling(5, min_periods=1).std().fillna(0)
            df[f"{col}_delta"] = df[col].diff().fillna(0)

    return df


def add_climate_context(df: pd.DataFrame, config: ProjectConfig) -> pd.DataFrame:
    """Merge climate enrichment data (hourly) with sensor data."""
    climate_path = config.enriched_dir / f"climate_{config.project_id}.csv"
    if not climate_path.exists():
        print("[features] No climate data, skipping merge")
        return df

    climate = pd.read_csv(climate_path)
    if climate.empty or "timestamp" not in climate.columns:
        return df

    climate["timestamp"] = pd.to_datetime(climate["timestamp"])
    climate["timestamp_hour"] = climate["timestamp"].dt.floor("h")

    if "timestamp" in df.columns:
        df["timestamp_dt"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df["timestamp_hour"] = df["timestamp_dt"].dt.floor("h")
        df = df.merge(climate, on="timestamp_hour", how="left", suffixes=("", "_climate"))
        df.drop(columns=["timestamp_hour", "timestamp_dt", "timestamp_climate"], errors="ignore", inplace=True)

    return df


def build_enrichment_features(config: ProjectConfig) -> dict:
    """
    Extract static enrichment features from Phase 2 JSON files.
    These are the same for every row (global context).
    """
    features = {}

    # Seed VOC — count of expected biomarkers per condition
    seed_path = config.enriched_dir / f"seed_voc_{config.project_id}.json"
    seed_data = load_enrichment_json(seed_path)
    if seed_data:
        profiles = seed_data.get("voc_profiles", {})
        for condition, vocs in profiles.items():
            if isinstance(vocs, list):
                features[f"seed_voc_count_{condition}"] = len(vocs)

        biomarkers = seed_data.get("key_biomarkers", [])
        features["seed_biomarker_count"] = len(biomarkers)

    # Microorganisms — pathogen count and threat level
    micro_path = config.enriched_dir / f"microorganisms_{config.project_id}.json"
    micro_data = load_enrichment_json(micro_path)
    if micro_data:
        features["pathogen_count"] = len(micro_data.get("crop_pathogens", []))
        features["soil_microbe_count"] = len(micro_data.get("soil_microbiome", []))
        features["regional_threat_count"] = len(micro_data.get("regional_threats", []))

    # Agrochemicals — product count
    agro_path = config.enriched_dir / f"agrochemicals_{config.project_id}.json"
    agro_data = load_enrichment_json(agro_path)
    if agro_data:
        features["fertilizer_count"] = len(agro_data.get("fertilizers", []))
        features["pesticide_count"] = len(agro_data.get("pesticides", []))

    # AlphaEarth — soil properties
    earth_path = config.enriched_dir / f"alpha_earth_{config.project_id}.json"
    earth_data = load_enrichment_json(earth_path)
    if earth_data:
        elev = earth_data.get("elevation", {})
        features["elevation_m"] = elev.get("elevation_m", 0)

        soil = earth_data.get("soil", {})
        for prop in ["clay", "sand", "silt", "phh2o", "soc", "nitrogen"]:
            vals = soil.get(prop, {})
            if isinstance(vals, dict):
                top_val = vals.get("0-5cm")
                if top_val is not None:
                    features[f"soil_{prop}_0_5cm"] = top_val

    return features


def generate_labels(df: pd.DataFrame, config: ProjectConfig) -> pd.DataFrame:
    """
    Generate training labels from tags and sensor patterns.

    Label columns:
      - plant_state: 0=healthy, 1=mild_stress, 2=severe_stress, 3=pest, 4=flowering
      - stress_pct: continuous 0-100
      - has_soil_event: binary
      - air_quality: 0=good, 1=moderate, 2=poor
    """
    n = len(df)

    # Plant state from tags
    plant_state = np.zeros(n, dtype=int)
    stress_pct = np.zeros(n, dtype=float)

    if "tags" in df.columns:
        for i, tags_str in enumerate(df["tags"]):
            try:
                tags = json.loads(tags_str) if isinstance(tags_str, str) else []
            except json.JSONDecodeError:
                tags = []

            if "stress_severe" in tags:
                plant_state[i] = 2
                stress_pct[i] = 80 + np.random.uniform(0, 20)
            elif "stress_mild" in tags:
                plant_state[i] = 1
                stress_pct[i] = 30 + np.random.uniform(0, 30)
            elif "possible_pest_defense" in tags:
                plant_state[i] = 3
                stress_pct[i] = 60 + np.random.uniform(0, 30)
            elif "stress_event" in tags:
                plant_state[i] = 2
                stress_pct[i] = 70 + np.random.uniform(0, 30)
            else:
                stress_pct[i] = np.random.uniform(0, 15)

    df["label_plant_state"] = plant_state
    df["label_stress_pct"] = stress_pct

    # Soil event label
    df["label_soil_event"] = 0
    if "tags" in df.columns:
        for i, tags_str in enumerate(df["tags"]):
            try:
                tags = json.loads(tags_str) if isinstance(tags_str, str) else []
            except json.JSONDecodeError:
                tags = []
            if any(t.startswith("soil_") and t not in ("soil_dry", "soil_wet") for t in tags):
                df.loc[i, "label_soil_event"] = 1

    # Air quality label
    df["label_air_quality"] = 0
    if "pm_pm2_5" in df.columns:
        df.loc[df["pm_pm2_5"] > 35, "label_air_quality"] = 1
        df.loc[df["pm_pm2_5"] > 75, "label_air_quality"] = 2

    return df


def run_feature_builder(config: ProjectConfig) -> Path:
    """
    Build the complete training feature matrix.

    Combines Phase 1 sensor data with Phase 2 enrichments.
    Returns path to final training CSV.
    """
    print("=" * 60)
    print("PHASE 3a: Feature Builder")
    print("=" * 60)

    # Load Phase 1 sensor data
    print("[features] Loading Phase 1 sensor data...")
    df = load_phase1_data(config)
    print(f"  Raw shape: {df.shape}")

    # Add time features
    print("[features] Adding time features...")
    df = add_time_features(df)

    # Add derived sensor features
    print("[features] Adding sensor-derived features...")
    df = add_sensor_derived(df)

    # Merge climate context
    print("[features] Merging climate context...")
    df = add_climate_context(df, config)

    # Add static enrichment features (same for all rows)
    print("[features] Adding enrichment context...")
    enrichment = build_enrichment_features(config)
    for key, val in enrichment.items():
        df[key] = val

    # Generate labels
    print("[features] Generating training labels...")
    df = generate_labels(df, config)

    # Clean up
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.fillna(0)

    # Drop non-numeric/non-feature columns for the feature matrix
    drop_cols = ["timestamp", "timestamp_unix", "tags", "quality_flag"]
    feature_cols = [c for c in df.columns if c not in drop_cols]

    out_path = config.enriched_dir / f"training_features_{config.project_id}.csv"
    df[feature_cols].to_csv(out_path, index=False)

    print(f"\n[features] Final feature matrix: {df[feature_cols].shape}")
    print(f"  Sensor channels: {len([c for c in feature_cols if c.startswith(('dfrobot_', 'tgs_', 'bme688_', 'pm_', 'soil_'))])}")
    print(f"  Derived features: {len([c for c in feature_cols if 'ratio' in c or 'roll' in c or 'delta' in c])}")
    print(f"  Time features: {len([c for c in feature_cols if c.startswith(('hour', 'day_', 'is_'))])}")
    print(f"  Label columns: {len([c for c in feature_cols if c.startswith('label_')])}")
    print(f"  Saved → {out_path}")

    return out_path

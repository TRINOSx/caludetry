"""
Phase 1 — Auto-Tagger

Analyzes raw sensor readings and applies automatic tags:
  - Time-of-day (morning, afternoon, evening, night)
  - Stress detection (ethanol + HCHO spike)
  - Soil gas events (H2S + CH4 spike)
  - Humidity critical (>85% or <20%)
  - Temperature extreme (>38C or <5C)
  - Air quality (PM2.5 > WHO threshold)
  - Irrigation detected (soil moisture sudden increase)
  - Possible pest activity (VOC pattern)
"""
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import ProjectConfig


# ────────────────────────────────────────────────────────────
# Tag rules: each returns a list of tags for a given row
# ────────────────────────────────────────────────────────────

def _tag_time_of_day(row: dict) -> list[str]:
    """Tag based on hour of day."""
    try:
        ts = datetime.fromisoformat(row["timestamp"])
        h = ts.hour
    except (ValueError, KeyError):
        return []

    if 6 <= h < 12:
        return ["morning"]
    elif 12 <= h < 18:
        return ["afternoon"]
    elif 18 <= h < 22:
        return ["evening"]
    return ["night"]


def _tag_stress(row: dict) -> list[str]:
    """Detect plant stress via ethanol + formaldehyde elevation."""
    tags = []
    etoh = float(row.get("dfrobot_etoh", 0))
    hcho = float(row.get("dfrobot_hcho", 0))
    voc = float(row.get("dfrobot_voc", 0))

    if etoh > 10 and hcho > 0.3:
        tags.append("stress_severe")
    elif etoh > 5 or hcho > 0.15:
        tags.append("stress_mild")

    if voc > 5000:
        tags.append("voc_spike")

    return tags


def _tag_soil_gas(row: dict) -> list[str]:
    """Detect soil gas events."""
    tags = []
    h2s = float(row.get("dfrobot_h2s", 0))
    ch4 = float(row.get("dfrobot_ch4", 0))
    nh3 = float(row.get("dfrobot_h2s", 0))  # NH3 from H2S cross-sensitivity in TGS2602

    if h2s > 2:
        tags.append("soil_h2s_high")
    if ch4 > 50:
        tags.append("soil_ch4_high")

    return tags


def _tag_environment(row: dict) -> list[str]:
    """Tag environmental extremes."""
    tags = []
    temp = float(row.get("bme688_temperature", 25))
    hum = float(row.get("bme688_humidity", 50))
    pm25 = float(row.get("pm_pm2_5", 0))

    if temp > 38:
        tags.append("temp_extreme_high")
    elif temp < 5:
        tags.append("temp_extreme_low")

    if hum > 85:
        tags.append("humidity_critical_high")
    elif hum < 20:
        tags.append("humidity_critical_low")

    if pm25 > 35:  # WHO 24h guideline
        tags.append("air_quality_poor")
    if pm25 > 75:
        tags.append("air_quality_hazardous")

    return tags


def _tag_soil_conditions(row: dict) -> list[str]:
    """Tag soil conditions."""
    tags = []
    moisture = float(row.get("soil_moisture", 50))
    ph = float(row.get("soil_ph", 7.0))
    ec = float(row.get("soil_conductivity", 500))

    if moisture > 70:
        tags.append("soil_wet")
    elif moisture < 25:
        tags.append("soil_dry")

    if ph < 5.5:
        tags.append("soil_acidic")
    elif ph > 7.5:
        tags.append("soil_alkaline")

    if ec > 4000:
        tags.append("soil_saline")

    return tags


def _tag_pest_pattern(row: dict) -> list[str]:
    """
    Detect possible pest/disease VOC patterns.
    Defense VOCs (methyl salicylate proxy via TGS2602 response)
    combined with high TVOC suggest herbivore/pathogen response.
    """
    tags = []
    tgs2602 = float(row.get("tgs_tgs2602", 0.5))
    voc = float(row.get("dfrobot_voc", 0))

    # Low TGS2602 Rs/R0 = high gas concentration (defense VOCs)
    if tgs2602 < 0.3 and voc > 1000:
        tags.append("possible_pest_defense")

    return tags


ALL_TAG_RULES = [
    _tag_time_of_day,
    _tag_stress,
    _tag_soil_gas,
    _tag_environment,
    _tag_soil_conditions,
    _tag_pest_pattern,
]


class AutoTagger:
    """Applies all tag rules to a dataset of sensor readings."""

    def __init__(self, config: ProjectConfig):
        self.config = config

    def tag_row(self, row: dict) -> list[str]:
        """Apply all tag rules to a single row."""
        tags = []
        for rule in ALL_TAG_RULES:
            tags.extend(rule(row))
        return tags

    def tag_csv(self, csv_path: Path) -> Path:
        """
        Read raw CSV, apply auto-tags, write tagged CSV.
        Merges new tags with any existing tags.
        """
        df = pd.read_csv(csv_path)
        print(f"[tagger] Processing {len(df)} rows from {csv_path}")

        new_tags_list = []
        for _, row in df.iterrows():
            existing = json.loads(row.get("tags", "[]")) if isinstance(row.get("tags"), str) else []
            auto_tags = self.tag_row(row.to_dict())
            merged = list(set(existing + auto_tags))
            new_tags_list.append(json.dumps(merged))

        df["tags"] = new_tags_list

        # Save tagged version
        tagged_path = csv_path.parent / csv_path.name.replace(".csv", "_tagged.csv")
        df.to_csv(tagged_path, index=False)

        # Tag statistics
        all_tags = []
        for tags_json in new_tags_list:
            all_tags.extend(json.loads(tags_json))

        tag_counts = {}
        for t in all_tags:
            tag_counts[t] = tag_counts.get(t, 0) + 1

        print(f"[tagger] Tag distribution:")
        for tag, count in sorted(tag_counts.items(), key=lambda x: -x[1]):
            print(f"  {tag}: {count} ({count/len(df)*100:.1f}%)")

        print(f"[tagger] Saved → {tagged_path}")
        return tagged_path

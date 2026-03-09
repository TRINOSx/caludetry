"""
Phase 1 — ETL Orchestrator

Runs the complete Phase 1 pipeline:
  1. Collect sensor data (live MQTT or simulated)
  2. Apply auto-tags
  3. Validate data quality
  4. Output tagged CSV ready for Phase 2 enrichment
"""
import sys
from pathlib import Path

import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import ProjectConfig
from phase1_etl.collector import SensorCollector
from phase1_etl.tagger import AutoTagger


def validate_data(csv_path: Path) -> dict:
    """
    Validate collected data quality.
    Returns report dict with statistics and issues.
    """
    df = pd.read_csv(csv_path)
    report = {
        "total_rows": len(df),
        "columns": list(df.columns),
        "null_pct": {},
        "zero_pct": {},
        "issues": [],
    }

    sensor_cols = [c for c in df.columns if c not in ("timestamp", "timestamp_unix", "tags", "quality_flag")]

    for col in sensor_cols:
        null_pct = df[col].isna().mean() * 100
        zero_pct = (df[col] == 0).mean() * 100
        report["null_pct"][col] = round(null_pct, 2)
        report["zero_pct"][col] = round(zero_pct, 2)

        if null_pct > 50:
            report["issues"].append(f"{col}: {null_pct:.1f}% null values")
        if zero_pct > 90:
            report["issues"].append(f"{col}: {zero_pct:.1f}% zero values (sensor offline?)")

    # Check timestamp continuity
    if "timestamp_unix" in df.columns:
        diffs = df["timestamp_unix"].diff().dropna()
        if len(diffs) > 0:
            median_interval = diffs.median()
            gaps = diffs[diffs > median_interval * 3]
            if len(gaps) > 0:
                report["issues"].append(f"{len(gaps)} time gaps detected (>3x median interval)")

    return report


def run_phase1(config: ProjectConfig, simulated: bool = True, n_readings: int = 1000) -> Path:
    """
    Execute Phase 1 pipeline.

    Args:
        config: project configuration
        simulated: if True, generate simulated data instead of live MQTT
        n_readings: number of simulated readings

    Returns:
        Path to tagged CSV file
    """
    print("=" * 60)
    print("PHASE 1: ETL — Sensor Data Collection & Tagging")
    print("=" * 60)
    print(f"Project: {config.project_id}")
    print(f"Seed: {config.seed_name} ({config.seed_common_name})")
    print(f"Location: {config.latitude}, {config.longitude}")
    print()

    # Step 1: Collect data
    print("--- Step 1: Data Collection ---")
    collector = SensorCollector(config)

    if simulated:
        csv_path = collector.run_simulated_collection(n_readings, seed=config.random_seed)
    else:
        # Live MQTT collection would be started here
        # For now, we just return the path for existing data
        print("[collector] Live MQTT collection mode — connect sensors and run")
        print(f"  MQTT broker: {config.mqtt_broker}:{config.mqtt_port}")
        print(f"  Topic: {config.mqtt_topic_prefix}/#")
        print(f"  Sample interval: {config.sample_interval_s}s")
        csv_path = collector.csv_path

    if not csv_path.exists() or collector.readings_count == 0:
        print("[error] No data collected. Cannot proceed.")
        return csv_path

    # Step 2: Auto-tag
    print("\n--- Step 2: Auto-Tagging ---")
    tagger = AutoTagger(config)
    tagged_path = tagger.tag_csv(csv_path)

    # Step 3: Validate
    print("\n--- Step 3: Data Validation ---")
    report = validate_data(tagged_path)
    print(f"Total rows: {report['total_rows']}")
    if report["issues"]:
        print(f"Issues found ({len(report['issues'])}):")
        for issue in report["issues"]:
            print(f"  - {issue}")
    else:
        print("No issues found.")

    print(f"\n[phase1] Complete. Tagged data: {tagged_path}")
    return tagged_path

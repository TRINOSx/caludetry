#!/usr/bin/env python3
"""
VOC Training Pipeline — Main Entry Point

Internal training project for agricultural eNose sensor arrays.
Separate from the client-facing VOC Mesh Platform.

=== USAGE ===

1. Edit the config below with your seed, location, APIs
2. Run: python run_project.py
3. Or run individual phases:
     python run_project.py --phase 1    # ETL only
     python run_project.py --phase 2    # Enrichment only
     python run_project.py --phase 3    # Training only

=== PIPELINE ===

Phase 1 (ETL):
  Sensor collection → auto-tagging → data validation
  Input:  MQTT/LoRa sensor readings (or simulated)
  Output: data/raw/sensor_readings_*.csv

Phase 2 (Enrichment):
  Climate history + Seed VOCs + Microorganism VOCs +
  Agrochemical VOCs + AlphaEarth geospatial
  Input:  Config (seed, location, APIs)
  Output: data/enriched/*.json, *.csv

Phase 3 (Training):
  Feature builder → multi-head neural network → ONNX export
  Input:  Phase 1 + Phase 2 data
  Output: data/models/voc_model_*.pt, *.onnx

=== HARDWARE ===

  8x DFRobot MEMS: HCHO, H2S, NO2, VOC, CH4, CO, EtOH, H2
  4x Figaro TGS:   TGS2600, TGS2602, TGS2611, TGS2620
  1x Bosch BME688:  temp, humidity, pressure, gas resistance
  1x PMS5003:       PM1.0, PM2.5, PM10
  1x NPKPHCTH-S:    N, P, K, pH, EC, temp, moisture (RS485)
  ESP32 + LoRa SX1276
"""
import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import ProjectConfig


# ═══════════════════════════════════════════════════════════════
# PROGRAMMER: FILL THIS CONFIG BEFORE RUNNING
# ═══════════════════════════════════════════════════════════════

def get_config() -> ProjectConfig:
    """
    Edit this function with your project details.
    This is the ONLY place you need to change.
    """
    return ProjectConfig(
        # ─── Seed / Crop ───
        seed_name="Solanum lycopersicum",       # Scientific name
        seed_variety="Roma VF",                  # Variety
        seed_common_name="tomato",               # Common name
        crop_family="Solanaceae",                # Family

        # ─── Location (GPS) ───
        latitude=20.6597,                        # Latitude
        longitude=-103.3496,                     # Longitude
        altitude_m=1566,                         # Meters above sea level
        location_name="Guadalajara, Jalisco, MX",
        timezone="America/Mexico_City",

        # ─── Time ───
        start_date="2026-03-09T08:00:00",        # ISO format
        end_date="",                              # Empty = ongoing

        # ─── API Keys ───
        anthropic_api_key="",                     # Required for seed/microorganism research
        openweather_api_key="",                   # Optional: climate history
        google_earth_engine_project="",           # Optional: satellite data
        ncbi_api_key="",                          # Optional: PubChem compounds

        # ─── Sensor Transport ───
        mqtt_broker="localhost",
        mqtt_port=1883,
        mqtt_topic_prefix="training/voc",
        lora_gateway_serial="",                   # e.g. "/dev/ttyUSB0"

        # ─── Training ───
        batch_size_training=64,
        epochs=100,
        learning_rate=1e-3,
        val_split=0.15,
        test_split=0.15,
        random_seed=42,

        # ─── Enrichment flags ───
        enrich_climate=True,
        enrich_seed_voc=True,
        enrich_microorganisms=True,
        enrich_agrochemicals=True,
        enrich_alpha_earth=True,
    )


# ═══════════════════════════════════════════════════════════════
# Pipeline execution
# ═══════════════════════════════════════════════════════════════

def run_all(config: ProjectConfig, simulated: bool = True, n_readings: int = 1000):
    """Run all 3 phases sequentially."""
    print("╔══════════════════════════════════════════════════════════╗")
    print("║   VOC Training Pipeline — Internal                     ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"  Project ID: {config.project_id}")
    print(f"  Seed:       {config.seed_name} ({config.seed_common_name})")
    print(f"  Location:   {config.location_name}")
    print(f"  Start:      {config.start_date}")
    print()

    # Validate
    errors = config.validate()
    if errors:
        print("Configuration errors:")
        for e in errors:
            print(f"  - {e}")
        # Allow running without API key (will use placeholders)
        critical = [e for e in errors if "latitude" in e or "seed_name" in e or "start_date" in e]
        if critical:
            print("\nCritical errors found. Fix config and retry.")
            return

    config.ensure_dirs()

    # Phase 1: ETL
    print("\n" + "─" * 60)
    from phase1_etl.pipeline import run_phase1
    tagged_csv = run_phase1(config, simulated=simulated, n_readings=n_readings)

    # Phase 2: Enrichment
    print("\n" + "─" * 60)
    from phase2_enrichment.pipeline import run_phase2
    enrichment_paths = run_phase2(config)

    # Phase 3: Training
    print("\n" + "─" * 60)
    from phase3_training.feature_builder import run_feature_builder
    features_path = run_feature_builder(config)

    print("\n" + "─" * 60)
    from phase3_training.train import run_training
    report = run_training(config)

    # Final summary
    print("\n" + "═" * 60)
    print("PIPELINE COMPLETE")
    print("═" * 60)
    print(f"  Project:    {config.project_id}")
    print(f"  Model:      {config.models_dir / f'voc_model_{config.project_id}.pt'}")
    print(f"  ONNX:       {config.models_dir / f'voc_model_{config.project_id}.onnx'}")
    print(f"  Accuracy:   {report['metrics'].get('plant_state_accuracy', 'N/A')}")
    print(f"  Stress MAE: {report['metrics'].get('stress_mae', 'N/A')}%")
    print(f"  Report:     {config.models_dir / f'training_report_{config.project_id}.json'}")


def main():
    parser = argparse.ArgumentParser(description="VOC Training Pipeline")
    parser.add_argument("--phase", type=int, choices=[1, 2, 3],
                        help="Run specific phase (default: all)")
    parser.add_argument("--simulated", action="store_true", default=True,
                        help="Use simulated sensor data (default: True)")
    parser.add_argument("--live", action="store_true",
                        help="Use live MQTT sensor data")
    parser.add_argument("--readings", type=int, default=1000,
                        help="Number of simulated readings (default: 1000)")
    args = parser.parse_args()

    config = get_config()
    simulated = not args.live

    if args.phase is None:
        run_all(config, simulated=simulated, n_readings=args.readings)
    elif args.phase == 1:
        from phase1_etl.pipeline import run_phase1
        run_phase1(config, simulated=simulated, n_readings=args.readings)
    elif args.phase == 2:
        from phase2_enrichment.pipeline import run_phase2
        run_phase2(config)
    elif args.phase == 3:
        from phase3_training.feature_builder import run_feature_builder
        from phase3_training.train import run_training
        run_feature_builder(config)
        run_training(config)


if __name__ == "__main__":
    main()

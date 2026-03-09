"""
Phase 1 — Sensor Data Collector

Reads from all 26 sensor channels (DFRobot MEMS, Figaro TGS, BME688,
particle sensor, soil sensor) via MQTT or serial/LoRa gateway.

Each reading is timestamped and stored as a row in a Parquet file:
  timestamp | dfrobot_hcho | dfrobot_h2s | ... | soil_moisture | tags

The collector runs from start_date until manually stopped or end_date.
"""
import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import ProjectConfig, ALL_SENSOR_CHANNELS, TOTAL_CHANNELS


class SensorCollector:
    """Collects and stores sensor readings from the eNose array."""

    def __init__(self, config: ProjectConfig):
        self.config = config
        self.config.ensure_dirs()
        self.csv_path = config.raw_dir / f"sensor_readings_{config.project_id}.csv"
        self.readings_count = 0
        self._init_csv()

    def _init_csv(self):
        """Initialize CSV file with headers."""
        if self.csv_path.exists():
            # Count existing rows
            with open(self.csv_path) as f:
                self.readings_count = sum(1 for _ in f) - 1  # minus header
            print(f"[collector] Resuming: {self.readings_count} existing readings in {self.csv_path}")
            return

        headers = ["timestamp", "timestamp_unix"]
        for ch in ALL_SENSOR_CHANNELS:
            headers.append(ch["id"])
        headers.extend(["tags", "quality_flag"])

        with open(self.csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)

        print(f"[collector] Initialized {self.csv_path}")
        print(f"[collector] {TOTAL_CHANNELS} sensor channels configured")

    def store_reading(self, reading: dict, tags: list[str] = None, quality: str = "ok"):
        """
        Store a single sensor reading.

        Args:
            reading: dict mapping channel_id → value (e.g. {"dfrobot_hcho": 0.12, ...})
            tags: optional list of tags (e.g. ["irrigation", "morning"])
            quality: quality flag ("ok", "noisy", "drift", "calibrating")
        """
        now = datetime.now(timezone.utc)
        row = [now.isoformat(), now.timestamp()]

        for ch in ALL_SENSOR_CHANNELS:
            row.append(reading.get(ch["id"], 0.0))

        row.append(json.dumps(tags or []))
        row.append(quality)

        with open(self.csv_path, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(row)

        self.readings_count += 1

    def parse_mqtt_payload(self, payload: bytes) -> dict:
        """
        Parse MQTT message from ESP32 into channel readings.

        Expected JSON format from ESP32:
        {
            "dfrobot": {"HCHO": 0.12, "H2S": 0.5, "NO2": 0.03, ...},
            "tgs": {"TGS2600": 0.45, "TGS2602": 0.32, ...},
            "bme688": {"temperature": 25.3, "humidity": 60.1, "pressure": 1013, "gas_resistance": 50000},
            "pm": {"PM1_0": 12, "PM2_5": 25, "PM10": 40},
            "soil": {"nitrogen": 45, "phosphorus": 30, "potassium": 200, ...}
        }
        """
        data = json.loads(payload)
        reading = {}

        # DFRobot MEMS
        dfrobot = data.get("dfrobot", {})
        for key, val in dfrobot.items():
            reading[f"dfrobot_{key.lower()}"] = float(val)

        # Figaro TGS
        tgs = data.get("tgs", {})
        for key, val in tgs.items():
            reading[f"tgs_{key.lower()}"] = float(val)

        # BME688
        bme = data.get("bme688", {})
        for key, val in bme.items():
            reading[f"bme688_{key}"] = float(val)

        # Particle sensor
        pm = data.get("pm", {})
        for key, val in pm.items():
            reading[f"pm_{key.lower()}"] = float(val)

        # Soil sensor
        soil = data.get("soil", {})
        for key, val in soil.items():
            reading[f"soil_{key}"] = float(val)

        return reading

    def generate_simulated_reading(self, rng: np.random.Generator = None) -> dict:
        """
        Generate a simulated sensor reading for testing.
        Uses realistic ranges from sensor specs.
        """
        rng = rng or np.random.default_rng()
        reading = {}

        # DFRobot MEMS (ppm ranges)
        dfrobot_ranges = {
            "dfrobot_hcho": (0, 0.5),
            "dfrobot_h2s": (0, 5),
            "dfrobot_no2": (0, 1),
            "dfrobot_voc": (0, 2000),  # ppb
            "dfrobot_ch4": (0, 100),
            "dfrobot_co": (0, 50),
            "dfrobot_etoh": (0, 20),
            "dfrobot_h2": (0, 50),
        }
        for ch, (lo, hi) in dfrobot_ranges.items():
            reading[ch] = float(rng.uniform(lo, hi))

        # Figaro TGS (Rs/R0 ratio, 0.1-1.0)
        for tgs in ["tgs_tgs2600", "tgs_tgs2602", "tgs_tgs2611", "tgs_tgs2620"]:
            reading[tgs] = float(rng.uniform(0.15, 0.95))

        # BME688
        reading["bme688_temperature"] = float(rng.uniform(10, 40))
        reading["bme688_humidity"] = float(rng.uniform(30, 90))
        reading["bme688_pressure"] = float(rng.uniform(980, 1030))
        reading["bme688_gas_resistance"] = float(rng.exponential(50000) + 5000)

        # PM
        reading["pm_pm1_0"] = float(rng.uniform(0, 50))
        reading["pm_pm2_5"] = float(rng.uniform(0, 100))
        reading["pm_pm10"] = float(rng.uniform(0, 150))

        # Soil
        reading["soil_nitrogen"] = float(rng.uniform(10, 200))
        reading["soil_phosphorus"] = float(rng.uniform(5, 100))
        reading["soil_potassium"] = float(rng.uniform(50, 500))
        reading["soil_ph"] = float(rng.uniform(4.5, 8.0))
        reading["soil_conductivity"] = float(rng.uniform(100, 2000))
        reading["soil_temperature"] = float(rng.uniform(10, 35))
        reading["soil_moisture"] = float(rng.uniform(15, 80))

        return reading

    def run_simulated_collection(self, n_readings: int = 1000, seed: int = 42):
        """Generate simulated data for pipeline testing."""
        rng = np.random.default_rng(seed)
        print(f"[collector] Generating {n_readings} simulated readings...")

        auto_tags = ["simulated"]
        for i in range(n_readings):
            reading = self.generate_simulated_reading(rng)

            # Add time-based auto-tags
            hour = (i * self.config.sample_interval_s // 3600) % 24
            tags = list(auto_tags)
            if 6 <= hour < 12:
                tags.append("morning")
            elif 12 <= hour < 18:
                tags.append("afternoon")
            elif 18 <= hour < 22:
                tags.append("evening")
            else:
                tags.append("night")

            # Simulate some stress events
            if rng.random() < 0.05:
                reading["dfrobot_etoh"] *= 5  # ethanol spike
                reading["dfrobot_hcho"] *= 3
                tags.append("stress_event")

            if rng.random() < 0.03:
                reading["dfrobot_h2s"] *= 8  # soil gas event
                tags.append("soil_gas_event")

            self.store_reading(reading, tags=tags)

        print(f"[collector] Stored {n_readings} readings → {self.csv_path}")
        return self.csv_path

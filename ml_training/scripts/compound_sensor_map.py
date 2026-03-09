#!/usr/bin/env python3
"""
Chemical Fingerprint Mapping: GC-MS compounds → MOx sensor responses.

This is the critical bridge between metabolomics data (what compounds exist)
and sensor training data (how sensors respond to those compounds).

The mapping uses:
  1. Known cross-sensitivity profiles of MOx sensors (from datasheets)
  2. Compound physical properties (molecular weight, boiling point)
  3. Beer-Lambert absorption coefficients for PID sensors

Pipeline:
  Metabolomics Workbench / MetaboLights
    → compound concentrations (GC-MS, ppb)
    → compound_sensor_map (this module)
    → simulated sensor responses (mV / index)
    → merge with UCI real sensor data
    → train ML models

Usage:
    from compound_sensor_map import CompoundSensorMapper
    mapper = CompoundSensorMapper()
    sensor_response = mapper.compound_to_sensor("ethylene", concentration_ppb=200)
    training_batch = mapper.generate_sensor_training_data(metabolomics_compounds)
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import COMPOUND_SENSOR_FINGERPRINTS, DATASETS_DIR


class CompoundSensorMapper:
    """Maps GC-MS compound identifications to simulated MOx sensor responses."""

    # Sensor response characteristics (from datasheets)
    SENSOR_PARAMS = {
        "SGP40": {
            "type": "MOx",
            "baseline": 100,       # VOC Index baseline
            "max_output": 500,     # VOC Index max
            "noise_std": 5,        # typical noise
            "response_time_s": 10, # T90 response
            "drift_pct_year": 15,  # annual drift %
        },
        "TGS2602": {
            "type": "MOx",
            "baseline": 0.8,       # Rs/R0 in clean air
            "max_output": 0.1,     # Rs/R0 at max conc
            "noise_std": 0.02,
            "response_time_s": 30,
            "drift_pct_year": 10,
        },
        "TGS2620": {
            "type": "MOx",
            "baseline": 0.9,
            "max_output": 0.15,
            "noise_std": 0.015,
            "response_time_s": 20,
            "drift_pct_year": 12,
        },
        "PID": {
            "type": "photoionization",
            "baseline": 0,
            "max_output": 10000,   # ppb direct
            "noise_std": 2,
            "response_time_s": 2,
            "drift_pct_year": 5,
        },
        "MQ3": {
            "type": "MOx",
            "baseline": 1.0,
            "max_output": 0.05,
            "noise_std": 0.03,
            "response_time_s": 60,
            "drift_pct_year": 20,
        },
        "MQ135": {
            "type": "MOx",
            "baseline": 1.0,
            "max_output": 0.1,
            "noise_std": 0.025,
            "response_time_s": 45,
            "drift_pct_year": 18,
        },
    }

    def __init__(self, fingerprints: dict = None):
        self.fingerprints = fingerprints or COMPOUND_SENSOR_FINGERPRINTS

    def compound_to_sensor(
        self,
        compound: str,
        concentration_ppb: float,
        temperature_c: float = 25.0,
        humidity_pct: float = 50.0,
        add_noise: bool = True,
        rng: np.random.Generator = None,
    ) -> dict[str, float]:
        """
        Simulate MOx sensor responses for a given compound at a concentration.

        Returns dict mapping sensor_name → simulated reading.
        """
        rng = rng or np.random.default_rng()
        fp = self.fingerprints.get(compound)
        if fp is None:
            return {}

        responses = {}
        for sensor_name, sensitivity in fp.items():
            if sensor_name in ("category", "mw", "boiling_c"):
                continue

            params = self.SENSOR_PARAMS.get(sensor_name)
            if params is None:
                continue

            # Base response: logarithmic sensor characteristic
            # MOx sensors follow: Rs/R0 = a * C^(-b)
            # Simplified: response = sensitivity * log(1 + conc/ref_conc)
            ref_conc = 100.0  # reference concentration ppb
            raw_response = sensitivity * np.log1p(concentration_ppb / ref_conc)

            # Temperature compensation (MOx sensitivity increases ~2%/°C above 25°C)
            temp_factor = 1.0 + 0.02 * (temperature_c - 25.0)

            # Humidity interference (MOx response decreases at high humidity)
            humidity_factor = 1.0 - 0.005 * (humidity_pct - 50.0)

            # Scale to sensor output range
            output_range = params["max_output"] - params["baseline"]
            if params["type"] == "MOx":
                # MOx: resistance ratio decreases with gas (inverted)
                simulated = params["baseline"] - raw_response * abs(output_range) * temp_factor * humidity_factor
                simulated = max(params["max_output"], min(params["baseline"], simulated))
            else:
                # PID: direct proportional
                simulated = raw_response * params["max_output"] * temp_factor * humidity_factor
                simulated = max(0, min(params["max_output"], simulated))

            # Add realistic noise
            if add_noise:
                simulated += rng.normal(0, params["noise_std"])

            responses[sensor_name] = float(simulated)

        return responses

    def generate_sensor_training_data(
        self,
        compound_profiles: list[dict],
        n_samples_per_profile: int = 100,
        seed: int = 42,
    ) -> pd.DataFrame:
        """
        Generate synthetic sensor training data from metabolomics compound profiles.

        Args:
            compound_profiles: list of dicts with keys:
                - compound: str (platform compound name)
                - concentration_ppb: float (or range tuple)
                - condition: str (e.g., "stress", "healthy", "pest_attack")
            n_samples_per_profile: samples to generate per profile entry
            seed: random seed

        Returns:
            DataFrame with columns: [sensor_1, ..., sensor_n, compound, condition,
                                     concentration, temperature, humidity]
        """
        rng = np.random.default_rng(seed)
        rows = []

        for profile in compound_profiles:
            compound = profile["compound"]
            condition = profile.get("condition", "unknown")

            # Concentration range
            conc = profile.get("concentration_ppb", 100)
            if isinstance(conc, (list, tuple)):
                conc_lo, conc_hi = conc
            else:
                conc_lo, conc_hi = conc * 0.5, conc * 1.5

            for _ in range(n_samples_per_profile):
                c = rng.uniform(conc_lo, conc_hi)
                t = rng.uniform(10, 40)   # realistic field temps
                h = rng.uniform(30, 90)   # realistic humidity

                responses = self.compound_to_sensor(
                    compound, c, temperature_c=t, humidity_pct=h,
                    add_noise=True, rng=rng,
                )

                row = {
                    **responses,
                    "compound": compound,
                    "condition": condition,
                    "concentration_ppb": c,
                    "temperature_c": t,
                    "humidity_pct": h,
                }
                rows.append(row)

        df = pd.DataFrame(rows).fillna(0)
        return df

    def metabolomics_to_training(
        self,
        metabolomics_json_path: Path = None,
        n_samples: int = 100,
        seed: int = 42,
    ) -> pd.DataFrame:
        """
        End-to-end: load metabolomics results → generate sensor training data.

        Reads the output of fetch_metabolomics.py and creates sensor-level
        training data using the chemical fingerprint mapping.
        """
        json_path = metabolomics_json_path or (DATASETS_DIR / "metabolomics" / "metabolomics_compounds.json")

        if not json_path.exists():
            print(f"[warn] No metabolomics data at {json_path}. Run fetch_metabolomics.py first.")
            print("[info] Falling back to default compound profiles.")
            return self._generate_default_profiles(n_samples, seed)

        with open(json_path) as f:
            data = json.load(f)

        profiles = []
        for source_key in ("metabolomics_workbench", "metabolights"):
            source_data = data.get(source_key, {})
            for match in source_data.get("matched_compounds", []):
                compound = match["platform_compound"]
                category = match.get("category", "unknown")

                # Assign realistic concentration ranges by category
                conc_ranges = {
                    "stress": (50, 500),
                    "defense": (10, 200),
                    "terpene": (5, 300),
                    "flowering": (20, 400),
                    "soil": (100, 2000),
                    "atmosphere": (50, 1500),
                }
                conc = conc_ranges.get(category, (10, 500))

                profiles.append({
                    "compound": compound,
                    "concentration_ppb": conc,
                    "condition": category,
                })

        if not profiles:
            print("[warn] No compound matches found. Using defaults.")
            return self._generate_default_profiles(n_samples, seed)

        # Deduplicate by compound
        seen = set()
        unique_profiles = []
        for p in profiles:
            if p["compound"] not in seen:
                seen.add(p["compound"])
                unique_profiles.append(p)

        print(f"[info] Generating training data for {len(unique_profiles)} compounds")
        return self.generate_sensor_training_data(unique_profiles, n_samples, seed)

    def _generate_default_profiles(self, n_samples: int, seed: int) -> pd.DataFrame:
        """Fallback: generate training data from all known fingerprints."""
        profiles = []
        for compound, fp in self.fingerprints.items():
            category = fp.get("category", "unknown")
            conc_ranges = {
                "stress": (50, 500),
                "defense": (10, 200),
                "terpene": (5, 300),
                "flowering": (20, 400),
                "soil": (100, 2000),
                "atmosphere": (50, 1500),
            }
            profiles.append({
                "compound": compound,
                "concentration_ppb": conc_ranges.get(category, (10, 500)),
                "condition": category,
            })

        return self.generate_sensor_training_data(profiles, n_samples, seed)


def main():
    """Demo: generate sensor training data from compound fingerprints."""
    mapper = CompoundSensorMapper()

    # Try loading metabolomics data first, fall back to defaults
    print("=== Chemical Fingerprint → Sensor Training Data ===\n")
    df = mapper.metabolomics_to_training(n_samples=200, seed=42)

    print(f"\nGenerated dataset shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    print(f"\nCondition distribution:")
    print(df["condition"].value_counts().to_string())
    print(f"\nCompound distribution:")
    print(df["compound"].value_counts().to_string())
    print(f"\nSensor response statistics:")
    sensor_cols = [c for c in df.columns if c not in ("compound", "condition", "concentration_ppb", "temperature_c", "humidity_pct")]
    if sensor_cols:
        print(df[sensor_cols].describe().round(4).to_string())

    # Save
    out_dir = DATASETS_DIR / "synthetic_sensor"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "compound_sensor_training.csv"
    df.to_csv(out_path, index=False)
    print(f"\n[saved] {out_path}")


if __name__ == "__main__":
    main()

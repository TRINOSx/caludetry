#!/usr/bin/env python3
"""
Sensor calibration and drift compensation for VOC Mesh Platform.

Handles two critical sensor challenges:
  1. Calibration: Convert raw ADC → calibrated PPM/PPB using reference data
  2. Drift compensation: MOx sensors drift over time; this model corrects for it

Based on the UCI Gas Sensor Array Drift Dataset methodology.

Usage:
    python calibrate_sensors.py --mode calibrate
    python calibrate_sensors.py --mode drift
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestClassifier
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
import joblib

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import MODELS_DIR, CALIBRATION


def build_calibration_model(n_samples: int = 3000, seed: int = 42):
    """
    Train a calibration model that maps raw sensor readings → true concentrations.
    Uses the platform's calibration equations as ground truth generator.
    """
    rng = np.random.default_rng(seed)

    # Simulate raw ADC readings at various temperatures
    raw_adc = rng.uniform(100, 4000, n_samples)
    temperatures = rng.uniform(5, 45, n_samples)

    # Apply known calibration to generate ground truth
    a, b = CALIBRATION["temp_compensation"]["a"], CALIBRATION["temp_compensation"]["b"]
    corrected = raw_adc * (a * temperatures + b)

    ca, cb, cc = (CALIBRATION["ppm_conversion"]["a"],
                  CALIBRATION["ppm_conversion"]["b"],
                  CALIBRATION["ppm_conversion"]["c"])
    true_ppm = ca * (1 - cb * corrected) + cc

    # Add realistic noise to raw readings (sensor noise)
    noisy_adc = raw_adc + rng.normal(0, raw_adc * 0.03)
    noisy_temp = temperatures + rng.normal(0, 0.5, n_samples)

    features = np.column_stack([noisy_adc, noisy_temp])
    targets = true_ppm

    X_train, X_test, y_train, y_test = train_test_split(
        features, targets, test_size=0.2, random_state=seed,
    )

    model = GradientBoostingRegressor(
        n_estimators=200, max_depth=5, learning_rate=0.1, random_state=seed,
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)

    print(f"Calibration Model | MAE: {mae:.4f} PPM | R²: {r2:.4f}")

    return model


def build_drift_model(n_batches: int = 10, samples_per_batch: int = 500, seed: int = 42):
    """
    Train a drift compensation model.

    MOx sensors degrade over time. This model learns to classify gases
    correctly despite sensor drift by training on data from multiple
    time periods (batches), following the UCI Drift Dataset approach.
    """
    rng = np.random.default_rng(seed)

    n_sensors = 16
    n_gases = 6
    gas_names = ["NH3", "C2H4O", "C3H6O", "C2H4", "C2H5OH", "C7H8"]

    all_features = []
    all_labels = []
    all_batches = []

    # Simulate sensor drift across batches
    base_sensitivity = rng.uniform(0.5, 2.0, (n_gases, n_sensors))

    for batch_idx in range(n_batches):
        # Drift increases with batch number
        drift_factor = 1.0 + batch_idx * 0.05 * rng.normal(1, 0.3, (n_gases, n_sensors))
        drifted_sensitivity = base_sensitivity * drift_factor

        for _ in range(samples_per_batch):
            gas_class = rng.integers(0, n_gases)
            concentration = rng.exponential(200)

            # Sensor response with current drift
            response = concentration * drifted_sensitivity[gas_class]
            response += rng.normal(0, 0.1 * response)  # noise

            all_features.append(response)
            all_labels.append(gas_class)
            all_batches.append(batch_idx)

    features = np.array(all_features)
    labels = np.array(all_labels)
    batches = np.array(all_batches)

    # Strategy: train on early + middle batches, test on late batches
    train_mask = batches <= 7
    test_mask = batches > 7

    X_train, y_train = features[train_mask], labels[train_mask]
    X_test, y_test = features[test_mask], labels[test_mask]

    # Without drift compensation (baseline)
    baseline = RandomForestClassifier(n_estimators=100, random_state=seed)
    baseline.fit(X_train[:2000], y_train[:2000])  # Train on first batches only
    baseline_acc = baseline.score(X_test, y_test)

    # With drift-aware training (trained on all available batches)
    drift_aware = RandomForestClassifier(n_estimators=200, random_state=seed)
    drift_aware.fit(X_train, y_train)
    drift_acc = drift_aware.score(X_test, y_test)

    print(f"\nDrift Compensation Results:")
    print(f"  Baseline (no drift handling):  {baseline_acc:.4f}")
    print(f"  Drift-aware model:             {drift_acc:.4f}")
    print(f"  Improvement:                   +{(drift_acc - baseline_acc):.4f}")

    return drift_aware, gas_names


def main():
    parser = argparse.ArgumentParser(description="Sensor calibration & drift compensation")
    parser.add_argument("--mode", choices=["calibrate", "drift", "both"], default="both")
    args = parser.parse_args()

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    if args.mode in ("calibrate", "both"):
        print("=== Calibration Model ===")
        cal_model = build_calibration_model()
        cal_path = MODELS_DIR / "sensor_calibration.joblib"
        joblib.dump(cal_model, cal_path)
        print(f"Saved: {cal_path}\n")

    if args.mode in ("drift", "both"):
        print("=== Drift Compensation Model ===")
        drift_model, gas_names = build_drift_model()
        drift_path = MODELS_DIR / "drift_compensation.joblib"
        joblib.dump({"model": drift_model, "gas_names": gas_names}, drift_path)
        print(f"Saved: {drift_path}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Training script for all VOC ML models.

Generates synthetic data, trains each model, prints metrics, and optionally
exports to ONNX format.
"""

from __future__ import annotations

import logging
import os
import sys

import numpy as np

from models.stress_model import StressModel
from models.bloom_model import BloomModel
from models.pest_model import PestModel
from models.fire_model import FireModel
from models.carbon_model import CarbonModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-20s  %(levelname)-7s  %(message)s",
)
logger = logging.getLogger("train")

ONNX_DIR = os.path.join(os.path.dirname(__file__), "models")


def _separator(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def train_stress() -> None:
    _separator("Stress Model  (RandomForestRegressor)")
    model = StressModel()
    X, y = StressModel.generate_synthetic_data(n_samples=2000)
    metrics = model.train(X, y)
    print(f"  Train MAE: {metrics['mae']:.3f}")

    # Quick validation on held-out synthetic data
    X_val, y_val = StressModel.generate_synthetic_data(n_samples=500)
    preds = np.array([model.predict(x) for x in X_val])
    val_mae = float(np.mean(np.abs(y_val - preds)))
    print(f"  Val   MAE: {val_mae:.3f}")

    try:
        path = os.path.join(ONNX_DIR, "stress.onnx")
        model.export_onnx(path)
        print(f"  Exported: {path}")
    except Exception as exc:
        print(f"  ONNX export skipped: {exc}")


def train_bloom() -> None:
    _separator("Bloom Model  (GradientBoostingClassifier)")
    model = BloomModel()
    X, y = BloomModel.generate_synthetic_data(n_samples=2000)
    metrics = model.train(X, y)
    print(f"  Train Accuracy: {metrics['accuracy']:.3f}")
    print(f"  Train AUC:      {metrics['auc']:.3f}")

    X_val, y_val = BloomModel.generate_synthetic_data(n_samples=500)
    preds = np.array([1 if model.predict(x) > 0.5 else 0 for x in X_val])
    val_acc = float(np.mean(preds == y_val))
    print(f"  Val   Accuracy: {val_acc:.3f}")

    try:
        path = os.path.join(ONNX_DIR, "bloom.onnx")
        model.export_onnx(path)
        print(f"  Exported: {path}")
    except Exception as exc:
        print(f"  ONNX export skipped: {exc}")


def train_pest() -> None:
    _separator("Pest Model  (RandomForestClassifier)")
    model = PestModel()
    X, y = PestModel.generate_synthetic_data(n_samples=3000)
    metrics = model.train(X, y)
    print(f"  Train Accuracy: {metrics['accuracy']:.3f}")

    X_val, y_val = PestModel.generate_synthetic_data(n_samples=600)
    correct = 0
    for xv, yv in zip(X_val, y_val):
        result = model.predict(xv)
        from models.pest_model import _ZONE_TO_IDX
        pred_idx = _ZONE_TO_IDX.get(result["zone_type"], 0)
        if pred_idx == yv:
            correct += 1
    val_acc = correct / len(y_val)
    print(f"  Val   Accuracy: {val_acc:.3f}")

    try:
        path = os.path.join(ONNX_DIR, "pest.onnx")
        model.export_onnx(path)
        print(f"  Exported: {path}")
    except Exception as exc:
        print(f"  ONNX export skipped: {exc}")


def train_fire() -> None:
    _separator("Fire Model  (Rule + RandomForestClassifier)")
    model = FireModel()
    X, y = FireModel.generate_synthetic_data(n_samples=2000)
    metrics = model.train(X, y)
    print(f"  Train Accuracy: {metrics['accuracy']:.3f}")

    X_val, y_val = FireModel.generate_synthetic_data(n_samples=500)
    preds = np.array([1 if model.predict(x)["smoke_detected"] else 0 for x in X_val])
    val_acc = float(np.mean(preds == y_val))
    print(f"  Val   Accuracy: {val_acc:.3f}")

    try:
        path = os.path.join(ONNX_DIR, "fire.onnx")
        model.export_onnx(path)
        print(f"  Exported: {path}")
    except Exception as exc:
        print(f"  ONNX export skipped: {exc}")


def train_carbon() -> None:
    _separator("Carbon Model  (LinearRegression + engineered features)")
    model = CarbonModel()
    X, y = CarbonModel.generate_synthetic_data(n_samples=2000)
    metrics = model.train(X, y)
    print(f"  Train MAE: {metrics['mae']:.3f}")
    print(f"  Train R2:  {metrics['r2']:.3f}")

    X_val, y_val = CarbonModel.generate_synthetic_data(n_samples=500)
    preds = np.array([model.predict(x) for x in X_val])
    val_mae = float(np.mean(np.abs(y_val - preds)))
    print(f"  Val   MAE: {val_mae:.3f}")

    try:
        path = os.path.join(ONNX_DIR, "carbon.onnx")
        model.export_onnx(path)
        print(f"  Exported: {path}")
    except Exception as exc:
        print(f"  ONNX export skipped: {exc}")


def main() -> None:
    os.makedirs(ONNX_DIR, exist_ok=True)

    train_stress()
    train_bloom()
    train_pest()
    train_fire()
    train_carbon()

    _separator("DONE")
    print("  All models trained successfully.\n")


if __name__ == "__main__":
    main()

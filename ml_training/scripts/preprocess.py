#!/usr/bin/env python3
"""
Preprocessing pipeline for VOC sensor data.
Handles normalization, drift compensation, feature engineering,
and train/val/test splitting.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, RobustScaler

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import CALIBRATION, TRAINING_DEFAULTS


def apply_temperature_compensation(raw_values: np.ndarray, temperatures: np.ndarray) -> np.ndarray:
    """
    Apply temperature compensation from platform calibration.
    value_corrected = raw_adc × (a × temp_c + b)
    """
    a = CALIBRATION["temp_compensation"]["a"]
    b = CALIBRATION["temp_compensation"]["b"]
    correction_factor = a * temperatures + b
    return raw_values * correction_factor


def raw_to_ppm(corrected_values: np.ndarray) -> np.ndarray:
    """
    Convert corrected ADC values to PPM.
    ppm = a × (1 - b × value_corrected) + c
    """
    a = CALIBRATION["ppm_conversion"]["a"]
    b = CALIBRATION["ppm_conversion"]["b"]
    c = CALIBRATION["ppm_conversion"]["c"]
    return a * (1 - b * corrected_values) + c


def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived features useful for plant state classification."""
    out = df.copy()

    # Ratios that indicate specific conditions
    if "C2H4" in df.columns and "C2H5OH" in df.columns:
        out["ethylene_ethanol_ratio"] = df["C2H4"] / (df["C2H5OH"] + 1e-6)

    if "CO2" in df.columns and "O3" in df.columns:
        out["co2_o3_ratio"] = df["CO2"] / (df["O3"] + 1e-6)

    if "NH3" in df.columns and "H2S" in df.columns:
        out["nh3_h2s_sum"] = df["NH3"] + df["H2S"]

    if "TVOC" in df.columns and "CO" in df.columns:
        out["tvoc_co_ratio"] = df["TVOC"] / (df["CO"] + 1e-6)

    # Rolling statistics (if time-series)
    if "timestamp" in df.columns:
        for col in ["TVOC", "C2H4", "NH3"]:
            if col in df.columns:
                out[f"{col}_rolling_mean_5"] = df[col].rolling(5, min_periods=1).mean()
                out[f"{col}_rolling_std_5"] = df[col].rolling(5, min_periods=1).std().fillna(0)

    return out


def normalize_features(df: pd.DataFrame, method: str = "robust") -> tuple[pd.DataFrame, object]:
    """
    Normalize features. RobustScaler is preferred for sensor data
    (handles outliers from sensor spikes better than StandardScaler).
    """
    if method == "robust":
        scaler = RobustScaler()
    else:
        scaler = StandardScaler()

    scaled = scaler.fit_transform(df.values)
    return pd.DataFrame(scaled, columns=df.columns, index=df.index), scaler


def split_dataset(
    features: pd.DataFrame,
    labels: np.ndarray,
    val_split: float = None,
    test_split: float = None,
    seed: int = None,
) -> dict:
    """Split into train/val/test sets with stratification."""
    val_split = val_split or TRAINING_DEFAULTS["val_split"]
    test_split = test_split or TRAINING_DEFAULTS["test_split"]
    seed = seed or TRAINING_DEFAULTS["random_seed"]

    X_train_val, X_test, y_train_val, y_test = train_test_split(
        features, labels,
        test_size=test_split,
        random_state=seed,
        stratify=labels,
    )

    relative_val = val_split / (1 - test_split)
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val, y_train_val,
        test_size=relative_val,
        random_state=seed,
        stratify=y_train_val,
    )

    return {
        "X_train": X_train, "y_train": y_train,
        "X_val": X_val, "y_val": y_val,
        "X_test": X_test, "y_test": y_test,
    }


def preprocess_pipeline(
    features: pd.DataFrame,
    labels: np.ndarray,
    add_derived: bool = True,
    normalize: bool = True,
) -> tuple[dict, object]:
    """
    Full preprocessing pipeline:
    1. Add derived features
    2. Handle NaN/inf
    3. Normalize
    4. Split

    Returns:
        splits: dict with X_train, y_train, X_val, y_val, X_test, y_test
        scaler: fitted scaler for inference
    """
    if add_derived:
        features = add_derived_features(features)

    # Clean
    features = features.replace([np.inf, -np.inf], np.nan)
    features = features.fillna(0)

    scaler = None
    if normalize:
        features, scaler = normalize_features(features)

    splits = split_dataset(features, labels)

    print(f"Train: {splits['X_train'].shape[0]} samples")
    print(f"Val:   {splits['X_val'].shape[0]} samples")
    print(f"Test:  {splits['X_test'].shape[0]} samples")
    print(f"Features: {splits['X_train'].shape[1]}")

    return splits, scaler


if __name__ == "__main__":
    from data_loader import generate_synthetic_voc_data

    df, labels, classes = generate_synthetic_voc_data(2000)
    splits, scaler = preprocess_pipeline(df, labels)

    print(f"\nClass names: {classes}")
    print(f"Train label dist: {np.bincount(splits['y_train'])}")

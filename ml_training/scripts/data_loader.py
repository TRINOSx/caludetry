#!/usr/bin/env python3
"""
Unified data loader for VOC sensor datasets.
Loads UCI Gas Sensor datasets and converts them to a common format
compatible with the VOC Mesh Platform compound IDs.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DATASETS_DIR, GAS_TO_COMPOUND, GAS_CLASSES


def load_uci_gas_drift(data_dir: Path = None) -> tuple[pd.DataFrame, np.ndarray, list[str]]:
    """
    Load UCI Gas Sensor Array Drift Dataset.

    Returns:
        features: DataFrame with 128 sensor features (16 sensors × 8 features)
        labels: ndarray of gas class indices
        class_names: list of gas compound IDs
    """
    dataset_path = (data_dir or DATASETS_DIR) / "uci_gas_drift"

    # Find the .dat files (batch1.dat through batch10.dat)
    dat_files = sorted(dataset_path.rglob("*.dat"))
    if not dat_files:
        raise FileNotFoundError(f"No .dat files found in {dataset_path}. Run download_datasets.py first.")

    all_features = []
    all_labels = []

    gas_names = ["Ammonia", "Acetaldehyde", "Acetone", "Ethylene", "Ethanol", "Toluene"]
    class_names = [GAS_TO_COMPOUND.get(g, g) for g in gas_names]

    for dat_file in dat_files:
        with open(dat_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                # Label is "class:concentration" format → e.g., "1;0.015"
                label_part = parts[0]
                gas_class = int(label_part.split(";")[0]) - 1  # 0-indexed

                # Features are "index:value" format
                features = []
                for p in parts[1:]:
                    if ":" in p:
                        _, val = p.split(":")
                        features.append(float(val))
                    else:
                        features.append(float(p))

                all_features.append(features)
                all_labels.append(gas_class)

    # Pad/truncate to uniform length
    max_len = max(len(f) for f in all_features)
    features_padded = [f + [0.0] * (max_len - len(f)) for f in all_features]

    feature_cols = [f"sensor_{i // 8}_feat_{i % 8}" for i in range(max_len)]
    df = pd.DataFrame(features_padded, columns=feature_cols)

    return df, np.array(all_labels), class_names


def load_uci_gas_dynamic(data_dir: Path = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load UCI Gas Sensor Array under Dynamic Gas Mixtures.

    Returns:
        features: DataFrame with 16 sensor readings over time
        targets: DataFrame with gas concentrations (Ethylene, Methane or CO)
    """
    dataset_path = (data_dir or DATASETS_DIR) / "uci_gas_dynamic"

    csv_files = sorted(dataset_path.rglob("*.txt")) + sorted(dataset_path.rglob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No data files in {dataset_path}. Run download_datasets.py first.")

    all_data = []
    for f in csv_files:
        try:
            df = pd.read_csv(f, sep=r"\s+", header=None, engine="python")
            all_data.append(df)
        except Exception:
            continue

    if not all_data:
        raise ValueError(f"Could not parse any files in {dataset_path}")

    combined = pd.concat(all_data, ignore_index=True)

    # Typical format: col0=time, col1=Ethylene_conc, col2=Methane/CO_conc, cols3-18=sensors
    n_cols = combined.shape[1]
    if n_cols >= 19:
        targets = combined.iloc[:, 1:3].copy()
        targets.columns = ["gas_1_ppm", "gas_2_ppm"]
        features = combined.iloc[:, 3:19].copy()
        features.columns = [f"sensor_{i}" for i in range(16)]
    else:
        # Fallback: treat first 2 as targets, rest as features
        targets = combined.iloc[:, :2].copy()
        targets.columns = ["gas_1_ppm", "gas_2_ppm"]
        features = combined.iloc[:, 2:].copy()
        features.columns = [f"sensor_{i}" for i in range(features.shape[1])]

    return features, targets


def generate_synthetic_voc_data(n_samples: int = 5000, seed: int = 42) -> tuple[pd.DataFrame, np.ndarray, list[str]]:
    """
    Generate synthetic training data that mimics the VOC Mesh Platform sensors.
    Uses realistic concentration ranges for agricultural VOC monitoring.

    This fills the gap when real sensor data is not yet available.
    """
    rng = np.random.default_rng(seed)

    compounds = {
        "TVOC":    {"range": (50, 2000), "unit": "ppb"},
        "CO":      {"range": (100, 1500), "unit": "ppb"},
        "CO2":     {"range": (400, 5000), "unit": "ppm"},
        "C2H5OH":  {"range": (0, 800), "unit": "ppb"},
        "NH3":     {"range": (0, 600), "unit": "ppb"},
        "CH4":     {"range": (50, 1200), "unit": "ppb"},
        "H2":      {"range": (0, 500), "unit": "ppb"},
        "H2S":     {"range": (0, 300), "unit": "ppb"},
        "HCHO":    {"range": (0, 500), "unit": "ppb"},
        "C2H4":    {"range": (0, 400), "unit": "ppb"},
        "C7H8":    {"range": (0, 200), "unit": "ppb"},
        "C6H6":    {"range": (0, 100), "unit": "ppb"},
        "NO2":     {"range": (0, 200), "unit": "ppb"},
        "O3":      {"range": (0, 150), "unit": "ppb"},
        # Environmental
        "temperature": {"range": (5, 45), "unit": "C"},
        "humidity":    {"range": (20, 95), "unit": "%"},
        "soil_moisture": {"range": (10, 90), "unit": "%"},
    }

    data = {}
    for name, spec in compounds.items():
        lo, hi = spec["range"]
        data[name] = rng.uniform(lo, hi, n_samples).astype(np.float32)

    # Plant state labels: 0=healthy, 1=mild_stress, 2=severe_stress, 3=pest_attack, 4=flowering
    labels = np.zeros(n_samples, dtype=int)

    # Stress correlates with high ethylene + ethanol
    stress_mask = (data["C2H4"] > 250) & (data["C2H5OH"] > 400)
    labels[stress_mask] = 2

    mild_stress = (data["C2H4"] > 150) & (data["C2H5OH"] > 200) & ~stress_mask
    labels[mild_stress] = 1

    # Pest attack: defense VOC pattern (simulate via high TVOC + NH3)
    pest_mask = (data["TVOC"] > 1200) & (data["NH3"] > 300)
    labels[pest_mask] = 3

    # Flowering: low stress + moderate temp
    flowering_mask = (
        (data["temperature"] > 18) & (data["temperature"] < 30) &
        (data["C2H4"] < 100) & (labels == 0)
    )
    # Mark 20% of healthy as flowering
    flowering_indices = np.where(flowering_mask)[0]
    selected = rng.choice(flowering_indices, size=len(flowering_indices) // 5, replace=False)
    labels[selected] = 4

    class_names = ["healthy", "mild_stress", "severe_stress", "pest_attack", "flowering"]
    df = pd.DataFrame(data)

    return df, labels, class_names


def load_metabolomics_sensor_data(
    csv_path: Path = None,
    n_samples: int = 200,
    seed: int = 42,
) -> tuple[pd.DataFrame, np.ndarray, list[str]]:
    """
    Load sensor training data generated from metabolomics compound profiles.
    If no pre-generated CSV exists, generates data via CompoundSensorMapper.

    Returns:
        features: DataFrame with sensor response columns
        labels: ndarray of condition class indices
        class_names: list of condition names
    """
    default_path = DATASETS_DIR / "synthetic_sensor" / "compound_sensor_training.csv"
    csv_path = csv_path or default_path

    if csv_path.exists():
        df = pd.read_csv(csv_path)
        print(f"[loaded] metabolomics sensor data from {csv_path}: {df.shape}")
    else:
        # Generate on-the-fly using compound_sensor_map
        from compound_sensor_map import CompoundSensorMapper

        mapper = CompoundSensorMapper()
        df = mapper.metabolomics_to_training(n_samples=n_samples, seed=seed)

        csv_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(csv_path, index=False)
        print(f"[generated] metabolomics sensor data: {df.shape} → {csv_path}")

    # Extract features and labels
    meta_cols = ["compound", "condition", "concentration_ppb", "temperature_c", "humidity_pct"]
    feature_cols = [c for c in df.columns if c not in meta_cols]

    features = df[feature_cols].copy()
    conditions = df["condition"].astype(str)

    class_names = sorted(conditions.unique().tolist())
    label_map = {name: idx for idx, name in enumerate(class_names)}
    labels = conditions.map(label_map).values.astype(int)

    return features, labels, class_names


def load_combined_training_data(
    include_uci: bool = True,
    include_synthetic: bool = True,
    include_metabolomics: bool = True,
    n_synthetic: int = 5000,
    n_metabolomics: int = 200,
    seed: int = 42,
) -> tuple[pd.DataFrame, np.ndarray, list[str]]:
    """
    Combine all available data sources into a unified training set.

    Sources:
        1. UCI Gas Sensor Drift (real MOx sensor data)
        2. Synthetic VOC data (rule-based simulation)
        3. Metabolomics-derived sensor data (GC-MS → MOx mapping)

    All sources are normalized to a common feature space.
    """
    datasets = []
    all_class_names = set()

    if include_uci:
        try:
            df, labels, classes = load_uci_gas_drift()
            # Add source tag
            df = df.copy()
            df["_source"] = "uci"
            df["_label"] = labels
            datasets.append((df, classes, "uci"))
            all_class_names.update(classes)
            print(f"[combined] UCI drift: {df.shape[0]} samples, {len(classes)} classes")
        except FileNotFoundError:
            print("[skip] UCI drift dataset not downloaded yet")

    if include_synthetic:
        df, labels, classes = generate_synthetic_voc_data(n_synthetic, seed)
        df = df.copy()
        df["_source"] = "synthetic"
        df["_label"] = labels
        datasets.append((df, classes, "synthetic"))
        all_class_names.update(classes)
        print(f"[combined] Synthetic: {df.shape[0]} samples, {len(classes)} classes")

    if include_metabolomics:
        try:
            df, labels, classes = load_metabolomics_sensor_data(n_samples=n_metabolomics, seed=seed)
            df = df.copy()
            df["_source"] = "metabolomics"
            df["_label"] = labels
            datasets.append((df, classes, "metabolomics"))
            all_class_names.update(classes)
            print(f"[combined] Metabolomics: {df.shape[0]} samples, {len(classes)} classes")
        except Exception as e:
            print(f"[skip] Metabolomics data: {e}")

    if not datasets:
        raise ValueError("No datasets available. Run download_datasets.py or generate synthetic data.")

    # Build unified class list
    unified_classes = sorted(all_class_names)
    print(f"\n[combined] Unified classes: {unified_classes}")
    print(f"[combined] Total sources: {len(datasets)}")

    return datasets, unified_classes


if __name__ == "__main__":
    print("=== Synthetic VOC Data ===")
    df, labels, classes = generate_synthetic_voc_data(1000)
    print(f"Shape: {df.shape}")
    print(f"Classes: {classes}")
    print(f"Label distribution: {np.bincount(labels)}")
    print(f"\nSample row:\n{df.iloc[0]}")

    print("\n=== Metabolomics Sensor Data ===")
    try:
        df_m, labels_m, classes_m = load_metabolomics_sensor_data(n_samples=50)
        print(f"Shape: {df_m.shape}")
        print(f"Classes: {classes_m}")
        print(f"Label distribution: {np.bincount(labels_m)}")
    except Exception as e:
        print(f"Could not load: {e}")

    print("\n=== Combined Training Data ===")
    try:
        datasets, unified = load_combined_training_data(
            include_uci=False, n_synthetic=500, n_metabolomics=50
        )
        total = sum(d[0].shape[0] for d in datasets)
        print(f"Total samples across all sources: {total}")
    except Exception as e:
        print(f"Could not combine: {e}")

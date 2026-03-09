"""
Dataset configuration and sensor mappings for VOC ML training.
"""
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
DATASETS_DIR = BASE_DIR / "datasets"
MODELS_DIR = BASE_DIR / "models"

# ============================================================
# Public VOC / Gas Sensor Datasets
# ============================================================
DATASETS = {
    # UCI Gas Sensor Array Drift Dataset
    # 13,910 measurements from 16 chemical sensors, 6 gases at various concentrations
    # Gases: Ammonia, Acetaldehyde, Acetone, Ethylene, Ethanol, Toluene
    "uci_gas_drift": {
        "url": "https://archive.ics.uci.edu/static/public/224/gas+sensor+array+drift+dataset.zip",
        "description": "16-sensor array, 6 gases, 36 months of drift data",
        "gases": ["Ammonia", "Acetaldehyde", "Acetone", "Ethylene", "Ethanol", "Toluene"],
        "n_sensors": 16,
        "n_samples": 13910,
        "features_per_sensor": 8,  # steady-state + transient features
    },

    # UCI Gas Sensor Array under Dynamic Gas Mixtures
    # Ethylene + Methane in air, Ethylene + CO in air
    "uci_gas_dynamic": {
        "url": "https://archive.ics.uci.edu/static/public/322/gas+sensor+array+under+dynamic+gas+mixtures.zip",
        "description": "16-sensor array, dynamic gas mixtures (Ethylene, Methane, CO)",
        "gases": ["Ethylene", "Methane", "CO"],
        "n_sensors": 16,
    },

    # UCI Gas Sensor Array - Low Concentration
    # 10 MOx sensors, gases at ppb level
    "uci_gas_low_conc": {
        "url": "https://archive.ics.uci.edu/static/public/1081/gas+sensor+array+low-concentration.zip",
        "description": "10 MOx sensors, 6 gases at ppb-level concentrations",
        "gases": ["Ethanol", "Ethylene", "Ammonia", "Acetaldehyde", "Acetone", "Toluene"],
        "n_sensors": 10,
    },
}

# ============================================================
# Sensor-to-Platform Compound Mapping
# Maps dataset gas names → VOC Mesh Platform compound IDs
# ============================================================
GAS_TO_COMPOUND = {
    "Ammonia": "NH3",
    "Acetaldehyde": "C2H4O",
    "Acetone": "C3H6O",
    "Ethylene": "C2H4",
    "Ethanol": "C2H5OH",
    "Toluene": "C7H8",
    "Methane": "CH4",
    "CO": "CO",
    "Formaldehyde": "HCHO",
    "Benzene": "C6H6",
    "Hydrogen": "H2",
    "H2S": "H2S",
    "NO2": "NO2",
}

# ============================================================
# Platform sensor specs (from CLAUDE.md)
# ============================================================
PLATFORM_SENSORS = {
    "SGP40": {
        "type": "MOx",
        "outputs": ["VOC_index"],
        "range_ppb": (0, 1000),
    },
    "SCD40": {
        "type": "PAS",
        "outputs": ["CO2", "temperature", "humidity"],
        "range_ppm": (400, 5000),
    },
    "SHT31": {
        "type": "capacitive",
        "outputs": ["temperature", "humidity"],
    },
    "ADS1115": {
        "type": "ADC",
        "outputs": ["raw_adc"],
        "bits": 16,
    },
    "TGS_array": {
        "type": "MOx array",
        "outputs": ["C2H5OH", "CH4", "CO", "H2", "NH3", "NO2"],
    },
    "PID_10_6eV": {
        "type": "PID",
        "outputs": ["TVOC", "VOC"],
        "range_ppb": (1, 10000),
    },
}

# Calibration constants from CLAUDE.md
CALIBRATION = {
    "temp_compensation": {"a": -0.012501, "b": 1.35347167},
    "ppm_conversion": {"a": 2.92395047, "b": 0.02952922, "c": 0.43941621},
}

# Training hyperparameters
TRAINING_DEFAULTS = {
    "batch_size": 64,
    "learning_rate": 1e-3,
    "epochs": 100,
    "val_split": 0.15,
    "test_split": 0.15,
    "random_seed": 42,
    "early_stopping_patience": 10,
}

# Target labels for classification
GAS_CLASSES = ["NH3", "C2H4O", "C3H6O", "C2H4", "C2H5OH", "C7H8"]

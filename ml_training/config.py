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
# Metabolomics Repositories (GC-MS compound targets)
# These provide WHAT compounds plants emit — not sensor data.
# Used for: target identification, compound fingerprints,
# training label enrichment, transfer learning features.
# ============================================================
METABOLOMICS_SOURCES = {
    "metabolomics_workbench": {
        "base_url": "https://www.metabolomicsworkbench.org/rest",
        "description": "NIH metabolomics repository — plant VOC emission profiles (GC-MS)",
        "endpoints": {
            "study_list": "/study/study_id",
            "study_detail": "/study/study_id/{study_id}",
            "analysis": "/study/study_id/{study_id}/analysis",
            "metabolites": "/study/study_id/{study_id}/metabolites",
        },
        # Plant-relevant study IDs (curated for agricultural VOC)
        "plant_study_keywords": [
            "plant volatile", "VOC emission", "terpene",
            "herbivore induced", "jasmonate", "salicylate",
            "ethylene", "green leaf volatile", "floral scent",
        ],
        "output_format": "json",
    },
    "metabolights": {
        "base_url": "https://www.ebi.ac.uk/metabolights/ws",
        "description": "EMBL-EBI metabolomics — plant stress & defense VOC profiles (GC-MS)",
        "endpoints": {
            "study_list": "/studies",
            "study_detail": "/studies/{study_id}",
            "metabolites": "/studies/{study_id}/metabolites",
            "assays": "/studies/{study_id}/assays",
        },
        "plant_study_keywords": [
            "plant", "volatile", "terpene", "stress",
            "infection", "herbivory", "defense", "emission",
        ],
        "output_format": "json",
    },
}

# ============================================================
# GC-MS Compound → MOx Sensor Response Mapping
# Maps metabolomics compounds to expected sensor channel responses.
# sensitivity: relative sensitivity of each sensor to this compound (0-1)
# This is the "chemical fingerprint" bridge between GC-MS data and MOx arrays.
# ============================================================
COMPOUND_SENSOR_FINGERPRINTS = {
    # --- Stress markers ---
    "ethylene": {
        "SGP40": 0.3, "TGS2602": 0.5, "TGS2620": 0.7, "PID": 0.9,
        "category": "stress", "mw": 28.05, "boiling_c": -103.7,
    },
    "ethanol": {
        "SGP40": 0.6, "TGS2602": 0.8, "TGS2620": 0.9, "MQ3": 0.95,
        "category": "stress", "mw": 46.07, "boiling_c": 78.4,
    },
    "acetaldehyde": {
        "SGP40": 0.5, "TGS2602": 0.7, "TGS2620": 0.6, "PID": 0.85,
        "category": "stress", "mw": 44.05, "boiling_c": 20.2,
    },
    "hexanal": {
        "SGP40": 0.7, "TGS2602": 0.6, "PID": 0.8,
        "category": "stress", "mw": 100.16, "boiling_c": 131,
    },
    # --- Defense VOCs ---
    "methyl_salicylate": {
        "SGP40": 0.8, "TGS2602": 0.4, "PID": 0.7,
        "category": "defense", "mw": 152.15, "boiling_c": 222,
    },
    "methyl_jasmonate": {
        "SGP40": 0.6, "TGS2602": 0.3, "PID": 0.5,
        "category": "defense", "mw": 224.3, "boiling_c": 250,
    },
    "cis-3-hexenal": {
        "SGP40": 0.75, "TGS2602": 0.5, "PID": 0.85,
        "category": "defense", "mw": 98.14, "boiling_c": 120,
    },
    "beta-caryophyllene": {
        "SGP40": 0.5, "PID": 0.4,
        "category": "defense", "mw": 204.35, "boiling_c": 262,
    },
    "DMNT": {
        "SGP40": 0.6, "PID": 0.7,
        "category": "defense", "mw": 150.26, "boiling_c": 185,
    },
    "farnesene": {
        "SGP40": 0.4, "PID": 0.5,
        "category": "defense", "mw": 204.35, "boiling_c": 260,
    },
    # --- Terpenes ---
    "isoprene": {
        "SGP40": 0.7, "TGS2602": 0.4, "PID": 0.95,
        "category": "terpene", "mw": 68.12, "boiling_c": 34.1,
    },
    "alpha-pinene": {
        "SGP40": 0.8, "TGS2602": 0.3, "PID": 0.9,
        "category": "terpene", "mw": 136.24, "boiling_c": 156,
    },
    "limonene": {
        "SGP40": 0.85, "TGS2602": 0.35, "PID": 0.88,
        "category": "terpene", "mw": 136.24, "boiling_c": 176,
    },
    "linalool": {
        "SGP40": 0.9, "TGS2602": 0.4, "PID": 0.75,
        "category": "flowering", "mw": 154.25, "boiling_c": 198,
    },
    "geraniol": {
        "SGP40": 0.85, "TGS2602": 0.35, "PID": 0.7,
        "category": "flowering", "mw": 154.25, "boiling_c": 230,
    },
    # --- Soil gases ---
    "methane": {
        "SGP40": 0.1, "TGS2611": 0.95, "MQ4": 0.9,
        "category": "soil", "mw": 16.04, "boiling_c": -161.5,
    },
    "ammonia": {
        "SGP40": 0.4, "TGS2602": 0.6, "MQ135": 0.85,
        "category": "soil", "mw": 17.03, "boiling_c": -33.3,
    },
    "H2S": {
        "SGP40": 0.3, "TGS2602": 0.8, "MQ136": 0.9,
        "category": "soil", "mw": 34.08, "boiling_c": -60,
    },
    # --- Atmosphere ---
    "CO": {
        "SGP40": 0.2, "TGS5042": 0.95, "MQ7": 0.9,
        "category": "atmosphere", "mw": 28.01, "boiling_c": -191.5,
    },
    "NO2": {
        "SGP40": 0.15, "MiCS2714": 0.9,
        "category": "atmosphere", "mw": 46.01, "boiling_c": 21.2,
    },
    "ozone": {
        "SGP40": 0.1, "MQ131": 0.85,
        "category": "atmosphere", "mw": 48.0, "boiling_c": -112,
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

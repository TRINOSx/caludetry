"""Feature extraction engine for VOC sensor readings."""

from __future__ import annotations

import numpy as np

# 50 key VOC / environmental compound slots
VOC_COMPOUND_SLOTS: list[str] = [
    "ethylene", "ethanol", "methane", "ammonia", "CO2",
    "CO", "H2", "formaldehyde", "ozone", "H2S",
    "isoprene", "alpha-pinene", "beta-pinene", "limonene", "linalool",
    "methyl_salicylate", "methyl_jasmonate", "cis-3-hexenal", "hexanal", "nonanal",
    "TVOC", "VOC", "benzene", "toluene", "xylene",
    "styrene", "acetone", "acetaldehyde", "NO2", "SO2",
    "butadiene", "carbon_disulfide", "dimethyl_disulfide", "methanol", "trimethylamine",
    "indole", "geraniol", "myrcene", "ocimene", "farnesene",
    "beta-caryophyllene", "DMNT", "TMTT", "acetic_acid", "formic_acid",
    "propane", "butane", "SGP40", "PM25", "PM10",
]

FEATURE_DIM = 128

# Environmental context keys
_ENV_KEYS = ["PM25", "PM10", "CO2", "humidity", "temperature"]

# Top compounds whose values are temperature-normalised (13 slots)
_TEMP_NORM_COMPOUNDS = [
    "ethylene", "ethanol", "methane", "ammonia", "isoprene",
    "alpha-pinene", "limonene", "linalool", "methyl_salicylate",
    "methyl_jasmonate", "benzene", "toluene", "TVOC",
]


def _safe_mean(values: list[float]) -> float:
    return float(np.mean(values)) if values else 0.0


def _safe_max(values: list[float]) -> float:
    return float(np.max(values)) if values else 0.0


def _delta(values: list[float]) -> float:
    """Return last - first value (proxy for delta over the window)."""
    if len(values) < 2:
        return 0.0
    return float(values[-1] - values[0])


def extract_features(
    readings: list[dict],
    window_seconds: int = 60,
) -> np.ndarray:
    """Convert a list of raw sensor reading dicts into a 128-dim feature vector.

    Each reading dict is expected to have compound names as keys and float
    values.  Optional keys: ``humidity``, ``temperature``, ``timestamp``.

    The feature layout:
        [0..149]   50 compounds x 3 (mean, max, delta)   = 150
        [150..154] 5 environmental context values          =   5
        [155..167] 13 temperature-normalised compounds     =  13
        Total raw = 168  ->  truncated / padded to 128
    """

    # Collect per-compound time-series -----------------------------------------
    compound_series: dict[str, list[float]] = {c: [] for c in VOC_COMPOUND_SLOTS}
    env_series: dict[str, list[float]] = {k: [] for k in _ENV_KEYS}

    for r in readings:
        for c in VOC_COMPOUND_SLOTS:
            if c in r:
                compound_series[c].append(float(r[c]))
        for k in _ENV_KEYS:
            if k in r:
                env_series[k].append(float(r[k]))

    # Per-compound features: mean, max, delta (50 * 3 = 150) ------------------
    compound_feats: list[float] = []
    for c in VOC_COMPOUND_SLOTS:
        vals = compound_series[c]
        compound_feats.append(_safe_mean(vals))
        compound_feats.append(_safe_max(vals))
        compound_feats.append(_delta(vals))

    # Environmental context (5) ------------------------------------------------
    env_feats = [_safe_mean(env_series[k]) for k in _ENV_KEYS]

    # Temperature-normalised top compounds (13) --------------------------------
    temp_mean = _safe_mean(env_series["temperature"]) or 25.0  # fallback 25 C
    temp_norm_feats: list[float] = []
    for c in _TEMP_NORM_COMPOUNDS:
        raw_mean = _safe_mean(compound_series[c])
        # Simple normalisation: divide by (temperature / 25) to compensate for
        # volatility increase at higher temps.
        temp_norm_feats.append(raw_mean / (temp_mean / 25.0) if temp_mean != 0 else raw_mean)

    # Concatenate and truncate / pad to 128 ------------------------------------
    raw_vector = np.array(compound_feats + env_feats + temp_norm_feats, dtype=np.float32)

    if raw_vector.shape[0] >= FEATURE_DIM:
        return raw_vector[:FEATURE_DIM]
    else:
        padded = np.zeros(FEATURE_DIM, dtype=np.float32)
        padded[: raw_vector.shape[0]] = raw_vector
        return padded

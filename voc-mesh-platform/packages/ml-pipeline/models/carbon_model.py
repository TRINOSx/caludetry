"""Carbon sequestration index model.

Produces a carbon_index score (0-100) representing relative carbon
sequestration capacity based on CO2 absorption patterns, VOC-based NDVI
proxies, and soil respiration indicators.

Uses LinearRegression with engineered interaction features.
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score

logger = logging.getLogger(__name__)

FEATURE_DIM = 128

# Feature indices for key inputs (mean values in the 128-dim vector)
_CO2_MEAN_IDX = 4 * 3       # CO2 slot 4 -> index 12
_CO2_MAX_IDX = 4 * 3 + 1    # index 13
_CO2_DELTA_IDX = 4 * 3 + 2  # index 14
_ISOPRENE_MEAN_IDX = 10 * 3  # index 30  (NDVI proxy)
_ALPHA_PINENE_MEAN_IDX = 11 * 3  # index 33
_METHANE_MEAN_IDX = 2 * 3    # index 6  (soil respiration)
_H2S_MEAN_IDX = 9 * 3        # index 27 (soil microbiome)


class CarbonModel:
    """Linear regression carbon sequestration scorer."""

    def __init__(self) -> None:
        self._lr: Optional[LinearRegression] = None
        self._ort_session = None

    # ------------------------------------------------------------------
    # Feature engineering
    # ------------------------------------------------------------------

    @staticmethod
    def _engineer(X: np.ndarray) -> np.ndarray:
        """Add interaction / ratio features to the raw 128-dim vector."""
        n = X.shape[0]
        extras = np.zeros((n, 6), dtype=np.float32)

        co2_mean = X[:, min(_CO2_MEAN_IDX, FEATURE_DIM - 1)]
        co2_delta = X[:, min(_CO2_DELTA_IDX, FEATURE_DIM - 1)]
        iso_mean = X[:, min(_ISOPRENE_MEAN_IDX, FEATURE_DIM - 1)]
        pinene = X[:, min(_ALPHA_PINENE_MEAN_IDX, FEATURE_DIM - 1)]
        methane = X[:, min(_METHANE_MEAN_IDX, FEATURE_DIM - 1)]
        h2s = X[:, min(_H2S_MEAN_IDX, FEATURE_DIM - 1)]

        # CO2 absorption rate proxy (negative delta = absorption)
        extras[:, 0] = -co2_delta
        # NDVI proxy from terpene emissions
        extras[:, 1] = iso_mean + 0.5 * pinene
        # Soil respiration indicator
        extras[:, 2] = methane + 0.3 * h2s
        # Interaction: absorption * canopy health
        extras[:, 3] = (-co2_delta) * (iso_mean + 0.5 * pinene)
        # CO2 level itself (lower ambient = more absorption)
        extras[:, 4] = -co2_mean
        # Terpene diversity proxy
        extras[:, 5] = np.abs(iso_mean - pinene)

        return np.hstack([X, extras])

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def train(self, X: np.ndarray, y: np.ndarray) -> dict:
        """Train on *X* (n, 128) and *y* (n,) carbon_index in [0, 100]."""
        X_eng = self._engineer(X)

        self._lr = LinearRegression()
        self._lr.fit(X_eng, y)

        preds = np.clip(self._lr.predict(X_eng), 0, 100)
        mae = mean_absolute_error(y, preds)
        r2 = r2_score(y, preds)
        logger.info("CarbonModel trained  |  train MAE=%.3f  R2=%.3f", mae, r2)

        return {"mae": mae, "r2": r2}

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def predict(self, features: np.ndarray) -> float:
        """Return carbon_index in [0, 100]."""
        x = features.astype(np.float32).reshape(1, FEATURE_DIM)

        if self._ort_session is not None:
            x_eng = self._engineer(x)
            input_name = self._ort_session.get_inputs()[0].name
            result = self._ort_session.run(None, {input_name: x_eng.astype(np.float32)})
            raw = float(result[0].flat[0])
        elif self._lr is not None:
            x_eng = self._engineer(x)
            raw = float(self._lr.predict(x_eng)[0])
        else:
            raise RuntimeError("CarbonModel has no trained weights loaded")

        return float(np.clip(raw, 0.0, 100.0))

    # ------------------------------------------------------------------
    # ONNX
    # ------------------------------------------------------------------

    def export_onnx(self, path: str) -> None:
        if self._lr is None:
            raise RuntimeError("No trained model to export")

        from skl2onnx import convert_sklearn
        from skl2onnx.common.data_types import FloatTensorType

        # Input dim = 128 + 6 engineered features
        input_dim = FEATURE_DIM + 6
        initial_type = [("X", FloatTensorType([None, input_dim]))]
        onnx_model = convert_sklearn(self._lr, initial_types=initial_type)

        with open(path, "wb") as f:
            f.write(onnx_model.SerializeToString())
        logger.info("CarbonModel exported to %s", path)

    def load_onnx(self, path: str) -> None:
        import onnxruntime as ort

        self._ort_session = ort.InferenceSession(path)
        logger.info("CarbonModel loaded ONNX from %s", path)

    # ------------------------------------------------------------------
    # Synthetic data
    # ------------------------------------------------------------------

    @staticmethod
    def generate_synthetic_data(n_samples: int = 1000) -> tuple[np.ndarray, np.ndarray]:
        rng = np.random.default_rng(46)
        X = rng.normal(loc=0.5, scale=0.3, size=(n_samples, FEATURE_DIM)).astype(np.float32)

        co2_delta = X[:, min(_CO2_DELTA_IDX, FEATURE_DIM - 1)]
        iso = X[:, min(_ISOPRENE_MEAN_IDX, FEATURE_DIM - 1)]
        pinene = X[:, min(_ALPHA_PINENE_MEAN_IDX, FEATURE_DIM - 1)]
        methane = X[:, min(_METHANE_MEAN_IDX, FEATURE_DIM - 1)]

        y = (
            30.0
            - 20.0 * co2_delta       # negative delta -> higher score
            + 15.0 * iso              # healthy canopy
            + 10.0 * pinene
            - 5.0 * methane           # soil respiration cost
            + rng.normal(0, 4, n_samples)
        )
        y = np.clip(y, 0.0, 100.0).astype(np.float32)

        return X, y

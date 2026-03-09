"""Plant stress detection model.

Predicts a stress percentage (0-100) from a 128-dim VOC feature vector using a
RandomForestRegressor.  Supports ONNX export / import for production serving.
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

logger = logging.getLogger(__name__)

FEATURE_DIM = 128


class StressModel:
    """RandomForest-based plant stress regressor."""

    def __init__(self) -> None:
        self._rf: Optional[RandomForestRegressor] = None
        self._ort_session = None  # onnxruntime InferenceSession

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def train(self, X: np.ndarray, y: np.ndarray) -> dict:
        """Train on feature matrix *X* (n, 128) and target *y* (n,) in [0, 100]."""
        self._rf = RandomForestRegressor(
            n_estimators=200,
            max_depth=16,
            min_samples_leaf=4,
            random_state=42,
            n_jobs=-1,
        )
        self._rf.fit(X, y)

        preds = self._rf.predict(X)
        mae = mean_absolute_error(y, preds)
        logger.info("StressModel trained  |  train MAE=%.3f", mae)

        # Feature importance
        importances = self._rf.feature_importances_
        top_idx = np.argsort(importances)[-10:][::-1]
        logger.info(
            "Top-10 feature indices: %s  importance: %s",
            top_idx.tolist(),
            np.round(importances[top_idx], 4).tolist(),
        )

        return {"mae": mae, "top_features": top_idx.tolist()}

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def predict(self, features: np.ndarray) -> float:
        """Return stress_pct in [0, 100].

        Uses ONNX runtime if available, otherwise falls back to sklearn.
        """
        x = features.astype(np.float32).reshape(1, FEATURE_DIM)

        if self._ort_session is not None:
            input_name = self._ort_session.get_inputs()[0].name
            result = self._ort_session.run(None, {input_name: x})
            raw = float(result[0].flat[0])
        elif self._rf is not None:
            raw = float(self._rf.predict(x)[0])
        else:
            raise RuntimeError("StressModel has no trained weights loaded")

        return float(np.clip(raw, 0.0, 100.0))

    # ------------------------------------------------------------------
    # ONNX
    # ------------------------------------------------------------------

    def export_onnx(self, path: str) -> None:
        """Export the trained sklearn model to ONNX format."""
        if self._rf is None:
            raise RuntimeError("No trained model to export")

        from skl2onnx import convert_sklearn
        from skl2onnx.common.data_types import FloatTensorType

        initial_type = [("X", FloatTensorType([None, FEATURE_DIM]))]
        onnx_model = convert_sklearn(self._rf, initial_types=initial_type)

        with open(path, "wb") as f:
            f.write(onnx_model.SerializeToString())
        logger.info("StressModel exported to %s", path)

    def load_onnx(self, path: str) -> None:
        """Load an ONNX model for inference."""
        import onnxruntime as ort

        self._ort_session = ort.InferenceSession(path)
        logger.info("StressModel loaded ONNX from %s", path)

    # ------------------------------------------------------------------
    # Synthetic data
    # ------------------------------------------------------------------

    @staticmethod
    def generate_synthetic_data(n_samples: int = 1000) -> tuple[np.ndarray, np.ndarray]:
        """Generate synthetic training data for testing / bootstrapping.

        X: (n_samples, 128)  random sensor-like features
        y: (n_samples,)      stress_pct in [0, 100]
        """
        rng = np.random.default_rng(42)
        X = rng.normal(loc=0.5, scale=0.3, size=(n_samples, FEATURE_DIM)).astype(np.float32)

        # Stress is driven mainly by ethylene (slot 0-2), methyl_jasmonate (slot 48-50),
        # and inversely by humidity context (slot 153).
        y = (
            15.0 * X[:, 0]       # ethylene mean
            + 10.0 * X[:, 1]     # ethylene max
            + 12.0 * X[:, 48]    # methyl_jasmonate mean
            - 8.0 * X[:, 100]    # some mid-range feature
            + 20.0               # offset
            + rng.normal(0, 3, n_samples)  # noise
        )
        y = np.clip(y, 0.0, 100.0).astype(np.float32)

        return X, y

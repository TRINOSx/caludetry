"""Bloom probability prediction model.

Predicts the probability of flowering / bloom (0-1) from a 128-dim feature
vector using a GradientBoostingClassifier.
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, roc_auc_score

logger = logging.getLogger(__name__)

FEATURE_DIM = 128


class BloomModel:
    """GradientBoosting-based bloom probability classifier."""

    def __init__(self) -> None:
        self._clf: Optional[GradientBoostingClassifier] = None
        self._ort_session = None

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def train(self, X: np.ndarray, y: np.ndarray) -> dict:
        """Train on *X* (n, 128) and binary *y* (n,) where 1=bloom."""
        self._clf = GradientBoostingClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            random_state=42,
        )
        self._clf.fit(X, y)

        proba = self._clf.predict_proba(X)[:, 1]
        preds = self._clf.predict(X)
        acc = accuracy_score(y, preds)
        auc = roc_auc_score(y, proba)
        logger.info("BloomModel trained  |  train acc=%.3f  AUC=%.3f", acc, auc)

        importances = self._clf.feature_importances_
        top_idx = np.argsort(importances)[-10:][::-1]
        logger.info(
            "Top-10 feature indices: %s  importance: %s",
            top_idx.tolist(),
            np.round(importances[top_idx], 4).tolist(),
        )

        return {"accuracy": acc, "auc": auc, "top_features": top_idx.tolist()}

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def predict(self, features: np.ndarray) -> float:
        """Return bloom_probability in [0, 1]."""
        x = features.astype(np.float32).reshape(1, FEATURE_DIM)

        if self._ort_session is not None:
            input_name = self._ort_session.get_inputs()[0].name
            result = self._ort_session.run(None, {input_name: x})
            # ONNX classifier output: [labels, probabilities]
            proba_map = result[1]  # list of dicts [{0: p0, 1: p1}]
            if isinstance(proba_map, list):
                return float(proba_map[0].get(1, proba_map[0].get("1", 0.0)))
            return float(proba_map[0, 1])
        elif self._clf is not None:
            return float(self._clf.predict_proba(x)[0, 1])
        else:
            raise RuntimeError("BloomModel has no trained weights loaded")

    # ------------------------------------------------------------------
    # ONNX
    # ------------------------------------------------------------------

    def export_onnx(self, path: str) -> None:
        if self._clf is None:
            raise RuntimeError("No trained model to export")

        from skl2onnx import convert_sklearn
        from skl2onnx.common.data_types import FloatTensorType

        initial_type = [("X", FloatTensorType([None, FEATURE_DIM]))]
        onnx_model = convert_sklearn(self._clf, initial_types=initial_type)

        with open(path, "wb") as f:
            f.write(onnx_model.SerializeToString())
        logger.info("BloomModel exported to %s", path)

    def load_onnx(self, path: str) -> None:
        import onnxruntime as ort

        self._ort_session = ort.InferenceSession(path)
        logger.info("BloomModel loaded ONNX from %s", path)

    # ------------------------------------------------------------------
    # Synthetic data
    # ------------------------------------------------------------------

    @staticmethod
    def generate_synthetic_data(n_samples: int = 1000) -> tuple[np.ndarray, np.ndarray]:
        """Generate synthetic bloom / no-bloom data.

        Bloom is influenced by terpene compounds (limonene, linalool, geraniol)
        and temperature.
        """
        rng = np.random.default_rng(43)
        X = rng.normal(loc=0.5, scale=0.3, size=(n_samples, FEATURE_DIM)).astype(np.float32)

        # Bloom signal from terpenes (slots ~39-42 in compound features)
        # and temperature-normalised compounds in upper feature range
        score = (
            3.0 * X[:, 39]   # limonene mean
            + 2.5 * X[:, 42]  # linalool mean
            + 2.0 * X[:, 105] # geraniol proxy
            - 1.5 * X[:, 10]  # inverse stress indicator
            + rng.normal(0, 0.5, n_samples)
        )
        y = (score > np.median(score)).astype(np.int32)

        return X, y

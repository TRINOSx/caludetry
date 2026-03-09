"""Fire / smoke risk detection model.

Hybrid rule-based + ML approach:
  - Rule layer: if smoke compounds (CO, benzene, toluene) exceed threshold AND
    humidity < 30%, fire alert is raised immediately.
  - ML layer: RandomForestClassifier provides a secondary smoke-detection
    confidence that catches subtler patterns.
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

logger = logging.getLogger(__name__)

FEATURE_DIM = 128

# Feature indices (within the 128-dim vector) for key compounds.
# These correspond to the *mean* value for each compound in the feature layout:
#   slot_index = compound_position_in_VOC_COMPOUND_SLOTS * 3
_CO_MEAN_IDX = 5 * 3       # CO is slot 5 -> index 15
_BENZENE_MEAN_IDX = 22 * 3  # benzene is slot 22 -> index 66
_TOLUENE_MEAN_IDX = 23 * 3  # toluene is slot 23 -> index 69

# Environmental context block starts at index 150 in raw vector but we
# truncate to 128, so humidity is unreachable directly.  We use a proxy:
# slot 48 (PM25 mean = index 48*3=144 -> not in 128 either).  In practice
# the worker passes humidity separately; here we use a mid-range proxy.
_HUMIDITY_PROXY_IDX = 100

# Rule thresholds
CO_THRESHOLD = 1.5
BENZENE_THRESHOLD = 1.2
TOLUENE_THRESHOLD = 1.2
HUMIDITY_CRITICAL_THRESHOLD = 0.3  # normalised


class FireModel:
    """Hybrid rule + ML fire / smoke detection."""

    def __init__(self) -> None:
        self._clf: Optional[RandomForestClassifier] = None
        self._ort_session = None

    # ------------------------------------------------------------------
    # Training (ML component only)
    # ------------------------------------------------------------------

    def train(self, X: np.ndarray, y: np.ndarray) -> dict:
        """Train the ML smoke-detection classifier.

        *y* is binary: 1 = smoke / fire present, 0 = safe.
        """
        self._clf = RandomForestClassifier(
            n_estimators=150,
            max_depth=10,
            min_samples_leaf=5,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        )
        self._clf.fit(X, y)

        preds = self._clf.predict(X)
        acc = accuracy_score(y, preds)
        logger.info("FireModel trained  |  train acc=%.3f", acc)

        return {"accuracy": acc}

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def predict(self, features: np.ndarray) -> dict:
        """Return ``{alert, smoke_detected, humidity_critical}``."""
        x = features.astype(np.float32).reshape(1, FEATURE_DIM)
        flat = x[0]

        # --- Rule layer ---
        co_val = flat[min(_CO_MEAN_IDX, FEATURE_DIM - 1)]
        benzene_val = flat[min(_BENZENE_MEAN_IDX, FEATURE_DIM - 1)]
        toluene_val = flat[min(_TOLUENE_MEAN_IDX, FEATURE_DIM - 1)]
        humidity_val = flat[min(_HUMIDITY_PROXY_IDX, FEATURE_DIM - 1)]

        smoke_rule = (
            co_val > CO_THRESHOLD
            and benzene_val > BENZENE_THRESHOLD
            and toluene_val > TOLUENE_THRESHOLD
        )
        humidity_critical = bool(humidity_val < HUMIDITY_CRITICAL_THRESHOLD)

        # --- ML layer ---
        if self._ort_session is not None:
            input_name = self._ort_session.get_inputs()[0].name
            result = self._ort_session.run(None, {input_name: x})
            ml_smoke = int(result[0][0]) == 1
        elif self._clf is not None:
            ml_smoke = bool(self._clf.predict(x)[0] == 1)
        else:
            ml_smoke = False

        smoke_detected = bool(smoke_rule or ml_smoke)
        alert = bool(smoke_detected and humidity_critical)

        return {
            "alert": alert,
            "smoke_detected": smoke_detected,
            "humidity_critical": humidity_critical,
        }

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
        logger.info("FireModel exported to %s", path)

    def load_onnx(self, path: str) -> None:
        import onnxruntime as ort

        self._ort_session = ort.InferenceSession(path)
        logger.info("FireModel loaded ONNX from %s", path)

    # ------------------------------------------------------------------
    # Synthetic data
    # ------------------------------------------------------------------

    @staticmethod
    def generate_synthetic_data(n_samples: int = 1000) -> tuple[np.ndarray, np.ndarray]:
        rng = np.random.default_rng(45)
        X = rng.normal(loc=0.5, scale=0.3, size=(n_samples, FEATURE_DIM)).astype(np.float32)
        y = np.zeros(n_samples, dtype=np.int32)

        # ~20% fire-positive samples
        n_fire = n_samples // 5
        fire_idx = rng.choice(n_samples, size=n_fire, replace=False)
        y[fire_idx] = 1

        # Inject smoke compound signal into positive samples
        co_idx = min(_CO_MEAN_IDX, FEATURE_DIM - 1)
        benz_idx = min(_BENZENE_MEAN_IDX, FEATURE_DIM - 1)
        tol_idx = min(_TOLUENE_MEAN_IDX, FEATURE_DIM - 1)
        hum_idx = min(_HUMIDITY_PROXY_IDX, FEATURE_DIM - 1)

        X[fire_idx, co_idx] += 2.0
        X[fire_idx, benz_idx] += 1.8
        X[fire_idx, tol_idx] += 1.8
        X[fire_idx, hum_idx] -= 1.0  # low humidity

        return X, y

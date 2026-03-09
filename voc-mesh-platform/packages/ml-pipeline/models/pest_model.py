"""Pest / pathogen detection model.

Classifies parcela status into one of several pest / pathogen zone types using
a RandomForestClassifier.
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

logger = logging.getLogger(__name__)

FEATURE_DIM = 128

ZONE_TYPES: list[str] = [
    "none",
    "fungal",
    "bacterial",
    "insect_aphid",
    "insect_mite",
    "nematode",
]

_ZONE_TO_IDX = {z: i for i, z in enumerate(ZONE_TYPES)}
_IDX_TO_ZONE = {i: z for z, i in _ZONE_TO_IDX.items()}


class PestModel:
    """RandomForest pest / pathogen classifier."""

    def __init__(self) -> None:
        self._clf: Optional[RandomForestClassifier] = None
        self._ort_session = None

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def train(self, X: np.ndarray, y: np.ndarray) -> dict:
        """Train on *X* (n, 128) and integer labels *y* (n,) mapping to ZONE_TYPES."""
        self._clf = RandomForestClassifier(
            n_estimators=250,
            max_depth=14,
            min_samples_leaf=3,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        )
        self._clf.fit(X, y)

        preds = self._clf.predict(X)
        acc = accuracy_score(y, preds)
        report = classification_report(y, preds, target_names=ZONE_TYPES, zero_division=0)
        logger.info("PestModel trained  |  train acc=%.3f", acc)
        logger.info("Classification report:\n%s", report)

        importances = self._clf.feature_importances_
        top_idx = np.argsort(importances)[-10:][::-1]
        logger.info(
            "Top-10 feature indices: %s  importance: %s",
            top_idx.tolist(),
            np.round(importances[top_idx], 4).tolist(),
        )

        return {"accuracy": acc, "top_features": top_idx.tolist()}

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def predict(self, features: np.ndarray) -> dict:
        """Return ``{detected, zone_type, confidence}``."""
        x = features.astype(np.float32).reshape(1, FEATURE_DIM)

        if self._ort_session is not None:
            input_name = self._ort_session.get_inputs()[0].name
            result = self._ort_session.run(None, {input_name: x})
            label = int(result[0][0])
            proba_map = result[1]
            if isinstance(proba_map, list):
                confidence = float(proba_map[0].get(label, proba_map[0].get(str(label), 0.0)))
            else:
                confidence = float(proba_map[0, label])
        elif self._clf is not None:
            label = int(self._clf.predict(x)[0])
            confidence = float(np.max(self._clf.predict_proba(x)[0]))
        else:
            raise RuntimeError("PestModel has no trained weights loaded")

        zone_type = _IDX_TO_ZONE.get(label, "none")
        detected = zone_type != "none"

        return {
            "detected": detected,
            "zone_type": zone_type,
            "confidence": round(confidence, 4),
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
        logger.info("PestModel exported to %s", path)

    def load_onnx(self, path: str) -> None:
        import onnxruntime as ort

        self._ort_session = ort.InferenceSession(path)
        logger.info("PestModel loaded ONNX from %s", path)

    # ------------------------------------------------------------------
    # Synthetic data
    # ------------------------------------------------------------------

    @staticmethod
    def generate_synthetic_data(n_samples: int = 1000) -> tuple[np.ndarray, np.ndarray]:
        """Generate synthetic pest detection data across all zone types."""
        rng = np.random.default_rng(44)
        X = rng.normal(loc=0.5, scale=0.3, size=(n_samples, FEATURE_DIM)).astype(np.float32)

        n_classes = len(ZONE_TYPES)
        y = np.zeros(n_samples, dtype=np.int32)

        samples_per_class = n_samples // n_classes
        for cls_idx in range(n_classes):
            start = cls_idx * samples_per_class
            end = start + samples_per_class if cls_idx < n_classes - 1 else n_samples
            y[start:end] = cls_idx

            # Inject class-specific signal
            if cls_idx == 1:    # fungal
                X[start:end, 45] += 1.5   # methyl_salicylate region
                X[start:end, 54] += 1.0   # hexanal region
            elif cls_idx == 2:  # bacterial
                X[start:end, 48] += 1.5   # methyl_jasmonate
                X[start:end, 96] += 1.2   # dimethyl_disulfide region
            elif cls_idx == 3:  # insect_aphid
                X[start:end, 30] += 2.0   # isoprene region
                X[start:end, 33] += 1.5   # alpha-pinene region
            elif cls_idx == 4:  # insect_mite
                X[start:end, 51] += 1.8   # cis-3-hexenal region
                X[start:end, 120] += 1.3  # DMNT proxy
            elif cls_idx == 5:  # nematode
                X[start:end, 57] += 1.5   # nonanal region
                X[start:end, 99] += 1.0   # carbon_disulfide region

        # Shuffle
        perm = rng.permutation(n_samples)
        return X[perm], y[perm]

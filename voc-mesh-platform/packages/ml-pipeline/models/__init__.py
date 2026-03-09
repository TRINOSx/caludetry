"""Model registry for VOC ML pipeline."""

from __future__ import annotations

from typing import Any

from models.stress_model import StressModel
from models.bloom_model import BloomModel
from models.pest_model import PestModel
from models.fire_model import FireModel
from models.carbon_model import CarbonModel


class ModelRegistry:
    """Loads and caches all model instances."""

    _REGISTRY: dict[str, type] = {
        "stress": StressModel,
        "bloom": BloomModel,
        "pest": PestModel,
        "fire": FireModel,
        "carbon": CarbonModel,
    }

    def __init__(self) -> None:
        self._instances: dict[str, Any] = {}

    def load_all(self, onnx_dir: str = "models") -> None:
        """Instantiate every registered model and attempt to load ONNX weights."""
        import os

        for name, cls in self._REGISTRY.items():
            instance = cls()
            onnx_path = os.path.join(onnx_dir, f"{name}.onnx")
            if os.path.exists(onnx_path):
                instance.load_onnx(onnx_path)
            self._instances[name] = instance

    def get_model(self, name: str) -> Any:
        """Return a loaded model instance by name.

        Raises ``KeyError`` if the model has not been loaded.
        """
        if name not in self._instances:
            if name in self._REGISTRY:
                self._instances[name] = self._REGISTRY[name]()
            else:
                raise KeyError(f"Unknown model: {name}")
        return self._instances[name]

    @property
    def available(self) -> list[str]:
        return list(self._REGISTRY.keys())

"""
VOC Field Intelligence - Plant Metabolism ML Model
Multimodal prediction: VOC + Soil + Climate + AlphaEarth -> Plant State
"""

import json
import numpy as np
from datetime import datetime


# ================================
# VOC Compound Registry (300+ compounds)
# ================================
VOC_COMPOUNDS = [
    "VOC", "VOC2", "TVOC", "TVOC2", "CO", "CO2", "NO2",
    "C2H5OH", "H2", "NH3", "CH4", "CH3COOH", "C2H2",
    "C3H3N", "C6H6", "C4H6", "CS2", "C2H6S2", "C2H4",
    "C2H4O", "HCHO", "HCOOH", "HCl", "HCN", "C4H8",
    "CH3OH", "CH4S", "C2H6S", "C8H10", "C8H8", "C7H8",
    "C3H6N", "H2S", "EtOH", "C3H8", "C4H10", "O3",
    # Extended
    "C12H8", "C12H10", "C2H4O2", "C2H5NO", "C4H6O3",
    "C4H8O2", "C3H6O", "C8H8O", "C2H3BrO", "C3H4O",
    "C3H6O2", "C3H5Br", "C3H5Cl",
    # Agricultural VOCs
    "isoprene", "alpha_pinene", "beta_pinene", "limonene",
    "linalool", "methyl_salicylate", "methyl_jasmonate",
    "cis_3_hexenal", "trans_2_hexenal", "hexanal",
    "nonanal", "decanal", "beta_caryophyllene",
    "DMNT", "TMTT", "indole", "geraniol", "myrcene",
    "ocimene", "farnesene",
]

SOIL_FEATURES = ["ph", "conductivity", "moisture", "temperature",
                 "nitrogen", "phosphorus", "potassium"]

CLIMATE_FEATURES = ["temperature", "humidity", "pressure", "wind_speed",
                    "solar_radiation", "uv_index", "precipitation"]

# Total feature vector size
FEATURE_DIM = len(VOC_COMPOUNDS) + len(SOIL_FEATURES) + len(CLIMATE_FEATURES) + 64  # +64 for AlphaEarth


class PlantMetabolismModel:
    """
    Rule-based + statistical model for plant metabolism prediction.
    Replace with trained neural network when sufficient data is collected.
    """

    def __init__(self):
        self.version = "v2.1-rule-based"
        self.voc_weights = self._init_voc_weights()
        self.thresholds = {
            "methane": {"normal": 400, "elevated": 600, "high": 1000},
            "nh3": {"normal": 200, "elevated": 400, "high": 600},
            "ethanol": {"normal": 200, "elevated": 400, "high": 600},
            "tvoc": {"normal": 300, "elevated": 600, "high": 1000},
            "co": {"normal": 300, "elevated": 500, "high": 800},
            "formaldehyde": {"normal": 200, "elevated": 400, "high": 600},
        }

    def _init_voc_weights(self):
        """Weights for each VOC compound's contribution to plant state."""
        weights = {}
        # Stress indicators
        weights["C2H4"] = {"stress": 0.8, "plagues": 0.2}   # Ethylene
        weights["C2H5OH"] = {"stress": 0.7, "plagues": 0.1}  # Ethanol (hypoxia)
        weights["HCHO"] = {"stress": 0.5, "plagues": 0.3}    # Formaldehyde
        weights["H2S"] = {"stress": 0.6, "plagues": 0.4}     # Root issues
        weights["NH3"] = {"stress": 0.5, "plagues": 0.2}     # Nitrogen imbalance

        # Defense / plague indicators
        weights["methyl_salicylate"] = {"stress": 0.3, "plagues": 0.8}
        weights["methyl_jasmonate"] = {"stress": 0.2, "plagues": 0.9}
        weights["cis_3_hexenal"] = {"stress": 0.4, "plagues": 0.7}
        weights["beta_caryophyllene"] = {"stress": 0.2, "plagues": 0.8}
        weights["DMNT"] = {"stress": 0.3, "plagues": 0.9}
        weights["TMTT"] = {"stress": 0.2, "plagues": 0.95}
        weights["farnesene"] = {"stress": 0.1, "plagues": 0.85}
        weights["ocimene"] = {"stress": 0.2, "plagues": 0.8}

        # Flowering indicators
        weights["linalool"] = {"flowering": 0.8}
        weights["geraniol"] = {"flowering": 0.7}

        return weights

    def predict(self, sensor_data: dict) -> dict:
        """
        Predict plant state from sensor data.

        Args:
            sensor_data: Dict with VOC readings, soil data, climate data

        Returns:
            Dict with stress, plagues, metabolism, flowering predictions
        """
        stress = self._calculate_stress(sensor_data)
        plagues = self._calculate_plague_risk(sensor_data)
        metabolism = self._calculate_metabolism(sensor_data, stress)
        flowering = self._calculate_flowering(sensor_data)

        return {
            "timestamp": datetime.now().isoformat(),
            "model_version": self.version,
            "stress": round(min(100, max(0, stress)), 2),
            "plagues": round(min(100, max(0, plagues)), 2),
            "metabolism": round(min(100, max(0, metabolism)), 2),
            "flowering": round(min(100, max(0, flowering)), 2),
            "confidence": self._calculate_confidence(sensor_data),
            "alerts": self._generate_alerts(sensor_data),
        }

    def _calculate_stress(self, data: dict) -> float:
        stress = 5.0  # Base

        # VOC-based stress
        tvoc = data.get("tvoc", 0)
        if tvoc > 400:
            stress += (tvoc - 400) * 0.03
        if tvoc > 700:
            stress += (tvoc - 700) * 0.05

        # Ethylene/ethanol stress
        ethanol = data.get("ethanol", data.get("C2H5OH", 0))
        if ethanol > 300:
            stress += (ethanol - 300) * 0.04

        # NH3 stress (nitrogen)
        nh3 = data.get("nh3", data.get("NH3", 0))
        if nh3 > 200:
            stress += (nh3 - 200) * 0.03

        # Temperature stress
        temp = data.get("temperature", 20)
        if temp < 10:
            stress += (10 - temp) * 2
        elif temp > 35:
            stress += (temp - 35) * 3

        # Soil moisture stress
        moisture = data.get("soil_moisture", 40)
        if moisture < 20:
            stress += (20 - moisture) * 0.5
        elif moisture > 80:
            stress += (moisture - 80) * 0.3

        return stress

    def _calculate_plague_risk(self, data: dict) -> float:
        risk = 0.0

        # Defense VOC patterns
        for compound, weights in self.voc_weights.items():
            if "plagues" in weights:
                value = data.get(compound, 0)
                if value > 0:
                    risk += value * weights["plagues"] * 0.01

        # High TVOC + specific patterns
        tvoc = data.get("tvoc", 0)
        if tvoc > 500:
            risk += (tvoc - 500) * 0.02

        return risk

    def _calculate_metabolism(self, data: dict, stress: float) -> float:
        base = 85.0

        # Stress reduces metabolism
        base -= stress * 0.5

        # Temperature affects metabolism (optimal 20-30C)
        temp = data.get("temperature", 20)
        if 20 <= temp <= 30:
            base += 5  # Optimal
        elif temp < 10 or temp > 40:
            base -= 15

        # Soil moisture affects metabolism
        moisture = data.get("soil_moisture", 40)
        if 30 <= moisture <= 60:
            base += 3  # Optimal
        elif moisture < 15 or moisture > 85:
            base -= 10

        return max(10, base)

    def _calculate_flowering(self, data: dict) -> float:
        flowering = 1.0

        # Floral VOCs indicate flowering
        linalool = data.get("linalool", 0)
        geraniol = data.get("geraniol", 0)

        flowering += linalool * 0.05 + geraniol * 0.04

        return min(100, flowering)

    def _calculate_confidence(self, data: dict) -> float:
        """Confidence based on data completeness."""
        total_fields = len(VOC_COMPOUNDS) + len(SOIL_FEATURES) + len(CLIMATE_FEATURES)
        present = sum(1 for k in data if data[k] is not None and data[k] != 0)
        return round(min(0.95, 0.3 + (present / total_fields) * 0.65), 2)

    def _generate_alerts(self, data: dict) -> list:
        alerts = []

        for compound, thresholds in self.thresholds.items():
            value = data.get(compound, 0)
            if value > thresholds["high"]:
                alerts.append({
                    "level": "danger",
                    "compound": compound,
                    "value": value,
                    "threshold": thresholds["high"],
                    "message": f"{compound} critically high: {value} ppb",
                })
            elif value > thresholds["elevated"]:
                alerts.append({
                    "level": "warning",
                    "compound": compound,
                    "value": value,
                    "threshold": thresholds["elevated"],
                    "message": f"{compound} elevated: {value} ppb",
                })

        return alerts

    def create_feature_vector(self, data: dict) -> np.ndarray:
        """
        Create ML-ready feature vector from sensor data.
        Size: len(VOC_COMPOUNDS) + len(SOIL) + len(CLIMATE) + 64 (AlphaEarth)
        """
        vector = []

        # VOC features
        for compound in VOC_COMPOUNDS:
            vector.append(float(data.get(compound, 0)))

        # Soil features
        for feature in SOIL_FEATURES:
            vector.append(float(data.get(feature, 0)))

        # Climate features
        for feature in CLIMATE_FEATURES:
            vector.append(float(data.get(feature, 0)))

        # AlphaEarth embedding (placeholder zeros if not available)
        ae_embedding = data.get("alpha_earth_embedding", [0] * 64)
        vector.extend(ae_embedding[:64])

        return np.array(vector, dtype=np.float32)


# ================================
# Usage example
# ================================
if __name__ == "__main__":
    model = PlantMetabolismModel()

    # Simulated sensor reading
    sample_data = {
        "parcel_id": "P1",
        "sensor_id": "VOC_NODE_1",
        "timestamp": datetime.now().isoformat(),
        "tvoc": 280,
        "CO2": 420,
        "NH3": 60,
        "CH4": 120,
        "C2H5OH": 150,
        "H2": 80,
        "HCHO": 45,
        "temperature": 21.2,
        "humidity": 61,
        "soil_moisture": 38,
        "ph": 6.5,
    }

    # Predict
    result = model.predict(sample_data)
    print(json.dumps(result, indent=2))

    # Feature vector for ML training
    vector = model.create_feature_vector(sample_data)
    print(f"\nFeature vector dimension: {len(vector)}")
    print(f"Non-zero features: {np.count_nonzero(vector)}")

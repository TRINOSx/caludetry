#!/usr/bin/env python3
"""
Train a plant state prediction model for the VOC Mesh Platform.

Replaces the rule-based PlantMetabolismModel (ml/plant_model.py) with a
trained neural network that predicts:
  - stress (0-100)
  - plague_risk (0-100)
  - metabolism (0-100)
  - flowering (0-100)

Uses synthetic data generated to match the rule-based model's behavior,
then fine-tunes on real sensor data when available.

Usage:
    python train_plant_state.py --samples 10000 --epochs 80
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "ml"))
from config import MODELS_DIR, TRAINING_DEFAULTS


class PlantStateNet(nn.Module):
    """
    Multi-output regression network for plant state prediction.
    Input: VOC + soil + climate features
    Output: [stress, plague_risk, metabolism, flowering] each 0-100
    """

    def __init__(self, input_dim: int):
        super().__init__()
        self.shared = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
        )
        # Separate heads for each prediction target
        self.stress_head = nn.Sequential(nn.Linear(64, 16), nn.ReLU(), nn.Linear(16, 1), nn.Sigmoid())
        self.plague_head = nn.Sequential(nn.Linear(64, 16), nn.ReLU(), nn.Linear(16, 1), nn.Sigmoid())
        self.metabolism_head = nn.Sequential(nn.Linear(64, 16), nn.ReLU(), nn.Linear(16, 1), nn.Sigmoid())
        self.flowering_head = nn.Sequential(nn.Linear(64, 16), nn.ReLU(), nn.Linear(16, 1), nn.Sigmoid())

    def forward(self, x):
        shared = self.shared(x)
        stress = self.stress_head(shared) * 100
        plague = self.plague_head(shared) * 100
        metabolism = self.metabolism_head(shared) * 100
        flowering = self.flowering_head(shared) * 100
        return torch.cat([stress, plague, metabolism, flowering], dim=1)


def generate_training_data(n_samples: int = 10000, seed: int = 42):
    """
    Generate training data using the existing rule-based model as a teacher.
    This is a knowledge distillation approach: the neural network learns
    to replicate the rule-based model, then can be fine-tuned on real data.
    """
    from plant_model import PlantMetabolismModel

    rng = np.random.default_rng(seed)
    model = PlantMetabolismModel()

    features_list = []
    targets_list = []

    feature_names = [
        "tvoc", "CO2", "NH3", "CH4", "C2H5OH", "H2", "HCHO",
        "C2H4", "H2S", "CO", "NO2", "O3",
        "linalool", "geraniol", "methyl_salicylate", "methyl_jasmonate",
        "cis_3_hexenal", "beta_caryophyllene", "DMNT", "TMTT",
        "farnesene", "ocimene",
        "temperature", "humidity", "soil_moisture", "ph",
    ]

    for _ in range(n_samples):
        data = {
            "tvoc": rng.exponential(300),
            "CO2": rng.uniform(400, 2000),
            "NH3": rng.exponential(150),
            "CH4": rng.exponential(200),
            "C2H5OH": rng.exponential(200),
            "H2": rng.exponential(80),
            "HCHO": rng.exponential(60),
            "C2H4": rng.exponential(100),
            "H2S": rng.exponential(50),
            "CO": rng.exponential(200),
            "NO2": rng.exponential(30),
            "O3": rng.exponential(20),
            # Defense VOCs
            "linalool": rng.exponential(10),
            "geraniol": rng.exponential(8),
            "methyl_salicylate": rng.exponential(15),
            "methyl_jasmonate": rng.exponential(12),
            "cis_3_hexenal": rng.exponential(20),
            "beta_caryophyllene": rng.exponential(10),
            "DMNT": rng.exponential(8),
            "TMTT": rng.exponential(5),
            "farnesene": rng.exponential(10),
            "ocimene": rng.exponential(8),
            # Environment
            "temperature": rng.uniform(5, 45),
            "humidity": rng.uniform(20, 95),
            "soil_moisture": rng.uniform(10, 90),
            "ph": rng.uniform(4.5, 8.5),
        }

        result = model.predict(data)
        features_list.append([data.get(f, 0) for f in feature_names])
        targets_list.append([
            result["stress"],
            result["plagues"],
            result["metabolism"],
            result["flowering"],
        ])

    import pandas as pd
    features = pd.DataFrame(features_list, columns=feature_names)
    targets = np.array(targets_list, dtype=np.float32)

    return features, targets


def main():
    parser = argparse.ArgumentParser(description="Train plant state predictor")
    parser.add_argument("--samples", type=int, default=10000)
    parser.add_argument("--epochs", type=int, default=TRAINING_DEFAULTS["epochs"])
    parser.add_argument("--batch-size", type=int, default=TRAINING_DEFAULTS["batch_size"])
    parser.add_argument("--lr", type=float, default=TRAINING_DEFAULTS["learning_rate"])
    parser.add_argument("--export-onnx", action="store_true")
    args = parser.parse_args()

    print(f"Generating {args.samples} samples from rule-based teacher model...")
    features, targets = generate_training_data(args.samples)

    print(f"Features: {features.shape}, Targets: {targets.shape}")
    print(f"Target stats (mean): stress={targets[:,0].mean():.1f}, "
          f"plague={targets[:,1].mean():.1f}, "
          f"metabolism={targets[:,2].mean():.1f}, "
          f"flowering={targets[:,3].mean():.1f}")

    # Normalize features
    from preprocess import normalize_features
    features_norm, scaler = normalize_features(features)

    # Split
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        features_norm.values, targets, test_size=0.2, random_state=42,
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train, test_size=0.15, random_state=42,
    )

    train_loader = DataLoader(
        TensorDataset(torch.FloatTensor(X_train), torch.FloatTensor(y_train)),
        batch_size=args.batch_size, shuffle=True,
    )
    val_loader = DataLoader(
        TensorDataset(torch.FloatTensor(X_val), torch.FloatTensor(y_val)),
        batch_size=args.batch_size,
    )
    test_loader = DataLoader(
        TensorDataset(torch.FloatTensor(X_test), torch.FloatTensor(y_test)),
        batch_size=args.batch_size,
    )

    model = PlantStateNet(X_train.shape[1])
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr, weight_decay=1e-4)
    criterion = nn.MSELoss()

    print(f"\nPlantStateNet params: {sum(p.numel() for p in model.parameters()):,}")
    print("Training...\n")

    best_val = float("inf")
    best_state = None
    wait = 0

    for epoch in range(args.epochs):
        model.train()
        t_loss = 0
        for X, y in train_loader:
            optimizer.zero_grad()
            loss = criterion(model(X), y)
            loss.backward()
            optimizer.step()
            t_loss += loss.item()
        t_loss /= len(train_loader)

        model.eval()
        v_loss = 0
        with torch.no_grad():
            for X, y in val_loader:
                v_loss += criterion(model(X), y).item()
        v_loss /= len(val_loader)

        if (epoch + 1) % 10 == 0 or epoch == 0:
            print(f"Epoch {epoch+1:3d}/{args.epochs} | Train MSE: {t_loss:.4f} | Val MSE: {v_loss:.4f}")

        if v_loss < best_val:
            best_val = v_loss
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            wait = 0
        else:
            wait += 1
            if wait >= TRAINING_DEFAULTS["early_stopping_patience"]:
                print(f"Early stopping at epoch {epoch+1}")
                break

    if best_state:
        model.load_state_dict(best_state)

    # Evaluate
    model.eval()
    all_preds, all_targets = [], []
    with torch.no_grad():
        for X, y in test_loader:
            all_preds.append(model(X).numpy())
            all_targets.append(y.numpy())

    preds = np.vstack(all_preds)
    targets_test = np.vstack(all_targets)

    names = ["stress", "plague_risk", "metabolism", "flowering"]
    print("\n=== Test Results ===")
    for i, name in enumerate(names):
        mae = np.mean(np.abs(preds[:, i] - targets_test[:, i]))
        rmse = np.sqrt(np.mean((preds[:, i] - targets_test[:, i]) ** 2))
        print(f"  {name:15s} | MAE: {mae:6.2f} | RMSE: {rmse:6.2f}")

    # Save
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    save_path = MODELS_DIR / "plant_state_net.pt"
    torch.save({
        "model_state": model.state_dict(),
        "input_dim": X_train.shape[1],
        "feature_names": list(features.columns),
        "target_names": names,
    }, save_path)
    print(f"\nModel saved: {save_path}")

    if args.export_onnx:
        onnx_path = MODELS_DIR / "plant_state_net.onnx"
        model.eval()
        dummy = torch.randn(1, X_train.shape[1])
        torch.onnx.export(
            model, dummy, str(onnx_path),
            input_names=["sensor_features"],
            output_names=["plant_state"],
            dynamic_axes={"sensor_features": {0: "batch"}, "plant_state": {0: "batch"}},
            opset_version=17,
        )
        print(f"ONNX exported: {onnx_path}")


if __name__ == "__main__":
    main()

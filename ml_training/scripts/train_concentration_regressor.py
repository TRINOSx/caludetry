#!/usr/bin/env python3
"""
Train a concentration regression model for VOC sensors.

Predicts gas concentrations (PPM/PPB) from raw sensor array readings.
This is the core model for converting MOx sensor responses to calibrated values.

Usage:
    python train_concentration_regressor.py --mode synthetic --epochs 80
    python train_concentration_regressor.py --mode uci
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import MODELS_DIR, TRAINING_DEFAULTS


class ConcentrationRegressor(nn.Module):
    """
    Multi-output regressor: sensor features → gas concentrations.
    Predicts simultaneous concentrations for multiple compounds.
    """

    def __init__(self, input_dim: int, output_dim: int):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, output_dim),
        )

    def forward(self, x):
        return self.network(x)


def generate_regression_data(n_samples: int = 5000, seed: int = 42):
    """
    Generate synthetic sensor→concentration data.
    Simulates how raw MOx sensor readings relate to actual gas concentrations
    with realistic noise, cross-sensitivity, and nonlinearity.
    """
    rng = np.random.default_rng(seed)

    # True concentrations (what we want to predict)
    target_gases = ["C2H5OH", "NH3", "CH4", "CO", "H2", "TVOC"]
    concentrations = np.column_stack([
        rng.exponential(200, n_samples),   # Ethanol ppb
        rng.exponential(150, n_samples),   # NH3 ppb
        rng.exponential(300, n_samples),   # CH4 ppb
        rng.exponential(250, n_samples),   # CO ppb
        rng.exponential(100, n_samples),   # H2 ppb
        rng.exponential(400, n_samples),   # TVOC ppb
    ])

    # Simulate 16 MOx sensor responses with cross-sensitivity
    n_sensors = 16
    # Random sensitivity matrix (each sensor responds differently to each gas)
    sensitivity = rng.uniform(0.1, 2.0, (len(target_gases), n_sensors))

    # Sensor response = sum of (concentration × sensitivity) + noise
    # With log-like nonlinearity (typical of MOx sensors)
    raw_responses = np.log1p(concentrations @ sensitivity)

    # Add sensor noise (±5%)
    noise = rng.normal(0, 0.05, raw_responses.shape)
    raw_responses += noise * raw_responses

    # Add temperature and humidity as features
    temperature = rng.uniform(5, 45, (n_samples, 1))
    humidity = rng.uniform(20, 95, (n_samples, 1))
    features = np.hstack([raw_responses, temperature, humidity])

    import pandas as pd
    feature_cols = [f"sensor_{i}" for i in range(n_sensors)] + ["temperature", "humidity"]
    features_df = pd.DataFrame(features, columns=feature_cols)
    targets_df = pd.DataFrame(concentrations, columns=target_gases)

    return features_df, targets_df


def train_regressor(
    model, train_loader, val_loader, epochs, lr, patience, device="cpu"
):
    model = model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5, factor=0.5)
    criterion = nn.MSELoss()

    best_val_loss = float("inf")
    best_state = None
    wait = 0

    for epoch in range(epochs):
        model.train()
        train_loss = 0
        for X_batch, y_batch in train_loader:
            X_batch, y_batch = X_batch.to(device), y_batch.to(device)
            optimizer.zero_grad()
            out = model(X_batch)
            loss = criterion(out, y_batch)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
        train_loss /= len(train_loader)

        model.eval()
        val_loss = 0
        with torch.no_grad():
            for X_batch, y_batch in val_loader:
                X_batch, y_batch = X_batch.to(device), y_batch.to(device)
                val_loss += criterion(model(X_batch), y_batch).item()
        val_loss /= len(val_loader)
        scheduler.step(val_loss)

        if (epoch + 1) % 10 == 0 or epoch == 0:
            print(f"Epoch {epoch+1:3d}/{epochs} | Train MSE: {train_loss:.4f} | Val MSE: {val_loss:.4f}")

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            wait = 0
        else:
            wait += 1
            if wait >= patience:
                print(f"Early stopping at epoch {epoch+1}")
                break

    if best_state:
        model.load_state_dict(best_state)


def evaluate_regressor(model, test_loader, target_names, device="cpu"):
    model.eval()
    all_preds = []
    all_targets = []

    with torch.no_grad():
        for X_batch, y_batch in test_loader:
            preds = model(X_batch.to(device)).cpu().numpy()
            all_preds.append(preds)
            all_targets.append(y_batch.numpy())

    preds = np.vstack(all_preds)
    targets = np.vstack(all_targets)

    print("\n=== Regression Results ===")
    for i, name in enumerate(target_names):
        mae = np.mean(np.abs(preds[:, i] - targets[:, i]))
        rmse = np.sqrt(np.mean((preds[:, i] - targets[:, i]) ** 2))
        r2 = 1 - np.sum((targets[:, i] - preds[:, i]) ** 2) / np.sum((targets[:, i] - targets[:, i].mean()) ** 2)
        print(f"  {name:10s} | MAE: {mae:8.2f} | RMSE: {rmse:8.2f} | R²: {r2:.4f}")


def main():
    parser = argparse.ArgumentParser(description="Train VOC concentration regressor")
    parser.add_argument("--mode", choices=["uci", "synthetic"], default="synthetic")
    parser.add_argument("--epochs", type=int, default=TRAINING_DEFAULTS["epochs"])
    parser.add_argument("--batch-size", type=int, default=TRAINING_DEFAULTS["batch_size"])
    parser.add_argument("--lr", type=float, default=TRAINING_DEFAULTS["learning_rate"])
    parser.add_argument("--export-onnx", action="store_true")
    args = parser.parse_args()

    from preprocess import normalize_features

    if args.mode == "uci":
        from data_loader import load_uci_gas_dynamic
        print("Loading UCI Dynamic Gas Mixtures...")
        features, targets = load_uci_gas_dynamic()
        target_names = list(targets.columns)
    else:
        print("Generating synthetic regression data...")
        features, targets = generate_regression_data(5000)
        target_names = list(targets.columns)

    print(f"Features: {features.shape}, Targets: {targets.shape}")

    # Normalize features
    features_norm, scaler = normalize_features(features)

    # Split
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        features_norm.values, targets.values,
        test_size=0.2, random_state=42,
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train, test_size=0.15, random_state=42,
    )

    train_ds = TensorDataset(torch.FloatTensor(X_train), torch.FloatTensor(y_train))
    val_ds = TensorDataset(torch.FloatTensor(X_val), torch.FloatTensor(y_val))
    test_ds = TensorDataset(torch.FloatTensor(X_test), torch.FloatTensor(y_test))

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size)
    test_loader = DataLoader(test_ds, batch_size=args.batch_size)

    model = ConcentrationRegressor(X_train.shape[1], y_train.shape[1])
    print(f"Model params: {sum(p.numel() for p in model.parameters()):,}")

    train_regressor(
        model, train_loader, val_loader,
        epochs=args.epochs, lr=args.lr,
        patience=TRAINING_DEFAULTS["early_stopping_patience"],
    )

    evaluate_regressor(model, test_loader, target_names)

    # Save
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    save_path = MODELS_DIR / f"voc_regressor_{args.mode}.pt"
    torch.save({
        "model_state": model.state_dict(),
        "target_names": target_names,
        "input_dim": X_train.shape[1],
        "output_dim": y_train.shape[1],
    }, save_path)
    print(f"\nModel saved: {save_path}")

    if args.export_onnx:
        onnx_path = MODELS_DIR / f"voc_regressor_{args.mode}.onnx"
        model.eval()
        dummy = torch.randn(1, X_train.shape[1])
        torch.onnx.export(
            model, dummy, str(onnx_path),
            input_names=["sensor_features"],
            output_names=["concentrations"],
            dynamic_axes={"sensor_features": {0: "batch"}, "concentrations": {0: "batch"}},
            opset_version=17,
        )
        print(f"ONNX exported: {onnx_path}")


if __name__ == "__main__":
    main()

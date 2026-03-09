"""
Phase 3 — Model Trainer

Trains the final ML models using the enriched feature matrix.

Models trained:
  1. PlantStateClassifier — multi-class: healthy/mild_stress/severe_stress/pest/flowering
  2. StressRegressor — continuous stress percentage (0-100)
  3. SoilEventDetector — binary: normal/soil_gas_event
  4. AirQualityClassifier — 3-class: good/moderate/poor

Architecture: PyTorch multi-head neural network
  Shared backbone → 4 task-specific heads
  Exports to ONNX for edge inference on ESP32 companion board.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import RobustScaler
from torch.utils.data import DataLoader, TensorDataset

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import ProjectConfig


# ─────────────────────────────────────────────────────────────
# Neural Network Architecture
# ─────────────────────────────────────────────────────────────

class VOCMultiHead(nn.Module):
    """
    Multi-head neural network for VOC sensor prediction.

    Shared backbone extracts common features from 26 sensor channels + enrichment.
    4 task-specific heads produce different outputs.
    """

    def __init__(self, input_dim: int, hidden_dim: int = 128, dropout: float = 0.3):
        super().__init__()

        # Shared backbone
        self.backbone = nn.Sequential(
            nn.Linear(input_dim, hidden_dim * 2),
            nn.BatchNorm1d(hidden_dim * 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
        )

        # Head 1: Plant state classification (5 classes)
        self.head_plant_state = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 5),
        )

        # Head 2: Stress regression (0-100)
        self.head_stress = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Sigmoid(),  # Output 0-1, scale to 0-100
        )

        # Head 3: Soil event detection (binary)
        self.head_soil = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
        )

        # Head 4: Air quality (3 classes)
        self.head_air = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 3),
        )

    def forward(self, x):
        features = self.backbone(x)
        return {
            "plant_state": self.head_plant_state(features),
            "stress_pct": self.head_stress(features).squeeze(-1) * 100,
            "soil_event": self.head_soil(features).squeeze(-1),
            "air_quality": self.head_air(features),
        }


# ─────────────────────────────────────────────────────────────
# Training Loop
# ─────────────────────────────────────────────────────────────

def prepare_data(features_path: Path, config: ProjectConfig) -> dict:
    """Load feature matrix and split into train/val/test."""
    df = pd.read_csv(features_path)
    print(f"[train] Loaded {df.shape[0]} samples, {df.shape[1]} columns")

    # Separate features and labels
    label_cols = [c for c in df.columns if c.startswith("label_")]
    feature_cols = [c for c in df.columns if not c.startswith("label_")]

    X = df[feature_cols].values.astype(np.float32)
    y_plant = df["label_plant_state"].values.astype(np.int64) if "label_plant_state" in df.columns else np.zeros(len(df), dtype=np.int64)
    y_stress = df["label_stress_pct"].values.astype(np.float32) if "label_stress_pct" in df.columns else np.zeros(len(df), dtype=np.float32)
    y_soil = df["label_soil_event"].values.astype(np.float32) if "label_soil_event" in df.columns else np.zeros(len(df), dtype=np.float32)
    y_air = df["label_air_quality"].values.astype(np.int64) if "label_air_quality" in df.columns else np.zeros(len(df), dtype=np.int64)

    # Normalize features
    scaler = RobustScaler()
    X = scaler.fit_transform(X)

    # Split
    indices = np.arange(len(X))
    train_idx, test_idx = train_test_split(indices, test_size=config.test_split, random_state=config.random_seed)
    train_idx, val_idx = train_test_split(train_idx, test_size=config.val_split / (1 - config.test_split), random_state=config.random_seed)

    def make_dataset(idx):
        return TensorDataset(
            torch.from_numpy(X[idx]),
            torch.from_numpy(y_plant[idx]),
            torch.from_numpy(y_stress[idx]),
            torch.from_numpy(y_soil[idx]),
            torch.from_numpy(y_air[idx]),
        )

    return {
        "train": DataLoader(make_dataset(train_idx), batch_size=config.batch_size_training, shuffle=True),
        "val": DataLoader(make_dataset(val_idx), batch_size=config.batch_size_training),
        "test": DataLoader(make_dataset(test_idx), batch_size=config.batch_size_training),
        "input_dim": X.shape[1],
        "scaler": scaler,
        "feature_cols": feature_cols,
        "n_train": len(train_idx),
        "n_val": len(val_idx),
        "n_test": len(test_idx),
    }


def train_model(data: dict, config: ProjectConfig) -> tuple[VOCMultiHead, dict]:
    """Train the multi-head model."""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[train] Device: {device}")

    model = VOCMultiHead(input_dim=data["input_dim"]).to(device)

    # Loss functions
    ce_plant = nn.CrossEntropyLoss()
    mse_stress = nn.MSELoss()
    bce_soil = nn.BCEWithLogitsLoss()
    ce_air = nn.CrossEntropyLoss()

    optimizer = torch.optim.AdamW(model.parameters(), lr=config.learning_rate, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5, factor=0.5)

    best_val_loss = float("inf")
    patience_counter = 0
    history = {"train_loss": [], "val_loss": []}

    print(f"[train] Training: {data['n_train']} train, {data['n_val']} val, {data['n_test']} test")
    print(f"[train] Input dim: {data['input_dim']}, Epochs: {config.epochs}")

    for epoch in range(config.epochs):
        # Train
        model.train()
        train_loss = 0
        for batch_x, batch_plant, batch_stress, batch_soil, batch_air in data["train"]:
            batch_x = batch_x.to(device)
            batch_plant = batch_plant.to(device)
            batch_stress = batch_stress.to(device)
            batch_soil = batch_soil.to(device)
            batch_air = batch_air.to(device)

            optimizer.zero_grad()
            out = model(batch_x)

            loss = (
                ce_plant(out["plant_state"], batch_plant)
                + 0.01 * mse_stress(out["stress_pct"], batch_stress)
                + bce_soil(out["soil_event"], batch_soil)
                + ce_air(out["air_quality"], batch_air)
            )

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            train_loss += loss.item()

        train_loss /= len(data["train"])

        # Validate
        model.eval()
        val_loss = 0
        with torch.no_grad():
            for batch_x, batch_plant, batch_stress, batch_soil, batch_air in data["val"]:
                batch_x = batch_x.to(device)
                out = model(batch_x)
                loss = (
                    ce_plant(out["plant_state"], batch_plant.to(device))
                    + 0.01 * mse_stress(out["stress_pct"], batch_stress.to(device))
                    + bce_soil(out["soil_event"], batch_soil.to(device))
                    + ce_air(out["air_quality"], batch_air.to(device))
                )
                val_loss += loss.item()

        val_loss /= len(data["val"])
        scheduler.step(val_loss)

        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)

        if (epoch + 1) % 10 == 0 or epoch == 0:
            lr = optimizer.param_groups[0]["lr"]
            print(f"  Epoch {epoch+1:3d}/{config.epochs}: train={train_loss:.4f} val={val_loss:.4f} lr={lr:.2e}")

        # Early stopping
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
        else:
            patience_counter += 1
            if patience_counter >= 10:
                print(f"  Early stopping at epoch {epoch+1}")
                break

    # Restore best weights
    model.load_state_dict(best_state)
    return model, history


def evaluate_model(model: VOCMultiHead, data: dict) -> dict:
    """Evaluate model on test set."""
    device = next(model.parameters()).device
    model.eval()

    all_plant_pred, all_plant_true = [], []
    all_stress_pred, all_stress_true = [], []
    all_air_pred, all_air_true = [], []

    with torch.no_grad():
        for batch_x, batch_plant, batch_stress, batch_soil, batch_air in data["test"]:
            out = model(batch_x.to(device))

            all_plant_pred.extend(out["plant_state"].argmax(dim=1).cpu().numpy())
            all_plant_true.extend(batch_plant.numpy())

            all_stress_pred.extend(out["stress_pct"].cpu().numpy())
            all_stress_true.extend(batch_stress.numpy())

            all_air_pred.extend(out["air_quality"].argmax(dim=1).cpu().numpy())
            all_air_true.extend(batch_air.numpy())

    plant_pred = np.array(all_plant_pred)
    plant_true = np.array(all_plant_true)
    stress_pred = np.array(all_stress_pred)
    stress_true = np.array(all_stress_true)

    plant_acc = (plant_pred == plant_true).mean()
    stress_mae = np.abs(stress_pred - stress_true).mean()
    air_acc = (np.array(all_air_pred) == np.array(all_air_true)).mean()

    metrics = {
        "plant_state_accuracy": round(float(plant_acc), 4),
        "stress_mae": round(float(stress_mae), 2),
        "air_quality_accuracy": round(float(air_acc), 4),
        "n_test_samples": len(plant_true),
    }

    print(f"\n[eval] Test Results:")
    print(f"  Plant State Accuracy:  {plant_acc:.2%}")
    print(f"  Stress MAE:            {stress_mae:.2f}%")
    print(f"  Air Quality Accuracy:  {air_acc:.2%}")

    return metrics


def export_onnx(model: VOCMultiHead, input_dim: int, out_path: Path):
    """Export model to ONNX for edge deployment."""
    model.eval()
    model.cpu()
    dummy = torch.randn(1, input_dim)

    torch.onnx.export(
        model, dummy, str(out_path),
        input_names=["sensor_input"],
        output_names=["plant_state", "stress_pct", "soil_event", "air_quality"],
        dynamic_axes={"sensor_input": {0: "batch"}},
        opset_version=13,
    )
    print(f"[export] ONNX model → {out_path}")


def run_training(config: ProjectConfig) -> dict:
    """
    Execute Phase 3 training pipeline.

    Returns dict with model path, metrics, and history.
    """
    print("=" * 60)
    print("PHASE 3b: Model Training")
    print("=" * 60)

    features_path = config.enriched_dir / f"training_features_{config.project_id}.csv"
    if not features_path.exists():
        raise FileNotFoundError(f"Run feature builder first. Missing: {features_path}")

    # Prepare data
    print("[train] Preparing data...")
    data = prepare_data(features_path, config)

    # Train
    print("\n[train] Training multi-head model...")
    model, history = train_model(data, config)

    # Evaluate
    metrics = evaluate_model(model, data)

    # Save
    config.ensure_dirs()
    model_path = config.models_dir / f"voc_model_{config.project_id}.pt"
    torch.save({
        "model_state": model.state_dict(),
        "input_dim": data["input_dim"],
        "feature_cols": data["feature_cols"],
        "metrics": metrics,
        "config": {
            "seed_name": config.seed_name,
            "location": config.location_name,
            "project_id": config.project_id,
        },
    }, model_path)
    print(f"\n[train] Model saved → {model_path}")

    # Export ONNX
    onnx_path = config.models_dir / f"voc_model_{config.project_id}.onnx"
    try:
        export_onnx(model, data["input_dim"], onnx_path)
    except Exception as e:
        print(f"[export] ONNX export failed (non-critical): {e}")

    # Save training report
    report = {
        "project_id": config.project_id,
        "seed": config.seed_name,
        "location": config.location_name,
        "input_dim": data["input_dim"],
        "n_train": data["n_train"],
        "n_val": data["n_val"],
        "n_test": data["n_test"],
        "metrics": metrics,
        "epochs_trained": len(history["train_loss"]),
        "final_train_loss": history["train_loss"][-1] if history["train_loss"] else None,
        "final_val_loss": history["val_loss"][-1] if history["val_loss"] else None,
    }

    report_path = config.models_dir / f"training_report_{config.project_id}.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"[train] Report → {report_path}")

    return report

#!/usr/bin/env python3
"""
Train a gas classification model on VOC sensor array data.

Supports two modes:
  1. UCI dataset mode: Train on public UCI Gas Sensor Array Drift data
  2. Synthetic mode: Train on generated data matching platform sensors

Outputs an ONNX model compatible with the VOC Mesh Platform inference pipeline.

Usage:
    python train_gas_classifier.py --mode synthetic --epochs 50
    python train_gas_classifier.py --mode uci --epochs 100
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import classification_report, confusion_matrix
from torch.utils.data import DataLoader, TensorDataset

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import MODELS_DIR, TRAINING_DEFAULTS


class VOCClassifier(nn.Module):
    """
    Multi-layer classifier for gas/VOC identification from sensor arrays.
    Architecture sized for 16-sensor arrays (128 features) or platform sensors (~20 features).
    """

    def __init__(self, input_dim: int, n_classes: int, hidden_dims: list[int] = None):
        super().__init__()
        if hidden_dims is None:
            hidden_dims = [128, 64, 32]

        layers = []
        prev_dim = input_dim
        for h_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, h_dim),
                nn.BatchNorm1d(h_dim),
                nn.ReLU(),
                nn.Dropout(0.3),
            ])
            prev_dim = h_dim

        layers.append(nn.Linear(prev_dim, n_classes))
        self.network = nn.Sequential(*layers)

    def forward(self, x):
        return self.network(x)


class VOCConvClassifier(nn.Module):
    """
    1D-CNN classifier that treats sensor array readings as a 1D signal.
    Better at capturing inter-sensor correlation patterns.
    """

    def __init__(self, input_dim: int, n_classes: int):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv1d(1, 32, kernel_size=3, padding=1),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.Conv1d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(8),
        )
        self.fc = nn.Sequential(
            nn.Linear(64 * 8, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, n_classes),
        )

    def forward(self, x):
        x = x.unsqueeze(1)  # (batch, 1, features)
        x = self.conv(x)
        x = x.view(x.size(0), -1)
        return self.fc(x)


def train_model(
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    epochs: int,
    lr: float,
    patience: int,
    device: str = "cpu",
) -> dict:
    model = model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5, factor=0.5)
    criterion = nn.CrossEntropyLoss()

    best_val_loss = float("inf")
    best_state = None
    wait = 0
    history = {"train_loss": [], "val_loss": [], "val_acc": []}

    for epoch in range(epochs):
        # Train
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

        # Validate
        model.eval()
        val_loss = 0
        correct = 0
        total = 0
        with torch.no_grad():
            for X_batch, y_batch in val_loader:
                X_batch, y_batch = X_batch.to(device), y_batch.to(device)
                out = model(X_batch)
                val_loss += criterion(out, y_batch).item()
                pred = out.argmax(dim=1)
                correct += (pred == y_batch).sum().item()
                total += len(y_batch)

        val_loss /= len(val_loader)
        val_acc = correct / total
        scheduler.step(val_loss)

        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_acc)

        if (epoch + 1) % 10 == 0 or epoch == 0:
            print(f"Epoch {epoch+1:3d}/{epochs} | "
                  f"Train Loss: {train_loss:.4f} | "
                  f"Val Loss: {val_loss:.4f} | "
                  f"Val Acc: {val_acc:.4f}")

        # Early stopping
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

    return history


def evaluate_model(model, test_loader, class_names, device="cpu"):
    model.eval()
    all_preds = []
    all_labels = []

    with torch.no_grad():
        for X_batch, y_batch in test_loader:
            X_batch = X_batch.to(device)
            preds = model(X_batch).argmax(dim=1).cpu().numpy()
            all_preds.extend(preds)
            all_labels.extend(y_batch.numpy())

    print("\n=== Classification Report ===")
    print(classification_report(all_labels, all_preds, target_names=class_names))

    cm = confusion_matrix(all_labels, all_preds)
    print("Confusion Matrix:")
    print(cm)

    return np.array(all_preds), np.array(all_labels)


def export_onnx(model, input_dim, save_path):
    model.eval()
    dummy = torch.randn(1, input_dim)
    torch.onnx.export(
        model, dummy, str(save_path),
        input_names=["sensor_features"],
        output_names=["gas_class_logits"],
        dynamic_axes={"sensor_features": {0: "batch"}, "gas_class_logits": {0: "batch"}},
        opset_version=17,
    )
    print(f"ONNX model exported: {save_path}")


def main():
    parser = argparse.ArgumentParser(description="Train VOC gas classifier")
    parser.add_argument("--mode", choices=["uci", "synthetic"], default="synthetic")
    parser.add_argument("--arch", choices=["mlp", "cnn"], default="mlp")
    parser.add_argument("--epochs", type=int, default=TRAINING_DEFAULTS["epochs"])
    parser.add_argument("--batch-size", type=int, default=TRAINING_DEFAULTS["batch_size"])
    parser.add_argument("--lr", type=float, default=TRAINING_DEFAULTS["learning_rate"])
    parser.add_argument("--export-onnx", action="store_true", help="Export to ONNX format")
    args = parser.parse_args()

    from data_loader import load_uci_gas_drift, generate_synthetic_voc_data
    from preprocess import preprocess_pipeline

    # Load data
    if args.mode == "uci":
        print("Loading UCI Gas Sensor Array Drift Dataset...")
        features, labels, class_names = load_uci_gas_drift()
    else:
        print("Generating synthetic VOC sensor data...")
        features, labels, class_names = generate_synthetic_voc_data(5000)

    print(f"Dataset: {features.shape[0]} samples, {features.shape[1]} features")
    print(f"Classes: {class_names}")

    # Preprocess
    splits, scaler = preprocess_pipeline(features, labels)

    # Create data loaders
    train_ds = TensorDataset(
        torch.FloatTensor(splits["X_train"].values),
        torch.LongTensor(splits["y_train"]),
    )
    val_ds = TensorDataset(
        torch.FloatTensor(splits["X_val"].values),
        torch.LongTensor(splits["y_val"]),
    )
    test_ds = TensorDataset(
        torch.FloatTensor(splits["X_test"].values),
        torch.LongTensor(splits["y_test"]),
    )

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size)
    test_loader = DataLoader(test_ds, batch_size=args.batch_size)

    input_dim = splits["X_train"].shape[1]
    n_classes = len(class_names)

    # Build model
    if args.arch == "cnn":
        model = VOCConvClassifier(input_dim, n_classes)
    else:
        model = VOCClassifier(input_dim, n_classes)

    print(f"\nModel: {args.arch.upper()} | Params: {sum(p.numel() for p in model.parameters()):,}")

    # Train
    history = train_model(
        model, train_loader, val_loader,
        epochs=args.epochs, lr=args.lr,
        patience=TRAINING_DEFAULTS["early_stopping_patience"],
    )

    # Evaluate
    evaluate_model(model, test_loader, class_names)

    # Save
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    model_path = MODELS_DIR / f"voc_classifier_{args.mode}_{args.arch}.pt"
    torch.save({
        "model_state": model.state_dict(),
        "class_names": class_names,
        "input_dim": input_dim,
        "arch": args.arch,
        "history": history,
    }, model_path)
    print(f"\nModel saved: {model_path}")

    # ONNX export
    if args.export_onnx:
        onnx_path = MODELS_DIR / f"voc_classifier_{args.mode}_{args.arch}.onnx"
        export_onnx(model, input_dim, onnx_path)


if __name__ == "__main__":
    main()

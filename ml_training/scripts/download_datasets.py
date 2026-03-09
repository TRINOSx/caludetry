#!/usr/bin/env python3
"""
Download public VOC/gas sensor datasets for training.

Datasets:
  1. UCI Gas Sensor Array Drift (13,910 samples, 16 sensors, 6 gases)
  2. UCI Gas Sensor Dynamic Mixtures (Ethylene + Methane/CO)
  3. UCI Gas Sensor Low-Concentration (ppb-level, 10 sensors)

Usage:
    python download_datasets.py              # Download all
    python download_datasets.py --dataset uci_gas_drift   # Download one
"""
import argparse
import io
import os
import sys
import zipfile
from pathlib import Path

import requests
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DATASETS, DATASETS_DIR


def download_and_extract(name: str, info: dict, dest: Path) -> None:
    target_dir = dest / name
    if target_dir.exists() and any(target_dir.iterdir()):
        print(f"[skip] {name} already exists at {target_dir}")
        return

    target_dir.mkdir(parents=True, exist_ok=True)
    url = info["url"]
    print(f"[download] {name}: {url}")

    resp = requests.get(url, stream=True, timeout=120)
    resp.raise_for_status()

    total = int(resp.headers.get("content-length", 0))
    buf = io.BytesIO()
    with tqdm(total=total, unit="B", unit_scale=True, desc=name) as pbar:
        for chunk in resp.iter_content(chunk_size=8192):
            buf.write(chunk)
            pbar.update(len(chunk))

    buf.seek(0)
    if url.endswith(".zip"):
        with zipfile.ZipFile(buf) as zf:
            zf.extractall(target_dir)
        print(f"[extracted] {name} -> {target_dir}")
    else:
        out_file = target_dir / url.split("/")[-1]
        out_file.write_bytes(buf.read())
        print(f"[saved] {name} -> {out_file}")


def main():
    parser = argparse.ArgumentParser(description="Download VOC sensor datasets")
    parser.add_argument("--dataset", choices=list(DATASETS.keys()),
                        help="Download a specific dataset (default: all)")
    args = parser.parse_args()

    DATASETS_DIR.mkdir(parents=True, exist_ok=True)

    targets = {args.dataset: DATASETS[args.dataset]} if args.dataset else DATASETS
    for name, info in targets.items():
        try:
            download_and_extract(name, info, DATASETS_DIR)
        except Exception as e:
            print(f"[error] {name}: {e}")

    print("\nDone. Datasets saved to:", DATASETS_DIR)


if __name__ == "__main__":
    main()

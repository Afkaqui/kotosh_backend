"""Train a YOLOv8 object detector for cow detection."""

import argparse
import os
import shutil

import yaml
from ultralytics import YOLO


def load_config(config_path: str) -> dict:
    """Load training configuration from YAML file."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def train_detector(config_path: str) -> None:
    """Train the cow detector model using YOLOv8."""
    config = load_config(config_path)
    det_cfg = config["detector"]

    dataset_yaml = os.path.join(os.path.dirname(__file__), "..", "data", "dataset.yaml")
    dataset_yaml = os.path.abspath(dataset_yaml)

    if not os.path.isfile(dataset_yaml):
        print(f"Error: dataset config not found: {dataset_yaml}")
        return

    print("Loading model:", det_cfg["model"])
    model = YOLO(det_cfg["model"])

    print("Starting detector training...")
    print(f"  Epochs: {det_cfg['epochs']}")
    print(f"  Image size: {det_cfg['imgsz']}")
    print(f"  Batch size: {det_cfg['batch']}")
    print(f"  Learning rate: {det_cfg['lr0']}")
    print(f"  Patience: {det_cfg['patience']}")
    print(f"  Dataset: {dataset_yaml}")

    results = model.train(
        data=dataset_yaml,
        epochs=det_cfg["epochs"],
        imgsz=det_cfg["imgsz"],
        batch=det_cfg["batch"],
        lr0=det_cfg["lr0"],
        patience=det_cfg["patience"],
        project=os.path.join(os.path.dirname(__file__), "runs", "detect"),
        name="cow_detector",
        exist_ok=True,
    )

    models_dir = os.path.join(os.path.dirname(__file__), "..", "models")
    os.makedirs(models_dir, exist_ok=True)
    best_model = os.path.join(
        os.path.dirname(__file__), "runs", "detect", "cow_detector", "weights", "best.pt"
    )

    if os.path.isfile(best_model):
        dest = os.path.join(models_dir, "detector_best.pt")
        shutil.copy2(best_model, dest)
        print(f"Best model saved to {os.path.abspath(dest)}")
    else:
        print("Warning: best.pt not found in training output")

    print("Training complete.")
    if results and hasattr(results, "results_dict"):
        metrics = results.results_dict
        print(f"  mAP50: {metrics.get('metrics/mAP50(B)', 'N/A')}")
        print(f"  mAP50-95: {metrics.get('metrics/mAP50-95(B)', 'N/A')}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train YOLOv8 cow detector.")
    parser.add_argument(
        "--config",
        default=os.path.join(os.path.dirname(__file__), "config.yaml"),
        help="Path to training config YAML (default: training/config.yaml)",
    )
    args = parser.parse_args()

    train_detector(args.config)

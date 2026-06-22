"""Train a YOLOv8 classifier for cow behavior classification."""

import argparse
import os
import shutil

import yaml
from ultralytics import YOLO


def load_config(config_path: str) -> dict:
    """Load training configuration from YAML file."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def train_classifier(config_path: str) -> None:
    """Train the behavior classifier model using YOLOv8-cls."""
    config = load_config(config_path)
    cls_cfg = config["classifier"]

    data_dir = os.path.join(os.path.dirname(__file__), "..", "data", "classification")
    data_dir = os.path.abspath(data_dir)

    if not os.path.isdir(data_dir):
        print(f"Error: classification data directory not found: {data_dir}")
        print("Expected structure:")
        print("  data/classification/train/eating/")
        print("  data/classification/train/resting/")
        print("  data/classification/train/moving/")
        print("  data/classification/val/eating/")
        print("  data/classification/val/resting/")
        print("  data/classification/val/moving/")
        return

    print("Loading model:", cls_cfg["model"])
    model = YOLO(cls_cfg["model"])

    print("Starting classifier training...")
    print(f"  Epochs: {cls_cfg['epochs']}")
    print(f"  Image size: {cls_cfg['imgsz']}")
    print(f"  Batch size: {cls_cfg['batch']}")
    print(f"  Data: {data_dir}")
    print("  Classes: eating, resting, moving")

    results = model.train(
        data=data_dir,
        epochs=cls_cfg["epochs"],
        imgsz=cls_cfg["imgsz"],
        batch=cls_cfg["batch"],
        project=os.path.join(os.path.dirname(__file__), "runs", "classify"),
        name="behavior_classifier",
        exist_ok=True,
    )

    models_dir = os.path.join(os.path.dirname(__file__), "..", "models")
    os.makedirs(models_dir, exist_ok=True)
    best_model = os.path.join(
        os.path.dirname(__file__), "runs", "classify", "behavior_classifier", "weights", "best.pt"
    )

    if os.path.isfile(best_model):
        dest = os.path.join(models_dir, "classifier_best.pt")
        shutil.copy2(best_model, dest)
        print(f"Best model saved to {os.path.abspath(dest)}")
    else:
        print("Warning: best.pt not found in training output")

    print("Training complete.")
    if results and hasattr(results, "results_dict"):
        metrics = results.results_dict
        print(f"  Top-1 accuracy: {metrics.get('metrics/accuracy_top1', 'N/A')}")
        print(f"  Top-5 accuracy: {metrics.get('metrics/accuracy_top5', 'N/A')}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train YOLOv8 behavior classifier.")
    parser.add_argument(
        "--config",
        default=os.path.join(os.path.dirname(__file__), "config.yaml"),
        help="Path to training config YAML (default: training/config.yaml)",
    )
    args = parser.parse_args()

    train_classifier(args.config)

"""Evaluate a trained YOLO model on a dataset."""

import argparse
import os

from ultralytics import YOLO


def evaluate_model(model_path: str, data_path: str) -> None:
    """Run validation on the given model and print metrics."""
    if not os.path.isfile(model_path):
        print(f"Error: model file not found: {model_path}")
        return

    print(f"Loading model: {model_path}")
    model = YOLO(model_path)

    task = model.task if hasattr(model, "task") else "detect"
    print(f"Model task: {task}")

    val_kwargs: dict = {
        "project": os.path.join(os.path.dirname(model_path), "eval_runs"),
        "name": "evaluation",
        "exist_ok": True,
    }

    if task == "classify":
        if os.path.isdir(data_path):
            val_kwargs["data"] = data_path
        else:
            print(f"Error: classification data directory not found: {data_path}")
            return
    else:
        if os.path.isfile(data_path) and data_path.endswith((".yaml", ".yml")):
            val_kwargs["data"] = data_path
        elif os.path.isdir(data_path):
            val_kwargs["data"] = data_path
        else:
            print(f"Error: dataset config or directory not found: {data_path}")
            return

    print("Running evaluation...")
    results = model.val(**val_kwargs)

    if results is None:
        print("Evaluation returned no results.")
        return

    print("\n--- Evaluation Results ---")

    if task == "classify":
        if hasattr(results, "results_dict"):
            metrics = results.results_dict
            print(f"  Top-1 Accuracy: {metrics.get('metrics/accuracy_top1', 'N/A')}")
            print(f"  Top-5 Accuracy: {metrics.get('metrics/accuracy_top5', 'N/A')}")
    else:
        if hasattr(results, "results_dict"):
            metrics = results.results_dict
            print(f"  Precision:  {metrics.get('metrics/precision(B)', 'N/A')}")
            print(f"  Recall:     {metrics.get('metrics/recall(B)', 'N/A')}")
            print(f"  mAP50:      {metrics.get('metrics/mAP50(B)', 'N/A')}")
            print(f"  mAP50-95:   {metrics.get('metrics/mAP50-95(B)', 'N/A')}")

    confusion_dir = os.path.join(
        os.path.dirname(model_path), "eval_runs", "evaluation"
    )
    if os.path.isdir(confusion_dir):
        cm_path = os.path.join(confusion_dir, "confusion_matrix.png")
        if os.path.isfile(cm_path):
            print(f"\nConfusion matrix saved to: {cm_path}")
        cm_norm_path = os.path.join(confusion_dir, "confusion_matrix_normalized.png")
        if os.path.isfile(cm_norm_path):
            print(f"Normalized confusion matrix saved to: {cm_norm_path}")

    print("\nEvaluation complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate a YOLO model.")
    parser.add_argument("--model", required=True, help="Path to the .pt model file")
    parser.add_argument(
        "--data",
        required=True,
        help="Path to dataset.yaml (detection) or data directory (classification)",
    )
    args = parser.parse_args()

    evaluate_model(args.model, args.data)

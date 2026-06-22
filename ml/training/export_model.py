"""Export a trained YOLO model to ONNX or other formats."""

import argparse
import os

from ultralytics import YOLO


def export_model(model_path: str, export_format: str) -> None:
    """Export a YOLO .pt model to the specified format."""
    if not os.path.isfile(model_path):
        print(f"Error: model file not found: {model_path}")
        return

    print(f"Loading model: {model_path}")
    model = YOLO(model_path)

    print(f"Exporting to {export_format.upper()} format...")

    export_kwargs: dict = {"format": export_format}

    if export_format == "onnx":
        export_kwargs["dynamic"] = True
        export_kwargs["simplify"] = True

    exported_path = model.export(**export_kwargs)

    if exported_path and os.path.isfile(exported_path):
        print(f"Model exported successfully: {exported_path}")
        size_mb = os.path.getsize(exported_path) / (1024 * 1024)
        print(f"  File size: {size_mb:.1f} MB")
    else:
        print("Export completed. Check the model directory for the output file.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export a YOLO model to ONNX or other formats.")
    parser.add_argument("--model", required=True, help="Path to the .pt model file")
    parser.add_argument(
        "--format",
        default="onnx",
        choices=["onnx", "torchscript", "openvino", "engine", "coreml"],
        help="Export format (default: onnx)",
    )
    args = parser.parse_args()

    export_model(args.model, args.format)

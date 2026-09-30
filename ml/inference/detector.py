"""Cow detection using YOLOv8."""

import os
from dataclasses import dataclass
from typing import List, Optional

import numpy as np
from ultralytics import YOLO


@dataclass
class Detection:
    bbox: List[float]  # [x1, y1, x2, y2]
    confidence: float
    class_id: int


COCO_COW_CLASS_ID = 19


class CowDetector:
    """Custom model (models/detector_best.pt) if present, else COCO YOLOv8n filtered to cows."""

    def __init__(self, model_path: str, confidence: float = 0.35, weights_dir: Optional[str] = None) -> None:
        self.confidence = confidence
        self.use_coco_fallback = False

        onnx_path = os.path.join(weights_dir, "yolov8n.onnx") if weights_dir else ""
        if os.path.isfile(model_path):
            self.model = YOLO(model_path)
            self.source = model_path
        elif onnx_path and os.path.isfile(onnx_path):
            # Exported at build with imgsz=416 (fixed input shape).
            self.model = YOLO(onnx_path, task="detect")
            self.use_coco_fallback = True
            self.source = onnx_path
        else:
            self.model = YOLO("yolov8n.pt")
            self.use_coco_fallback = True
            self.source = "yolov8n.pt"

        print(f"Detector: {self.source}")
        self.loaded = True

    def detect(self, frame: np.ndarray, imgsz: int = 416) -> List[Detection]:
        classes = [COCO_COW_CLASS_ID] if self.use_coco_fallback else None
        results = self.model(frame, conf=self.confidence, imgsz=imgsz, classes=classes, verbose=False)

        detections: List[Detection] = []
        for result in results:
            if result.boxes is None:
                continue
            boxes = result.boxes
            for i in range(len(boxes)):
                detections.append(Detection(
                    bbox=boxes.xyxy[i].tolist(),
                    confidence=float(boxes.conf[i].item()),
                    class_id=0 if self.use_coco_fallback else int(boxes.cls[i].item()),
                ))
        return detections

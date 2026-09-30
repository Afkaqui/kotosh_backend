"""Cow detection using YOLOv8."""

import os
from dataclasses import dataclass
from typing import List

import numpy as np
from ultralytics import YOLO


@dataclass
class Detection:
    bbox: List[float]  # [x1, y1, x2, y2]
    confidence: float
    class_id: int


COCO_COW_CLASS_ID = 19


class CowDetector:
    """Custom model (models/detector_best.pt) if present, else COCO YOLOv8n filtered to cows.

    PyTorch is used here on purpose: on the VPS CPU it beat the ONNX export (166 vs 283 ms/frame).
    """

    def __init__(self, model_path: str, confidence: float = 0.35) -> None:
        self.confidence = confidence
        self.use_coco_fallback = not os.path.isfile(model_path)
        self.source = "yolov8n.pt (COCO)" if self.use_coco_fallback else model_path
        self.model = YOLO("yolov8n.pt" if self.use_coco_fallback else model_path)
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

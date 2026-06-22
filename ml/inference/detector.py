"""Cow detection using YOLOv8."""

import os
from dataclasses import dataclass
from typing import List

import numpy as np
from ultralytics import YOLO


@dataclass
class Detection:
    """A single object detection result."""

    bbox: List[float]  # [x1, y1, x2, y2]
    confidence: float
    class_id: int


# COCO class ID for cow
COCO_COW_CLASS_ID = 19


class CowDetector:
    """Wrapper around YOLOv8 for cow detection."""

    def __init__(self, model_path: str, confidence: float = 0.5) -> None:
        self.confidence = confidence
        self.use_coco_fallback = False

        if os.path.isfile(model_path):
            print(f"Loading custom detector model: {model_path}")
            self.model = YOLO(model_path)
        else:
            print(f"Custom model not found at {model_path}, using pretrained YOLOv8n (COCO)")
            self.model = YOLO("yolov8n.pt")
            self.use_coco_fallback = True

        self.loaded = True

    def detect(self, frame: np.ndarray) -> List[Detection]:
        """Run detection on a frame and return cow detections."""
        results = self.model(frame, conf=self.confidence, verbose=False)

        detections: List[Detection] = []
        for result in results:
            if result.boxes is None:
                continue

            boxes = result.boxes
            for i in range(len(boxes)):
                cls_id = int(boxes.cls[i].item())
                conf = float(boxes.conf[i].item())
                xyxy = boxes.xyxy[i].tolist()

                if self.use_coco_fallback:
                    if cls_id != COCO_COW_CLASS_ID:
                        continue
                    cls_id = 0

                detections.append(Detection(
                    bbox=xyxy,
                    confidence=conf,
                    class_id=cls_id,
                ))

        return detections

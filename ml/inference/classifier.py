"""Cow behavior classification using YOLOv8-cls."""

import os
from typing import Tuple

import numpy as np
from ultralytics import YOLO


BEHAVIOR_CLASSES = ["eating", "resting", "moving"]


class BehaviorClassifier:
    """Wrapper around YOLOv8-cls for cow behavior classification."""

    def __init__(self, model_path: str) -> None:
        self.use_heuristic = False

        if os.path.isfile(model_path):
            print(f"Loading custom classifier model: {model_path}")
            self.model = YOLO(model_path)
        else:
            print(f"Classifier model not found at {model_path}, using heuristic fallback")
            self.model = None
            self.use_heuristic = True

        self.loaded = not self.use_heuristic

    def classify(self, crop: np.ndarray) -> Tuple[str, float]:
        """Classify the behavior of a cow from a cropped image."""
        if self.use_heuristic:
            return self._heuristic_classify(crop)

        results = self.model(crop, verbose=False)

        if results and results[0].probs is not None:
            probs = results[0].probs
            top_idx = int(probs.top1)
            top_conf = float(probs.top1conf.item())
            names = results[0].names

            if top_idx in names:
                label = names[top_idx]
                if label in BEHAVIOR_CLASSES:
                    return label, top_conf

            if top_idx < len(BEHAVIOR_CLASSES):
                return BEHAVIOR_CLASSES[top_idx], top_conf

        return self._heuristic_classify(crop)

    def _heuristic_classify(self, crop: np.ndarray) -> Tuple[str, float]:
        """Classify behavior using simple image heuristics as a placeholder."""
        h, w = crop.shape[:2]
        aspect_ratio = w / max(h, 1)

        gray = crop.mean() if crop.size > 0 else 128.0

        if aspect_ratio > 1.4:
            return "eating", 0.55
        elif aspect_ratio < 0.8:
            return "moving", 0.50

        if gray < 100:
            return "resting", 0.50
        elif gray > 160:
            return "eating", 0.45
        else:
            return "moving", 0.45

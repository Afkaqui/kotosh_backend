"""Cow posture/behavior classification.

Priority: trained YOLOv8-cls model (models/classifier_best.pt) > CLIP zero-shot > heuristic.
Movement is decided by the video processor from track displacement; this module
classifies what a single crop looks like (eating / resting / moving).
"""

import os
from typing import Dict, List, Optional, Sequence, Tuple

import cv2
import numpy as np

BEHAVIOR_CLASSES = ["eating", "resting", "moving"]

PROMPTS: Dict[str, List[str]] = {
    "eating": [
        "a photo of a cow grazing with its head down",
        "a photo of a cow eating grass",
        "a photo of a cow eating hay from a feeder",
        "a photo of a cow with its muzzle on the ground eating",
    ],
    "resting": [
        "a photo of a cow lying down on the ground",
        "a photo of a cow resting on the grass",
        "a photo of a cow standing still with its head up",
        "a photo of a cow sleeping",
    ],
    "moving": [
        "a photo of a cow walking",
        "a photo of a cow running",
    ],
}


class BehaviorClassifier:
    def __init__(self, model_path: str, use_clip: bool = True, clip_model: str = "ViT-B-32",
                 clip_pretrained: str = "openai") -> None:
        self.mode = "heuristic"
        self.model = None

        if os.path.isfile(model_path):
            from ultralytics import YOLO

            print(f"Loading custom classifier model: {model_path}")
            self.model = YOLO(model_path)
            self.mode = "yolo-cls"
        elif use_clip:
            try:
                self._load_clip(clip_model, clip_pretrained)
                self.mode = "clip-zero-shot"
            except Exception as e:  # noqa: BLE001 - keep service up without CLIP
                print(f"CLIP unavailable ({e}); using heuristic classifier")

        print(f"Behavior classifier mode: {self.mode}")
        self.loaded = self.mode != "heuristic"

    def _load_clip(self, name: str, pretrained: str) -> None:
        import open_clip
        import torch

        model, _, preprocess = open_clip.create_model_and_transforms(name, pretrained=pretrained)
        model.eval()
        tokenizer = open_clip.get_tokenizer(name)

        self._torch = torch
        self._clip = model
        self._preprocess = preprocess
        self._prompt_classes: List[str] = []
        texts: List[str] = []
        for cls, prompts in PROMPTS.items():
            for p in prompts:
                texts.append(p)
                self._prompt_classes.append(cls)

        with torch.no_grad():
            feats = model.encode_text(tokenizer(texts))
            self._text_feats = feats / feats.norm(dim=-1, keepdim=True)
        self._logit_scale = float(model.logit_scale.exp().item())

    def classify_batch(
        self, crops: Sequence[np.ndarray], allowed: Optional[Sequence[str]] = None
    ) -> List[Tuple[str, float]]:
        """Classify BGR crops. `allowed` restricts the candidate classes."""
        if not crops:
            return []
        if self.mode == "clip-zero-shot":
            return self._clip_classify(crops, allowed)
        if self.mode == "yolo-cls":
            return [self._yolo_classify(c) for c in crops]
        return [self._heuristic_classify(c) for c in crops]

    def classify(self, crop: np.ndarray) -> Tuple[str, float]:
        return self.classify_batch([crop])[0]

    def _clip_classify(
        self, crops: Sequence[np.ndarray], allowed: Optional[Sequence[str]]
    ) -> List[Tuple[str, float]]:
        from PIL import Image

        torch = self._torch
        images = torch.stack([
            self._preprocess(Image.fromarray(cv2.cvtColor(c, cv2.COLOR_BGR2RGB))) for c in crops
        ])
        with torch.no_grad():
            img_feats = self._clip.encode_image(images)
            img_feats = img_feats / img_feats.norm(dim=-1, keepdim=True)
            probs = (self._logit_scale * img_feats @ self._text_feats.T).softmax(dim=-1).numpy()

        classes = list(allowed) if allowed else BEHAVIOR_CLASSES
        results: List[Tuple[str, float]] = []
        for row in probs:
            scores = {c: 0.0 for c in classes}
            for p, cls in zip(row, self._prompt_classes):
                if cls in scores:
                    scores[cls] += float(p)
            total = sum(scores.values()) or 1.0
            label = max(scores, key=scores.get)
            results.append((label, scores[label] / total))
        return results

    def _yolo_classify(self, crop: np.ndarray) -> Tuple[str, float]:
        results = self.model(crop, verbose=False)
        if results and results[0].probs is not None:
            probs = results[0].probs
            top_idx = int(probs.top1)
            label = results[0].names.get(top_idx, "")
            if label in BEHAVIOR_CLASSES:
                return label, float(probs.top1conf.item())
        return self._heuristic_classify(crop)

    def _heuristic_classify(self, crop: np.ndarray) -> Tuple[str, float]:
        """Last-resort fallback: a lying cow's box is wide and low."""
        h, w = crop.shape[:2]
        if h == 0 or w == 0:
            return "resting", 0.4
        aspect_ratio = w / h
        if aspect_ratio > 2.0:
            return "resting", 0.5
        if aspect_ratio > 1.4:
            return "eating", 0.45
        return "resting", 0.4

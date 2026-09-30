"""Cow posture/behavior classification.

Priority: trained YOLOv8-cls (models/classifier_best.pt) > CLIP zero-shot via
ONNX Runtime (weights baked at build) > CLIP via PyTorch > aspect-ratio heuristic.
Movement is decided by the video processor from track displacement.
"""

import json
import os
from typing import List, Optional, Sequence, Tuple

import cv2
import numpy as np

from inference.prompts import BEHAVIOR_CLASSES, PROMPTS


class BehaviorClassifier:
    def __init__(
        self,
        model_path: str,
        weights_dir: Optional[str] = None,
        use_clip: bool = True,
        clip_model: str = "ViT-B-32-quickgelu",
        clip_pretrained: str = "openai",
        threads: int = 4,
    ) -> None:
        self.mode = "heuristic"
        self.engine = "none"

        if os.path.isfile(model_path):
            from ultralytics import YOLO

            self.model = YOLO(model_path)
            self.mode, self.engine = "yolo-cls", "ultralytics"
        elif use_clip:
            try:
                if weights_dir and os.path.isfile(os.path.join(weights_dir, "clip_visual.onnx")):
                    self._load_clip_onnx(weights_dir, threads)
                    self.engine = "onnxruntime"
                else:
                    self._load_clip_torch(clip_model, clip_pretrained)
                    self.engine = "torch"
                self.mode = "clip-zero-shot"
            except Exception as e:  # noqa: BLE001 - keep the service up without CLIP
                print(f"CLIP unavailable ({e}); using heuristic classifier")

        print(f"Behavior classifier: mode={self.mode} engine={self.engine}")
        self.loaded = self.mode != "heuristic"

    def _load_clip_onnx(self, weights_dir: str, threads: int) -> None:
        import onnxruntime as ort

        with open(os.path.join(weights_dir, "clip_meta.json")) as f:
            meta = json.load(f)
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = threads
        self._session = ort.InferenceSession(
            os.path.join(weights_dir, "clip_visual.onnx"), opts, providers=["CPUExecutionProvider"]
        )
        self._text_feats = np.load(os.path.join(weights_dir, "clip_text_features.npy"))
        self._prompt_classes: List[str] = meta["classes"]
        self._logit_scale = float(meta["logit_scale"])
        self._size = int(meta["size"])
        self._mean = np.array(meta["mean"], dtype=np.float32)
        self._std = np.array(meta["std"], dtype=np.float32)

    def _load_clip_torch(self, name: str, pretrained: str) -> None:
        import open_clip
        import torch

        model, _, _ = open_clip.create_model_and_transforms(name, pretrained=pretrained)
        model.eval()
        tokenizer = open_clip.get_tokenizer(name)
        self._prompt_classes = [c for c, ps in PROMPTS.items() for _ in ps]
        texts = [p for ps in PROMPTS.values() for p in ps]
        with torch.no_grad():
            feats = model.encode_text(tokenizer(texts))
            self._text_feats = (feats / feats.norm(dim=-1, keepdim=True)).numpy()
        self._torch, self._clip = torch, model
        self._logit_scale = float(model.logit_scale.exp().item())
        self._size = 224
        self._mean = np.array(open_clip.OPENAI_DATASET_MEAN, dtype=np.float32)
        self._std = np.array(open_clip.OPENAI_DATASET_STD, dtype=np.float32)

    def _preprocess(self, crop: np.ndarray) -> np.ndarray:
        """CLIP preprocessing: shortest side to 224 (bicubic), center crop, normalize."""
        h, w = crop.shape[:2]
        scale = self._size / min(h, w)
        resized = cv2.resize(
            crop, (max(self._size, round(w * scale)), max(self._size, round(h * scale))),
            interpolation=cv2.INTER_CUBIC,
        )
        rh, rw = resized.shape[:2]
        top, left = (rh - self._size) // 2, (rw - self._size) // 2
        patch = resized[top: top + self._size, left: left + self._size]
        rgb = cv2.cvtColor(patch, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        return ((rgb - self._mean) / self._std).transpose(2, 0, 1)

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

    def _clip_classify(
        self, crops: Sequence[np.ndarray], allowed: Optional[Sequence[str]]
    ) -> List[Tuple[str, float]]:
        batch = np.stack([self._preprocess(c) for c in crops]).astype(np.float32)
        if self.engine == "onnxruntime":
            emb = self._session.run(None, {"image": batch})[0]
        else:
            with self._torch.no_grad():
                e = self._clip.encode_image(self._torch.from_numpy(batch))
                emb = (e / e.norm(dim=-1, keepdim=True)).numpy()

        logits = self._logit_scale * emb @ self._text_feats.T
        logits -= logits.max(axis=1, keepdims=True)
        probs = np.exp(logits)
        probs /= probs.sum(axis=1, keepdims=True)

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
            label = results[0].names.get(int(probs.top1), "")
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

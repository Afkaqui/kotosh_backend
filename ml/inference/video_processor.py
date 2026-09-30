"""Video processing pipeline: detect, track, and classify cow behavior."""

import os
from collections import Counter, defaultdict, deque
from typing import Deque, Dict, List, Optional, Tuple

import cv2
import numpy as np

from inference.classifier import BehaviorClassifier
from inference.config import Settings
from inference.detector import CowDetector
from inference.schemas import AnalysisResponse, AnimalResult, BehaviorEntry
from inference.tracker import SimpleIOUTracker

STATIONARY_CLASSES = ("eating", "resting")


class VideoProcessor:
    def __init__(
        self,
        detector: CowDetector,
        classifier: BehaviorClassifier,
        tracker: SimpleIOUTracker,
        settings: Settings,
    ) -> None:
        self.detector = detector
        self.classifier = classifier
        self.tracker = tracker
        self.settings = settings

    def process(self, video_path: str) -> AnalysisResponse:
        if not os.path.isfile(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
        if fps <= 0 or fps > 240:
            fps = 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps

        if duration > self.settings.max_video_duration:
            cap.release()
            raise ValueError(
                f"Video duration ({duration:.0f}s) exceeds maximum "
                f"({self.settings.max_video_duration}s)"
            )

        self.tracker.reset()
        sample_rate = max(1, round(fps * self.settings.sample_interval_seconds))

        logs: Dict[int, List[BehaviorEntry]] = defaultdict(list)
        confidences: Dict[int, List[float]] = defaultdict(list)
        history: Dict[int, Deque[Tuple[float, float, float, float]]] = defaultdict(
            lambda: deque(maxlen=8)
        )

        processed_frames = 0
        frame_idx = 0
        # grab() skips the costly retrieve/convert step; seeking per sample is slow on H.264.
        while True:
            if frame_idx % sample_rate == 0:
                ret, frame = cap.read()
                if not ret:
                    break
                self._process_frame(frame, frame_idx, fps, logs, confidences, history)
                processed_frames += 1
            elif not cap.grab():
                break
            frame_idx += 1

        cap.release()

        seconds_per_sample = sample_rate / fps
        animals = self._build_results(logs, confidences, seconds_per_sample)

        return AnalysisResponse(
            fps=fps,
            total_frames=total_frames or frame_idx,
            processed_frames=processed_frames,
            classifier_mode=self.classifier.mode,
            animals=animals,
        )

    def _resize_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, float]:
        h, w = frame.shape[:2]
        target = self.settings.inference_resolution
        if max(h, w) <= target:
            return frame, 1.0
        scale = target / max(h, w)
        resized = cv2.resize(frame, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
        return resized, scale

    def _speed(self, track_hist: Deque[Tuple[float, float, float, float]]) -> Optional[float]:
        """Centroid speed in body-heights per second over roughly the last second."""
        if len(track_hist) < 2:
            return None
        t_now, cx, cy, h = track_hist[-1]
        ref = track_hist[0]
        for entry in reversed(track_hist):
            if t_now - entry[0] >= 1.0:
                ref = entry
                break
        dt = t_now - ref[0]
        if dt <= 0:
            return None
        body = max((h + ref[3]) / 2, 1.0)
        return float(np.hypot(cx - ref[1], cy - ref[2]) / body / dt)

    def _process_frame(self, frame, frame_idx, fps, logs, confidences, history) -> None:
        resized, scale = self._resize_frame(frame)
        detections = self.detector.detect(resized, imgsz=self.settings.inference_resolution)
        if scale != 1.0:
            for det in detections:
                det.bbox = [c / scale for c in det.bbox]
        tracked = self.tracker.update(detections)

        h, w = frame.shape[:2]
        t = frame_idx / fps
        pending: List[Tuple[int, float, np.ndarray, Optional[float]]] = []

        for td in tracked:
            x1, y1, x2, y2 = td.bbox
            bw, bh = x2 - x1, y2 - y1
            if bw <= 2 or bh <= 2:
                continue
            history[td.track_id].append((t, (x1 + x2) / 2, (y1 + y2) / 2, bh))
            confidences[td.track_id].append(td.confidence)

            speed = self._speed(history[td.track_id])
            if speed is not None and speed >= self.settings.moving_speed_threshold:
                conf = min(0.99, 0.6 + 0.4 * (speed / (speed + self.settings.moving_speed_threshold)))
                logs[td.track_id].append(BehaviorEntry(
                    frame=frame_idx, timestamp=round(t, 2), behavior="moving", confidence=round(conf, 3),
                ))
                continue

            # Pad the crop so ground/feeder context is visible to the classifier.
            px, py = bw * 0.1, bh * 0.1
            cx1, cy1 = max(0, int(x1 - px)), max(0, int(y1 - py))
            cx2, cy2 = min(w, int(x2 + px)), min(h, int(y2 + py))
            if cx2 - cx1 < 8 or cy2 - cy1 < 8:
                continue
            pending.append((td.track_id, t, frame[cy1:cy2, cx1:cx2], speed))

        if not pending:
            return

        known = [p for p in pending if p[3] is not None]
        unknown = [p for p in pending if p[3] is None]
        for group, allowed in ((known, STATIONARY_CLASSES), (unknown, None)):
            if not group:
                continue
            preds = self.classifier.classify_batch([p[2] for p in group], allowed=allowed)
            for (track_id, ts, _, _), (label, conf) in zip(group, preds):
                logs[track_id].append(BehaviorEntry(
                    frame=frame_idx, timestamp=round(ts, 2), behavior=label, confidence=round(conf, 3),
                ))

    def _smooth(self, labels: List[str]) -> List[str]:
        window = self.settings.smoothing_window
        if window <= 1 or len(labels) < window:
            return labels
        half = window // 2
        out = []
        for i in range(len(labels)):
            segment = labels[max(0, i - half): i + half + 1]
            out.append(Counter(segment).most_common(1)[0][0])
        return out

    def _build_results(self, logs, confidences, seconds_per_sample: float) -> List[AnimalResult]:
        animals: List[AnimalResult] = []
        for track_id, entries in sorted(logs.items()):
            if len(entries) < self.settings.min_track_samples:
                continue
            entries.sort(key=lambda e: e.frame)
            smoothed = self._smooth([e.behavior for e in entries])
            for entry, label in zip(entries, smoothed):
                entry.behavior = label

            counts = Counter(smoothed)
            eating = counts.get("eating", 0) * seconds_per_sample
            resting = counts.get("resting", 0) * seconds_per_sample
            moving = counts.get("moving", 0) * seconds_per_sample
            confs = confidences[track_id]

            animals.append(AnimalResult(
                track_id=track_id,
                label="cow",
                confidence=round(sum(confs) / len(confs), 4) if confs else 0.0,
                eating_seconds=round(eating, 2),
                resting_seconds=round(resting, 2),
                moving_seconds=round(moving, 2),
                total_seconds=round(eating + resting + moving, 2),
                behavior_log=entries,
            ))
        return animals

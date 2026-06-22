"""Video processing pipeline: detect, classify, and track cows."""

import os
from collections import defaultdict
from typing import Dict, List, Tuple

import cv2
import numpy as np

from inference.classifier import BehaviorClassifier
from inference.config import Settings
from inference.detector import CowDetector
from inference.schemas import AnalysisResponse, AnimalResult, BehaviorEntry
from inference.tracker import SimpleIOUTracker, TrackedDetection


class VideoProcessor:
    """Orchestrates detection, classification, and tracking on a video."""

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
        """Process a video and return analysis results for all tracked animals."""
        if not os.path.isfile(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0

        if duration > self.settings.max_video_duration:
            cap.release()
            raise ValueError(
                f"Video duration ({duration:.0f}s) exceeds maximum "
                f"({self.settings.max_video_duration}s)"
            )

        self.tracker.reset()

        # Per-track accumulator: track_id -> {behaviors, confidences, log}
        track_data: Dict[int, Dict] = defaultdict(lambda: {
            "behavior_counts": defaultdict(int),
            "confidences": [],
            "log": [],
        })

        processed_frames = 0
        frame_idx = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % self.settings.frame_sample_rate == 0:
                tracked = self._process_frame(
                    frame, frame_idx, fps, track_data
                )
                processed_frames += 1

            frame_idx += 1

        cap.release()

        animals = self._build_results(track_data, fps)

        return AnalysisResponse(
            fps=fps,
            total_frames=total_frames,
            processed_frames=processed_frames,
            animals=animals,
        )

    def _process_frame(
        self,
        frame: np.ndarray,
        frame_idx: int,
        fps: float,
        track_data: Dict[int, Dict],
    ) -> List[TrackedDetection]:
        """Detect, classify, and track cows in a single frame."""
        detections = self.detector.detect(frame)
        tracked = self.tracker.update(detections)

        h, w = frame.shape[:2]

        for td in tracked:
            x1 = max(0, int(td.bbox[0]))
            y1 = max(0, int(td.bbox[1]))
            x2 = min(w, int(td.bbox[2]))
            y2 = min(h, int(td.bbox[3]))

            if x2 <= x1 or y2 <= y1:
                continue

            crop = frame[y1:y2, x1:x2]
            behavior, conf = self.classifier.classify(crop)

            data = track_data[td.track_id]
            data["behavior_counts"][behavior] += 1
            data["confidences"].append(td.confidence)
            data["log"].append(BehaviorEntry(
                frame=frame_idx,
                timestamp=frame_idx / fps if fps > 0 else 0.0,
                behavior=behavior,
                confidence=conf,
            ))

        return tracked

    def _build_results(
        self,
        track_data: Dict[int, Dict],
        fps: float,
    ) -> List[AnimalResult]:
        """Convert accumulated tracking data into AnimalResult list."""
        animals: List[AnimalResult] = []
        seconds_per_sample = self.settings.frame_sample_rate / fps if fps > 0 else 0

        for track_id, data in sorted(track_data.items()):
            counts = data["behavior_counts"]
            confs = data["confidences"]

            eating_seconds = counts.get("eating", 0) * seconds_per_sample
            resting_seconds = counts.get("resting", 0) * seconds_per_sample
            moving_seconds = counts.get("moving", 0) * seconds_per_sample
            total_seconds = eating_seconds + resting_seconds + moving_seconds

            avg_confidence = sum(confs) / len(confs) if confs else 0.0

            animals.append(AnimalResult(
                track_id=track_id,
                label="cow",
                confidence=round(avg_confidence, 4),
                eating_seconds=round(eating_seconds, 2),
                resting_seconds=round(resting_seconds, 2),
                moving_seconds=round(moving_seconds, 2),
                total_seconds=round(total_seconds, 2),
                behavior_log=data["log"],
            ))

        return animals

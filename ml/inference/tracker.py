"""Simple IoU-based object tracker."""

from dataclasses import dataclass, field
from typing import List

from inference.detector import Detection


@dataclass
class TrackedDetection:
    """A detection with an assigned track ID."""

    bbox: List[float]
    confidence: float
    class_id: int
    track_id: int


@dataclass
class Track:
    """Internal state for a single tracked object."""

    track_id: int
    bbox: List[float]
    lost_count: int = 0


def compute_iou(box_a: List[float], box_b: List[float]) -> float:
    """Compute Intersection over Union between two bounding boxes."""
    x1 = max(box_a[0], box_b[0])
    y1 = max(box_a[1], box_b[1])
    x2 = min(box_a[2], box_b[2])
    y2 = min(box_a[3], box_b[3])

    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    if intersection == 0:
        return 0.0

    area_a = (box_a[2] - box_a[0]) * (box_a[3] - box_a[1])
    area_b = (box_b[2] - box_b[0]) * (box_b[3] - box_b[1])
    union = area_a + area_b - intersection

    return intersection / union if union > 0 else 0.0


class SimpleIOUTracker:
    """Greedy IoU-based multi-object tracker."""

    def __init__(self, iou_threshold: float = 0.3, max_lost: int = 10) -> None:
        self.iou_threshold = iou_threshold
        self.max_lost = max_lost
        self.tracks: List[Track] = []
        self._next_id = 1

    def update(self, detections: List[Detection]) -> List[TrackedDetection]:
        """Match detections to existing tracks and return tracked detections."""
        tracked: List[TrackedDetection] = []
        matched_track_indices: set = set()
        matched_det_indices: set = set()

        # Build IoU matrix and greedily match
        pairs: List[tuple] = []
        for d_idx, det in enumerate(detections):
            for t_idx, track in enumerate(self.tracks):
                iou = compute_iou(det.bbox, track.bbox)
                if iou >= self.iou_threshold:
                    pairs.append((iou, d_idx, t_idx))

        pairs.sort(key=lambda x: x[0], reverse=True)

        for iou, d_idx, t_idx in pairs:
            if d_idx in matched_det_indices or t_idx in matched_track_indices:
                continue

            matched_det_indices.add(d_idx)
            matched_track_indices.add(t_idx)

            det = detections[d_idx]
            track = self.tracks[t_idx]
            track.bbox = det.bbox
            track.lost_count = 0

            tracked.append(TrackedDetection(
                bbox=det.bbox,
                confidence=det.confidence,
                class_id=det.class_id,
                track_id=track.track_id,
            ))

        # Create new tracks for unmatched detections
        for d_idx, det in enumerate(detections):
            if d_idx in matched_det_indices:
                continue

            new_track = Track(track_id=self._next_id, bbox=det.bbox)
            self._next_id += 1
            self.tracks.append(new_track)

            tracked.append(TrackedDetection(
                bbox=det.bbox,
                confidence=det.confidence,
                class_id=det.class_id,
                track_id=new_track.track_id,
            ))

        # Increment lost count for unmatched tracks and prune
        for t_idx, track in enumerate(self.tracks):
            if t_idx not in matched_track_indices:
                track.lost_count += 1

        self.tracks = [t for t in self.tracks if t.lost_count <= self.max_lost]

        return tracked

    def reset(self) -> None:
        """Clear all tracks and reset the ID counter."""
        self.tracks.clear()
        self._next_id = 1

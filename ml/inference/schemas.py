"""Pydantic schemas for API request and response models."""

from pydantic import BaseModel


class BehaviorEntry(BaseModel):
    """A single behavior observation at a specific frame."""

    frame: int
    timestamp: float
    behavior: str
    confidence: float


class AnimalResult(BaseModel):
    """Aggregated analysis result for a single tracked animal."""

    track_id: int
    label: str = "cow"
    confidence: float
    eating_seconds: float
    resting_seconds: float
    moving_seconds: float
    total_seconds: float
    behavior_log: list[BehaviorEntry]


class AnalysisRequest(BaseModel):
    """Request body for video analysis."""

    video_path: str


class AnalysisResponse(BaseModel):
    """Response body containing full video analysis results."""

    fps: float
    total_frames: int
    processed_frames: int
    animals: list[AnimalResult]


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    detector_loaded: bool
    classifier_loaded: bool

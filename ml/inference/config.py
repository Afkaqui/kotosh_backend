"""Configuration for the ML inference service."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    detector_model_path: str = "../models/detector_best.pt"
    classifier_model_path: str = "../models/classifier_best.pt"
    confidence_threshold: float = 0.5
    frame_sample_rate: int = 5
    max_video_duration: int = 600

    class Config:
        env_prefix = "ML_"

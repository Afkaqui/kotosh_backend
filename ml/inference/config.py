"""Configuration for the ML inference service."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ML_", extra="ignore")

    detector_model_path: str = "../models/detector_best.pt"
    classifier_model_path: str = "../models/classifier_best.pt"
    # ONNX exports baked into the image by export_models.py.
    weights_dir: str = "../weights"
    confidence_threshold: float = 0.35
    max_video_duration: int = 600

    # Lightweight processing: analyse 2 frames per second at 416 px.
    sample_interval_seconds: float = 0.5
    inference_resolution: int = 416
    torch_threads: int = 4

    use_clip: bool = True
    clip_model: str = "ViT-B-32-quickgelu"
    clip_pretrained: str = "openai"

    # Body-heights per second above which a cow is considered to be walking.
    moving_speed_threshold: float = 0.25
    # Posture changes slowly: re-run CLIP on a stationary cow at most this often.
    posture_interval_seconds: float = 3.0
    smoothing_window: int = 5
    min_track_samples: int = 3

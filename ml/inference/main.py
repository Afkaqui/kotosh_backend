"""FastAPI inference service for cow detection and behavior analysis."""

import os
import threading
from contextlib import asynccontextmanager

import torch
from fastapi import FastAPI, HTTPException

from inference.classifier import BehaviorClassifier
from inference.config import Settings
from inference.detector import CowDetector
from inference.schemas import AnalysisRequest, AnalysisResponse, HealthResponse
from inference.tracker import SimpleIOUTracker
from inference.video_processor import VideoProcessor

settings = Settings()
detector: CowDetector | None = None
classifier: BehaviorClassifier | None = None
# One analysis at a time keeps CPU usage bounded on the shared VPS.
analysis_lock = threading.Lock()


def _resolve(path: str) -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), path))


def _configure_torch() -> None:
    torch.set_num_threads(settings.torch_threads)
    torch.backends.nnpack.set_flags(False)
    try:
        with open("/proc/cpuinfo") as f:
            has_avx2 = "avx2" in f.read()
    except OSError:
        has_avx2 = True
    if not has_avx2:
        # oneDNN fails ("could not create a primitive") on virtual CPUs without AVX2.
        torch.backends.mkldnn.enabled = False
        print("CPU without AVX2: oneDNN disabled")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global detector, classifier
    _configure_torch()
    weights_dir = _resolve(settings.weights_dir)

    try:
        detector = CowDetector(_resolve(settings.detector_model_path), settings.confidence_threshold)
    except Exception as e:  # noqa: BLE001
        print(f"Warning: failed to load detector: {e}")
        detector = None

    classifier = BehaviorClassifier(
        _resolve(settings.classifier_model_path),
        weights_dir=weights_dir,
        use_clip=settings.use_clip,
        clip_model=settings.clip_model,
        clip_pretrained=settings.clip_pretrained,
        threads=settings.torch_threads,
    )

    print("ML service ready.")
    yield


app = FastAPI(
    title="KotoshTech ML Service",
    description="Cow detection and behavior analysis API",
    version="2.0.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok" if detector is not None else "degraded",
        detector_loaded=detector is not None and detector.loaded,
        classifier_loaded=classifier is not None and classifier.loaded,
        classifier_mode=classifier.mode if classifier else "none",
    )


@app.post("/analyze-video", response_model=AnalysisResponse)
def analyze_video(request: AnalysisRequest) -> AnalysisResponse:
    if detector is None or classifier is None:
        raise HTTPException(status_code=503, detail="Models are not loaded. Service is not ready.")

    video_path = os.path.abspath(request.video_path)
    if not os.path.isfile(video_path):
        raise HTTPException(status_code=404, detail=f"Video file not found: {video_path}")

    processor = VideoProcessor(detector, classifier, SimpleIOUTracker(), settings)
    with analysis_lock:
        try:
            return processor.process(video_path)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except RuntimeError as e:
            raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("inference.main:app", host="0.0.0.0", port=8000)

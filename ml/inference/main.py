"""FastAPI inference service for cow detection and behavior analysis."""

import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from inference.classifier import BehaviorClassifier
from inference.config import Settings
from inference.detector import CowDetector
from inference.schemas import AnalysisRequest, AnalysisResponse, HealthResponse
from inference.tracker import SimpleIOUTracker
from inference.video_processor import VideoProcessor

settings = Settings()
detector: CowDetector | None = None
classifier: BehaviorClassifier | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load ML models on startup."""
    global detector, classifier

    det_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), settings.detector_model_path)
    )
    cls_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), settings.classifier_model_path)
    )

    print(f"Loading detector from: {det_path}")
    try:
        detector = CowDetector(det_path, settings.confidence_threshold)
    except Exception as e:
        print(f"Warning: failed to load detector: {e}")
        detector = None

    print(f"Loading classifier from: {cls_path}")
    try:
        classifier = BehaviorClassifier(cls_path)
    except Exception as e:
        print(f"Warning: failed to load classifier: {e}")
        classifier = None

    print("ML service ready.")
    yield
    print("Shutting down ML service.")


app = FastAPI(
    title="KotoshTech ML Service",
    description="Cow detection and behavior analysis API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Return the health status of the ML service."""
    return HealthResponse(
        status="ok" if detector is not None else "degraded",
        detector_loaded=detector is not None and detector.loaded,
        classifier_loaded=classifier is not None and classifier.loaded,
    )


@app.post("/analyze-video", response_model=AnalysisResponse)
async def analyze_video(request: AnalysisRequest) -> AnalysisResponse:
    """Analyze a video file for cow detection and behavior classification."""
    if detector is None:
        raise HTTPException(
            status_code=503,
            detail="Detector model is not loaded. Service is not ready.",
        )

    if classifier is None:
        raise HTTPException(
            status_code=503,
            detail="Classifier model is not loaded. Service is not ready.",
        )

    video_path = request.video_path
    if not os.path.isabs(video_path):
        video_path = os.path.abspath(video_path)

    if not os.path.isfile(video_path):
        raise HTTPException(
            status_code=404,
            detail=f"Video file not found: {video_path}",
        )

    tracker = SimpleIOUTracker()
    processor = VideoProcessor(detector, classifier, tracker, settings)

    try:
        result = processor.process(video_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "inference.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )

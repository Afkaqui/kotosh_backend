FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

ENV HF_HOME=/app/.cache/hf \
    YOLO_CONFIG_DIR=/app/.cache/ultralytics \
    PYTHONUNBUFFERED=1
RUN mkdir -p /app/.cache/ultralytics

# CPU-only torch: the VPS has no GPU, and the CUDA wheels add ~2 GB.
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Export CLIP + YOLOv8n to ONNX at build time (~2x faster on the VPS CPU, no network at startup).
COPY inference/prompts.py inference/prompts.py
COPY export_models.py .
RUN python -W ignore export_models.py /app/weights && rm -rf /app/.cache/hf

COPY . .

RUN mkdir -p /app/models

EXPOSE 8000
CMD ["uvicorn", "inference.main:app", "--host", "0.0.0.0", "--port", "8000"]

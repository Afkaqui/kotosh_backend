FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

ENV HF_HOME=/app/.cache/hf \
    YOLO_CONFIG_DIR=/app/.cache/ultralytics \
    PYTHONUNBUFFERED=1

# CPU-only torch: the VPS has no GPU, and the CUDA wheels add ~2 GB.
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bake model weights into the image so startup never needs the network.
RUN python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')" && \
    python -c "import open_clip; open_clip.create_model_and_transforms('ViT-B-32', pretrained='openai')"

COPY . .

RUN mkdir -p /app/models

EXPOSE 8000
CMD ["uvicorn", "inference.main:app", "--host", "0.0.0.0", "--port", "8000"]

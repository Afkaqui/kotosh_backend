"""Build-time export of CLIP (visual encoder + prompt embeddings) and YOLOv8n to ONNX.

ONNX Runtime is ~2x faster than PyTorch on the VPS CPU (no AVX), and the
runtime then needs neither open_clip nor the text encoder.
"""

import json
import os
import sys

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(__file__))
from inference.prompts import PROMPTS  # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else "weights"
CLIP_NAME, CLIP_PRETRAINED = "ViT-B-32-quickgelu", "openai"

torch.backends.mkldnn.enabled = False
os.makedirs(OUT, exist_ok=True)


def export_clip() -> None:
    import open_clip

    model, _, _ = open_clip.create_model_and_transforms(CLIP_NAME, pretrained=CLIP_PRETRAINED)
    model.eval()
    tokenizer = open_clip.get_tokenizer(CLIP_NAME)

    classes, texts = [], []
    for cls, prompts in PROMPTS.items():
        for p in prompts:
            classes.append(cls)
            texts.append(p)
    with torch.no_grad():
        feats = model.encode_text(tokenizer(texts))
        feats = feats / feats.norm(dim=-1, keepdim=True)
    np.save(os.path.join(OUT, "clip_text_features.npy"), feats.numpy().astype(np.float32))
    with open(os.path.join(OUT, "clip_meta.json"), "w") as f:
        json.dump({
            "classes": classes,
            "logit_scale": float(model.logit_scale.exp().item()),
            "mean": list(getattr(model.visual, "image_mean", None) or open_clip.OPENAI_DATASET_MEAN),
            "std": list(getattr(model.visual, "image_std", None) or open_clip.OPENAI_DATASET_STD),
            "size": 224,
        }, f)

    class Visual(torch.nn.Module):
        def __init__(self, m):
            super().__init__()
            self.m = m

        def forward(self, x):
            e = self.m.encode_image(x)
            return e / e.norm(dim=-1, keepdim=True)

    visual = Visual(model).eval()
    dummy = torch.randn(2, 3, 224, 224)
    path = os.path.join(OUT, "clip_visual.onnx")
    torch.onnx.export(
        visual, (dummy,), path,
        input_names=["image"], output_names=["embedding"],
        dynamic_axes={"image": {0: "batch"}, "embedding": {0: "batch"}},
        opset_version=17, dynamo=False,
    )

    import onnxruntime as ort

    sess = ort.InferenceSession(path, providers=["CPUExecutionProvider"])
    x = np.random.rand(3, 3, 224, 224).astype(np.float32)
    with torch.no_grad():
        ref = visual(torch.from_numpy(x)).numpy()
    diff = float(np.abs(sess.run(None, {"image": x})[0] - ref).max())
    print(f"CLIP exported, max diff vs torch: {diff:.2e}")
    if diff > 1e-3:
        raise SystemExit("CLIP ONNX export does not match PyTorch output")


def export_yolo() -> None:
    from ultralytics import YOLO

    YOLO("yolov8n.pt").export(format="onnx", imgsz=416, dynamic=False, simplify=False)
    os.replace("yolov8n.onnx", os.path.join(OUT, "yolov8n.onnx"))
    print("YOLOv8n exported")


if __name__ == "__main__":
    export_clip()
    export_yolo()

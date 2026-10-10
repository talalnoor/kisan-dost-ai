import io
import os

from PIL import Image
from transformers import pipeline

HF_MODEL_ID = os.environ.get("HF_CV_MODEL_ID") or "linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification"

_classifier = None
_manual_model = None


def _load_pipeline():
    """Try to build the HF pipeline with an explicitly loaded image processor.

    The auto-detection step is what crashed ("Unrecognized image processor"),
    so we load the MobileNetV2 processor by name instead.
    """
    from transformers import MobileNetV2ImageProcessor

    processor = MobileNetV2ImageProcessor.from_pretrained(HF_MODEL_ID)
    return pipeline(
        "image-classification",
        model=HF_MODEL_ID,
        image_processor=processor,
    )


def _load_manual_model():
    """Last-resort path: skip the processor classes and preprocess by hand."""
    from transformers import AutoModelForImageClassification

    model = AutoModelForImageClassification.from_pretrained(HF_MODEL_ID)
    model.eval()
    return model


def _manual_predict(image: Image.Image) -> list:
    import numpy as np
    import torch

    global _manual_model
    if _manual_model is None:
        _manual_model = _load_manual_model()

    img = image.resize((224, 224))
    arr = np.asarray(img, dtype="float32") / 255.0
    arr = (arr - 0.5) / 0.5  # MobileNetV2 checkpoints use mean=std=0.5
    tensor = torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0)

    with torch.no_grad():
        logits = _manual_model(tensor).logits
        probs = torch.softmax(logits, dim=-1)[0]

    top_idx = int(torch.argmax(probs))
    return [{
        "label": _manual_model.config.id2label[top_idx],
        "score": float(probs[top_idx]),
    }]


def _get_classifier():
    global _classifier
    if _classifier is None:
        try:
            _classifier = _load_pipeline()
            print("[CV] Loaded HF pipeline with explicit image processor")
        except Exception as e:
            print(f"[CV] Pipeline load failed ({e}); will use manual preprocessing")
            _classifier = "manual"
    return _classifier


def normalize_label(raw_label: str) -> str:
    label = raw_label.lower()
    label = label.replace("___", "_").replace("__", "_")
    label = label.replace(",", "").replace("(", "").replace(")", "")
    label = label.replace(" ", "_")
    return label


def real_cv_predict(image_bytes: bytes) -> dict:
    classifier = _get_classifier()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    if classifier == "manual":
        predictions = _manual_predict(image)
    else:
        try:
            predictions = classifier(image)
        except Exception as e:
            print(f"[CV] Pipeline inference failed ({e}); using manual preprocessing")
            predictions = _manual_predict(image)

    if not predictions:
        raise RuntimeError("Model returned no predictions")

    top = predictions[0]
    return {
        "disease_label": normalize_label(top["label"]),
        "confidence": round(float(top["score"]), 3),
        "raw_label": top["label"],
    }
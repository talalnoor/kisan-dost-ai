import io
import os
from PIL import Image
from transformers import pipeline

HF_MODEL_ID = os.environ.get("HF_CV_MODEL_ID") or "linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification"

_classifier = None


def _get_classifier():
    global _classifier
    if _classifier is None:
        _classifier = pipeline("image-classification", model=HF_MODEL_ID)
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
    predictions = classifier(image)

    if not predictions:
        raise RuntimeError("Model returned no predictions")

    top = predictions[0]
    return {
        "disease_label": normalize_label(top["label"]),
        "confidence": round(float(top["score"]), 3),
        "raw_label": top["label"],
    }

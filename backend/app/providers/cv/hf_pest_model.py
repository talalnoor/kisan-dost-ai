import io
import os
from PIL import Image
from transformers import pipeline

PEST_MODEL_ID = os.environ.get("HF_PEST_MODEL_ID") or "dima806/farm_insects_image_detection"

_classifier = None


def _get_classifier():
    global _classifier
    if _classifier is None:
        _classifier = pipeline("image-classification", model=PEST_MODEL_ID)
    return _classifier


def normalize_label(raw_label: str) -> str:
    label = raw_label.lower()
    label = label.replace("(", "").replace(")", "")
    label = label.replace(" ", "_")
    return label


def real_pest_predict(image_bytes: bytes) -> dict:
    classifier = _get_classifier()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    predictions = classifier(image)

    if not predictions:
        raise RuntimeError("Pest model returned no predictions")

    top = predictions[0]
    return {
        "pest_label": normalize_label(top["label"]),
        "confidence": round(float(top["score"]), 3),
        "raw_label": top["label"],
    }

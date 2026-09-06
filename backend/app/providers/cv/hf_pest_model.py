import io
import os
from PIL import Image
from transformers import pipeline

# Real HuggingFace insect classifier, trained on the "Dangerous Farm Insects"
# dataset (15 common agricultural pest classes). Apache 2.0 licensed.
# This is a general-purpose insect classifier, not fine-tuned on Pakistani
# crop-specific pest presentations — flagged honestly to the farmer in the
# frontend disclaimer rather than presented as more precise than it is.
HF_PEST_MODEL_ID = os.environ.get("HF_PEST_MODEL_ID") or "dima806/farm_insects_image_detection"

_pest_classifier = None


def _get_pest_classifier():
    global _pest_classifier
    if _pest_classifier is None:
        _pest_classifier = pipeline("image-classification", model=HF_PEST_MODEL_ID)
    return _pest_classifier


def normalize_pest_label(raw_label: str) -> str:
    label = raw_label.lower().strip()
    label = label.replace("___", "_").replace("__", "_")
    label = label.replace(",", "").replace("(", "").replace(")", "")
    label = label.replace("-", "_").replace(" ", "_")
    return label


def real_pest_predict(image_bytes: bytes) -> dict:
    classifier = _get_pest_classifier()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    predictions = classifier(image)

    if not predictions:
        raise RuntimeError("Pest model returned no predictions")

    top = predictions[0]
    return {
        "pest_label": normalize_pest_label(top["label"]),
        "confidence": round(float(top["score"]), 3),
        "raw_label": top["label"],
    }
import os
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from supabase import create_client, Client
from app.core.security import get_current_user, get_user_id

router = APIRouter(prefix="/api/v1/disease", tags=["disease"])

supabase_url = os.environ.get("SUPABASE_URL")
supabase_anon_key = os.environ.get("SUPABASE_ANON_KEY")

MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/jpg"}


def get_user_supabase_client(token: str) -> Client:
    client = create_client(supabase_url, supabase_anon_key)
    client.postgrest.auth(token)
    return client


def mock_cv_predict(image_bytes: bytes) -> dict:
    """
    TEMPORARY mock standing in for Zain's real CV provider.
    Replace this function's body with a real call to
    app/providers/cv/hf_plant_model.py once the model is chosen.
    Must keep returning this exact shape: {disease_label, confidence}.
    """
    return {"disease_label": "tomato_early_blight", "confidence": 0.87}


# TEMPORARY knowledge lookup — replace with real reads from
# backend/app/knowledge/diseases.json once Zain builds it.
MOCK_KNOWLEDGE = {
    "tomato_early_blight": {
        "display_name": "Tomato Early Blight",
        "severity": "moderate",
        "symptoms": ["Dark concentric-ring spots on lower leaves", "Yellowing around lesions"],
        "causes": ["Fungal pathogen (Alternaria solani)", "Favored by warm, humid conditions"],
        "treatment": ["Apply copper-based or chlorothalonil fungicide", "Remove and destroy infected leaves"],
        "prevention": ["Crop rotation", "Avoid overhead watering", "Ensure adequate plant spacing"],
    }
}


@router.post("/analyze")
async def analyze_disease(
    image: UploadFile = File(...),
    crop_id: str = Form(...),
    scan_type: str = Form("disease"),
    user: dict = Depends(get_current_user),
    authorization: str = None,
):
    user_id = get_user_id(user)

    if image.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail={"code": "INVALID_IMAGE", "message": "Only JPG/PNG images are supported"})

    image_bytes = await image.read()
    if len(image_bytes) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=400, detail={"code": "IMAGE_TOO_LARGE", "message": "Image exceeds 5MB limit"})

    prediction = mock_cv_predict(image_bytes)
    disease_label = prediction["disease_label"]
    confidence = prediction["confidence"]
    low_confidence = confidence < 0.5

    knowledge = MOCK_KNOWLEDGE.get(disease_label, {
        "display_name": disease_label,
        "severity": "unknown",
        "symptoms": [],
        "causes": [],
        "treatment": [],
        "prevention": [],
    })

    result = {
        "scan_id": str(uuid.uuid4()),
        "scan_type": scan_type,
        "disease": knowledge["display_name"],
        "confidence": confidence,
        "severity": knowledge["severity"],
        "low_confidence": low_confidence,
        "symptoms": knowledge["symptoms"],
        "causes": knowledge["causes"],
        "treatment": knowledge["treatment"],
        "prevention": knowledge["prevention"],
        "weather_risk": None,  # wired up once weather_service exists
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    return {"success": True, "data": result, "error": None}
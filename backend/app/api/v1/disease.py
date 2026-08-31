import os
import uuid
import httpx
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Header
from supabase import create_client, Client
from app.core.security import get_current_user, get_user_id

router = APIRouter(prefix="/api/v1/disease", tags=["disease"])

supabase_url = os.environ.get("SUPABASE_URL")
supabase_anon_key = os.environ.get("SUPABASE_ANON_KEY")
weather_api_key = os.environ.get("WEATHER_API_KEY")

MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/jpg"}


def get_weather_risk(lat: float, lon: float, humidity_threshold: int = 75) -> dict:
    """
    Fetches current weather and converts it to a simple risk classification
    for fungal/disease spread. Returns None if weather can't be fetched —
    disease analysis must still succeed even if weather fails.
    """
    if not weather_api_key or lat is None or lon is None:
        return None
    try:
        params = {"lat": lat, "lon": lon, "appid": weather_api_key, "units": "metric"}
        response = httpx.get("https://api.openweathermap.org/data/2.5/weather", params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        humidity = data["main"]["humidity"]
        condition = data["weather"][0]["main"].lower()
        is_rainy = "rain" in condition or "drizzle" in condition

        if humidity >= humidity_threshold and is_rainy:
            return {"level": "high", "reason": f"High humidity ({humidity}%) and rain increase fungal disease risk"}
        elif humidity >= humidity_threshold:
            return {"level": "medium", "reason": f"High humidity ({humidity}%) may increase disease risk"}
        else:
            return {"level": "low", "reason": "Current weather conditions are not favorable for rapid disease spread"}
    except Exception:
        return None


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
    lat: float = Form(None),
    lon: float = Form(None),
    user: dict = Depends(get_current_user),
    authorization: str = Header(None),
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

    scan_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    weather_risk = get_weather_risk(lat, lon)

    result = {
        "scan_id": scan_id,
        "scan_type": scan_type,
        "disease": knowledge["display_name"],
        "confidence": confidence,
        "severity": knowledge["severity"],
        "low_confidence": low_confidence,
        "symptoms": knowledge["symptoms"],
        "causes": knowledge["causes"],
        "treatment": knowledge["treatment"],
        "prevention": knowledge["prevention"],
        "weather_risk": weather_risk,
        "created_at": created_at,
    }

    # Persist the scan so it shows up in /history
    token = authorization.replace("Bearer ", "") if authorization else None
    client = get_user_supabase_client(token)
    try:
        client.table("disease_scans").insert({
            "id": scan_id,
            "user_id": user_id,
            "crop_id": crop_id,
            "scan_type": scan_type,
            "disease_label": disease_label,
            "disease_display_name": knowledge["display_name"],
            "confidence": confidence,
            "severity": knowledge["severity"],
            "low_confidence": low_confidence,
            "symptoms": knowledge["symptoms"],
            "causes": knowledge["causes"],
            "treatment": knowledge["treatment"],
            "prevention": knowledge["prevention"],
            "weather_snapshot": weather_risk,
            "created_at": created_at,
        }).execute()
    except Exception as e:
        # Don't fail the whole request if saving history fails —
        # the farmer still gets their result even if history write breaks.
        pass

    return {"success": True, "data": result, "error": None}
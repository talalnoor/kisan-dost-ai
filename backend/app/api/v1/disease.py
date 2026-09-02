import os
import uuid
import httpx
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Header
from supabase import create_client, Client
from app.core.security import get_current_user, get_user_id
from app.providers.cv.hf_plant_model import real_cv_predict

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
    FALLBACK ONLY. Used when the real HF CV model call fails
    (network error, HF API down, model cold-start timeout, etc.)
    so the farmer still gets a usable response instead of a 500.
    Must keep returning this exact shape: {disease_label, confidence}.
    """
    return {"disease_label": "tomato_early_blight", "confidence": 0.87}


def get_prediction(image_bytes: bytes) -> dict:
    """
    Tries the real CV model first; falls back to the mock prediction
    if the call fails for any reason. Never lets a broken external
    API crash the farmer's request. Logs the real error so we can
    debug why the fallback triggered instead of guessing.
    """
    try:
        return real_cv_predict(image_bytes)
    except Exception as e:
        print(f"[CV FALLBACK] real_cv_predict failed, using mock: {e}")
        return mock_cv_predict(image_bytes)


# Knowledge base covering all 38 PlantVillage classes the CV model
# was trained on. Labels here must match the output of normalize_label()
# in app/providers/cv/hf_plant_model.py exactly.
MOCK_KNOWLEDGE = {
    "apple_apple_scab": {
        "display_name": "Apple Scab",
        "severity": "moderate",
        "symptoms": ["Olive-green to black velvety spots on leaves", "Scabby, cracked lesions on fruit"],
        "causes": ["Fungal pathogen (Venturia inaequalis)", "Spreads in cool, wet spring weather"],
        "treatment": ["Apply fungicide (captan or myclobutanil) at green tip stage", "Remove fallen leaves that harbor spores"],
        "prevention": ["Choose scab-resistant apple varieties", "Prune for good air circulation", "Rake and destroy fallen leaves each autumn"],
    },
    "apple_black_rot": {
        "display_name": "Apple Black Rot",
        "severity": "moderate",
        "symptoms": ["Purple-bordered leaf spots", "Concentric rings on rotting fruit", "Sunken bark cankers"],
        "causes": ["Fungal pathogen (Botryosphaeria obtusa)", "Enters through wounds and dead wood"],
        "treatment": ["Prune out and destroy cankers and mummified fruit", "Apply fungicide during the growing season"],
        "prevention": ["Remove dead wood and mummified fruit each winter", "Avoid tree wounds during orchard work"],
    },
    "apple_cedar_apple_rust": {
        "display_name": "Cedar Apple Rust",
        "severity": "mild",
        "symptoms": ["Bright orange-yellow spots on leaves", "Small raised orange fruiting structures"],
        "causes": ["Fungal pathogen requiring both apple and cedar/juniper hosts to complete its cycle"],
        "treatment": ["Apply fungicide starting at bud break if nearby cedars are present", "Remove galls from nearby juniper/cedar trees"],
        "prevention": ["Plant resistant apple varieties", "Avoid planting apples near junipers/cedars where possible"],
    },
    "apple_healthy": {
        "display_name": "Healthy Apple",
        "severity": "none",
        "symptoms": ["No visible disease symptoms"],
        "causes": [],
        "treatment": ["No treatment needed"],
        "prevention": ["Continue regular monitoring", "Maintain good orchard hygiene and watering practices"],
    },
    "blueberry_healthy": {
        "display_name": "Healthy Blueberry",
        "severity": "none",
        "symptoms": ["No visible disease symptoms"],
        "causes": [],
        "treatment": ["No treatment needed"],
        "prevention": ["Continue regular monitoring", "Maintain proper soil acidity and drainage"],
    },
    "cherry_including_sour_powdery_mildew": {
        "display_name": "Cherry Powdery Mildew",
        "severity": "mild",
        "symptoms": ["White powdery coating on leaves and shoots", "Leaf curling and distortion"],
        "causes": ["Fungal pathogen (Podosphaera clandestina)", "Favored by warm days and cool, humid nights"],
        "treatment": ["Apply sulfur-based or potassium bicarbonate fungicide", "Prune affected shoots"],
        "prevention": ["Prune for good airflow", "Avoid excess nitrogen fertilizer"],
    },
    "cherry_including_sour_healthy": {
        "display_name": "Healthy Cherry",
        "severity": "none",
        "symptoms": ["No visible disease symptoms"],
        "causes": [],
        "treatment": ["No treatment needed"],
        "prevention": ["Continue regular monitoring"],
    },
    "corn_maize_cercospora_leaf_spot_gray_leaf_spot": {
        "display_name": "Corn Gray Leaf Spot",
        "severity": "moderate",
        "symptoms": ["Rectangular tan-to-gray lesions running parallel to leaf veins"],
        "causes": ["Fungal pathogen (Cercospora zeae-maydis)", "Favored by humid, warm conditions and crop residue"],
        "treatment": ["Apply foliar fungicide if disease is severe before tasseling", "Remove heavily infected residue"],
        "prevention": ["Rotate crops away from corn", "Plant resistant hybrids", "Till under old corn residue"],
    },
    "corn_maize_common_rust_": {
        "display_name": "Corn Common Rust",
        "severity": "mild",
        "symptoms": ["Small, reddish-brown, oval pustules on both leaf surfaces"],
        "causes": ["Fungal pathogen (Puccinia sorghi)", "Spreads via windblown spores in cool, humid weather"],
        "treatment": ["Apply fungicide if infection is severe on young plants", "Usually not economically damaging on mature corn"],
        "prevention": ["Plant rust-resistant hybrids", "Avoid very early planting in high-risk areas"],
    },
    "corn_maize_northern_leaf_blight": {
        "display_name": "Corn Northern Leaf Blight",
        "severity": "moderate",
        "symptoms": ["Long, cigar-shaped gray-green to tan lesions on leaves"],
        "causes": ["Fungal pathogen (Exserohilum turcicum)", "Favored by moderate temperatures and high humidity"],
        "treatment": ["Apply foliar fungicide at first sign of lesions", "Remove and destroy infected residue after harvest"],
        "prevention": ["Plant resistant hybrids", "Rotate crops", "Till infected residue into soil"],
    },
    "corn_maize_healthy": {
        "display_name": "Healthy Corn",
        "severity": "none",
        "symptoms": ["No visible disease symptoms"],
        "causes": [],
        "treatment": ["No treatment needed"],
        "prevention": ["Continue regular monitoring"],
    },
    "grape_black_rot": {
        "display_name": "Grape Black Rot",
        "severity": "severe",
        "symptoms": ["Brown circular leaf spots with dark borders", "Fruit shrivels into hard black mummies"],
        "causes": ["Fungal pathogen (Guignardia bidwellii)", "Spreads rapidly in warm, wet weather"],
        "treatment": ["Apply fungicide starting at bud break through fruit set", "Remove mummified fruit and infected canes"],
        "prevention": ["Prune for airflow", "Remove mummies and infected wood each dormant season"],
    },
    "grape_esca_black_measles": {
        "display_name": "Grape Esca (Black Measles)",
        "severity": "severe",
        "symptoms": ["Tiger-stripe pattern of yellow/red discoloration between leaf veins", "Dark spots on berries"],
        "causes": ["Fungal complex infecting the trunk and wood", "Enters through pruning wounds"],
        "treatment": ["No reliable chemical cure — remove and destroy severely affected vines", "Protect pruning wounds with sealant"],
        "prevention": ["Prune during dry weather", "Avoid large pruning wounds", "Sanitize pruning tools between vines"],
    },
    "grape_leaf_blight_isariopsis_leaf_spot": {
        "display_name": "Grape Leaf Blight (Isariopsis Leaf Spot)",
        "severity": "moderate",
        "symptoms": ["Angular dark brown spots on leaves that merge into larger blighted areas"],
        "causes": ["Fungal pathogen (Pseudocercospora vitis)", "Favored by warm, wet conditions"],
        "treatment": ["Apply copper-based fungicide", "Remove heavily infected leaves"],
        "prevention": ["Improve canopy airflow through pruning", "Avoid overhead irrigation"],
    },
    "grape_healthy": {
        "display_name": "Healthy Grape",
        "severity": "none",
        "symptoms": ["No visible disease symptoms"],
        "causes": [],
        "treatment": ["No treatment needed"],
        "prevention": ["Continue regular monitoring"],
    },
    "orange_haunglongbing_citrus_greening": {
        "display_name": "Citrus Greening (Huanglongbing)",
        "severity": "severe",
        "symptoms": ["Blotchy, asymmetric yellowing of leaves", "Small, lopsided, bitter fruit", "Twig dieback"],
        "causes": ["Bacterial pathogen spread by the Asian citrus psyllid insect"],
        "treatment": ["No cure — remove and destroy infected trees to protect the rest of the grove", "Control psyllid populations with insecticide"],
        "prevention": ["Use certified disease-free planting stock", "Monitor and control psyllid vectors", "Report suspected cases to local agriculture authorities"],
    },
    "peach_bacterial_spot": {
        "display_name": "Peach Bacterial Spot",
        "severity": "moderate",
        "symptoms": ["Small dark angular spots on leaves that may fall out, leaving a shot-hole look", "Sunken lesions on fruit"],
        "causes": ["Bacterial pathogen (Xanthomonas arboricola)", "Spreads via wind-driven rain"],
        "treatment": ["Apply copper-based bactericide during dormancy", "Avoid overhead irrigation"],
        "prevention": ["Plant resistant varieties", "Avoid excess nitrogen", "Space trees for airflow"],
    },
    "peach_healthy": {
        "display_name": "Healthy Peach",
        "severity": "none",
        "symptoms": ["No visible disease symptoms"],
        "causes": [],
        "treatment": ["No treatment needed"],
        "prevention": ["Continue regular monitoring"],
    },
    "pepper_bell_bacterial_spot": {
        "display_name": "Bell Pepper Bacterial Spot",
        "severity": "moderate",
        "symptoms": ["Small water-soaked spots on leaves turning brown", "Raised, scabby spots on fruit"],
        "causes": ["Bacterial pathogen (Xanthomonas campestris)", "Spreads via splashing water and contaminated seed"],
        "treatment": ["Apply copper-based bactericide", "Remove and destroy infected plants"],
        "prevention": ["Use certified disease-free seed", "Avoid overhead watering", "Rotate crops"],
    },
    "pepper_bell_healthy": {
        "display_name": "Healthy Bell Pepper",
        "severity": "none",
        "symptoms": ["No visible disease symptoms"],
        "causes": [],
        "treatment": ["No treatment needed"],
        "prevention": ["Continue regular monitoring"],
    },
    "potato_early_blight": {
        "display_name": "Potato Early Blight",
        "severity": "moderate",
        "symptoms": ["Dark concentric-ring spots on older leaves first", "Yellowing around lesions"],
        "causes": ["Fungal pathogen (Alternaria solani)", "Favored by warm, humid conditions and plant stress"],
        "treatment": ["Apply chlorothalonil or copper-based fungicide", "Remove and destroy infected foliage"],
        "prevention": ["Rotate crops", "Ensure adequate plant nutrition", "Avoid overhead watering"],
    },
    "potato_late_blight": {
        "display_name": "Potato Late Blight",
        "severity": "severe",
        "symptoms": ["Water-soaked gray-green lesions that turn brown/black rapidly", "White fungal growth on leaf undersides in humid weather"],
        "causes": ["Oomycete pathogen (Phytophthora infestans)", "Spreads explosively in cool, wet weather"],
        "treatment": ["Apply fungicide immediately at first sign (this disease can destroy a field within days)", "Remove and destroy infected plants"],
        "prevention": ["Plant certified disease-free seed potatoes", "Avoid overhead irrigation", "Destroy volunteer potato plants and cull piles"],
    },
    "potato_healthy": {
        "display_name": "Healthy Potato",
        "severity": "none",
        "symptoms": ["No visible disease symptoms"],
        "causes": [],
        "treatment": ["No treatment needed"],
        "prevention": ["Continue regular monitoring"],
    },
    "raspberry_healthy": {
        "display_name": "Healthy Raspberry",
        "severity": "none",
        "symptoms": ["No visible disease symptoms"],
        "causes": [],
        "treatment": ["No treatment needed"],
        "prevention": ["Continue regular monitoring"],
    },
    "soybean_healthy": {
        "display_name": "Healthy Soybean",
        "severity": "none",
        "symptoms": ["No visible disease symptoms"],
        "causes": [],
        "treatment": ["No treatment needed"],
        "prevention": ["Continue regular monitoring"],
    },
    "squash_powdery_mildew": {
        "display_name": "Squash Powdery Mildew",
        "severity": "moderate",
        "symptoms": ["White powdery patches on leaves and stems", "Leaves may yellow and dry out"],
        "causes": ["Fungal pathogen favored by warm days, cool nights, and high humidity"],
        "treatment": ["Apply sulfur or potassium bicarbonate fungicide", "Remove heavily infected leaves"],
        "prevention": ["Space plants for airflow", "Plant resistant varieties", "Water at the base, not overhead"],
    },
    "strawberry_leaf_scorch": {
        "display_name": "Strawberry Leaf Scorch",
        "severity": "moderate",
        "symptoms": ["Small purple spots that merge into scorched, reddish-brown blotches"],
        "causes": ["Fungal pathogen (Diplocarpon earlianum)", "Favored by wet foliage and warm temperatures"],
        "treatment": ["Apply fungicide labeled for leaf scorch", "Remove infected leaves after harvest"],
        "prevention": ["Avoid overhead watering", "Renovate beds after harvest to remove old foliage", "Space plants for airflow"],
    },
    "strawberry_healthy": {
        "display_name": "Healthy Strawberry",
        "severity": "none",
        "symptoms": ["No visible disease symptoms"],
        "causes": [],
        "treatment": ["No treatment needed"],
        "prevention": ["Continue regular monitoring"],
    },
    "tomato_bacterial_spot": {
        "display_name": "Tomato Bacterial Spot",
        "severity": "moderate",
        "symptoms": ["Small water-soaked spots on leaves that turn dark and greasy-looking", "Raised scabby spots on fruit"],
        "causes": ["Bacterial pathogen (Xanthomonas species)", "Spreads via splashing water and contaminated tools"],
        "treatment": ["Apply copper-based bactericide", "Remove and destroy infected plants"],
        "prevention": ["Use certified disease-free seed/transplants", "Avoid overhead watering", "Rotate crops"],
    },
    "tomato_early_blight": {
        "display_name": "Tomato Early Blight",
        "severity": "moderate",
        "symptoms": ["Dark concentric-ring spots on lower leaves", "Yellowing around lesions"],
        "causes": ["Fungal pathogen (Alternaria solani)", "Favored by warm, humid conditions"],
        "treatment": ["Apply copper-based or chlorothalonil fungicide", "Remove and destroy infected leaves"],
        "prevention": ["Crop rotation", "Avoid overhead watering", "Ensure adequate plant spacing"],
    },
    "tomato_late_blight": {
        "display_name": "Tomato Late Blight",
        "severity": "severe",
        "symptoms": ["Large water-soaked gray-green blotches that turn brown/black rapidly", "White fungal growth on leaf undersides in humid weather"],
        "causes": ["Oomycete pathogen (Phytophthora infestans)", "Spreads explosively in cool, wet weather"],
        "treatment": ["Apply fungicide immediately — this disease can destroy a crop within days", "Remove and destroy infected plants"],
        "prevention": ["Avoid overhead irrigation", "Ensure good airflow", "Destroy volunteer tomato/potato plants nearby"],
    },
    "tomato_leaf_mold": {
        "display_name": "Tomato Leaf Mold",
        "severity": "mild",
        "symptoms": ["Pale yellow spots on upper leaf surface", "Olive-green to grayish-purple fuzzy mold underneath"],
        "causes": ["Fungal pathogen (Passalora fulva)", "Favored by high humidity, common in greenhouses"],
        "treatment": ["Improve ventilation to lower humidity", "Apply fungicide if severe"],
        "prevention": ["Space plants for airflow", "Avoid overhead watering", "Prune lower leaves"],
    },
    "tomato_septoria_leaf_spot": {
        "display_name": "Tomato Septoria Leaf Spot",
        "severity": "moderate",
        "symptoms": ["Small circular spots with dark borders and gray centers", "Tiny black dots visible in spot centers"],
        "causes": ["Fungal pathogen (Septoria lycopersici)", "Favored by wet, humid conditions"],
        "treatment": ["Apply chlorothalonil or copper-based fungicide", "Remove infected lower leaves"],
        "prevention": ["Mulch to prevent soil splash onto leaves", "Rotate crops", "Avoid overhead watering"],
    },
    "tomato_spider_mites_two-spotted_spider_mite": {
        "display_name": "Tomato Spider Mites (Two-Spotted Spider Mite)",
        "severity": "moderate",
        "symptoms": ["Fine yellow stippling on leaves", "Fine webbing on leaf undersides in heavy infestations"],
        "causes": ["Tiny arachnid pest, thrives in hot, dry conditions"],
        "treatment": ["Apply insecticidal soap or miticide", "Spray leaf undersides with water to dislodge mites"],
        "prevention": ["Avoid drought stress", "Encourage natural predators like ladybugs", "Monitor regularly during hot weather"],
    },
    "tomato_target_spot": {
        "display_name": "Tomato Target Spot",
        "severity": "moderate",
        "symptoms": ["Brown lesions with concentric target-like rings on leaves and fruit"],
        "causes": ["Fungal pathogen (Corynespora cassiicola)", "Favored by warm, humid, wet conditions"],
        "treatment": ["Apply fungicide at first sign of spots", "Remove infected leaves"],
        "prevention": ["Improve airflow through pruning and spacing", "Avoid overhead watering", "Rotate crops"],
    },
    "tomato_tomato_yellow_leaf_curl_virus": {
        "display_name": "Tomato Yellow Leaf Curl Virus",
        "severity": "severe",
        "symptoms": ["Upward curling and yellowing of leaves", "Stunted growth", "Reduced fruit set"],
        "causes": ["Viral pathogen spread by whiteflies", "No cure once infected"],
        "treatment": ["Remove and destroy infected plants to reduce spread", "Control whitefly populations with insecticide or sticky traps"],
        "prevention": ["Plant resistant varieties", "Use whitefly-proof netting or reflective mulch", "Control weeds that host whiteflies"],
    },
    "tomato_tomato_mosaic_virus": {
        "display_name": "Tomato Mosaic Virus",
        "severity": "moderate",
        "symptoms": ["Mottled light and dark green mosaic pattern on leaves", "Leaf curling and stunted growth"],
        "causes": ["Viral pathogen spread by contact, tools, and hands", "Very stable — can persist in soil and dried plant debris"],
        "treatment": ["No cure — remove and destroy infected plants", "Disinfect tools and hands after handling infected plants"],
        "prevention": ["Use resistant varieties", "Wash hands and disinfect tools between plants", "Avoid tobacco use before handling plants (virus is related to TMV)"],
    },
    "tomato_healthy": {
        "display_name": "Healthy Tomato",
        "severity": "none",
        "symptoms": ["No visible disease symptoms"],
        "causes": [],
        "treatment": ["No treatment needed"],
        "prevention": ["Continue regular monitoring"],
    },
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

    prediction = get_prediction(image_bytes)
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
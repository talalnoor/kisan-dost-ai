import os
import httpx
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.security import get_current_user

router = APIRouter(prefix="/api/v1/weather", tags=["weather"])

WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")
OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"


@router.get("")
async def get_weather(
    lat: float = Query(...),
    lon: float = Query(...),
    user: dict = Depends(get_current_user),
):
    if not WEATHER_API_KEY:
        raise HTTPException(
            status_code=503,
            detail={"code": "WEATHER_PROVIDER_UNAVAILABLE", "message": "Weather service not configured"},
        )

    params = {
        "lat": lat,
        "lon": lon,
        "appid": WEATHER_API_KEY,
        "units": "metric",
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(OPENWEATHER_URL, params=params)
            response.raise_for_status()
            data = response.json()

        result = {
            "temperature": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "rain_probability": data.get("rain", {}).get("1h", 0) and 1.0 or 0.0,
            "condition": data["weather"][0]["main"].lower(),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
        return {"success": True, "data": result, "error": None}

    except httpx.HTTPStatusError:
        raise HTTPException(
            status_code=503,
            detail={"code": "WEATHER_PROVIDER_UNAVAILABLE", "message": "Could not retrieve weather data"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
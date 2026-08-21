"""
Pydantic models matching the Supabase schema.
See docs/database/database-schema.md for the source-of-truth table definitions.
"""
from datetime import date, datetime
from typing import Optional, Literal
from uuid import UUID
from pydantic import BaseModel
class Profile(BaseModel):
    id: UUID
    full_name: Optional[str] = None
    preferred_language: Literal["en", "ur"] = "en"
    region: Optional[str] = None
    created_at: datetime


class CropCreate(BaseModel):
    crop_type: str
    planted_date: Optional[date] = None
    stage: Optional[str] = None


class Crop(CropCreate):
    id: UUID
    user_id: UUID
    created_at: datetime


class WeatherRisk(BaseModel):
    level: Literal["low", "medium", "high"]
    reason: str


class DiseaseScan(BaseModel):
    scan_id: UUID
    scan_type: Literal["disease", "pest"] = "disease"
    disease: str
    confidence: float
    severity: str
    low_confidence: bool = False
    symptoms: list[str] = []
    causes: list[str] = []
    treatment: list[str] = []
    prevention: list[str] = []
    weather_risk: Optional[WeatherRisk] = None
    created_at: datetime


class ChatRequest(BaseModel):
    session_id: Optional[UUID] = None
    message: str
    language: Literal["en", "ur"] = "en"
    crop_id: Optional[UUID] = None


class ChatResponse(BaseModel):
    session_id: UUID
    reply: str
    language: Literal["en", "ur"]
    created_at: datetime


class WeatherData(BaseModel):
    temperature: float
    humidity: int
    rain_probability: float
    condition: str
    fetched_at: datetime


class TaskCreate(BaseModel):
    crop_id: Optional[UUID] = None
    task_type: str
    due_date: Optional[date] = None


class Task(TaskCreate):
    id: UUID
    user_id: UUID
    status: Literal["pending", "completed", "skipped"] = "pending"
    created_at: datetime
import os
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from openai import OpenAI
from supabase import create_client, Client
from app.core.security import get_current_user, get_user_id

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

supabase_url = os.environ.get("SUPABASE_URL")
supabase_anon_key = os.environ.get("SUPABASE_ANON_KEY")

DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY")
DASHSCOPE_BASE_URL = os.environ.get(
    "DASHSCOPE_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
)

SYSTEM_PROMPT_EN = (
    "You are Kisan Dost AI, a knowledgeable and friendly farming assistant for farmers in Pakistan. "
    "Answer practically about crops, diseases, fertilizers, irrigation, soil, and weather-related farming "
    "decisions. Be concise, farmer-friendly, and honest when you're unsure rather than guessing. "
    "STRICT RULE: never state a specific fertilizer/chemical dosage number, percentage, or quantity "
    "(e.g. do not say '20-40 kg per acre' or '0.5% solution'). Instead, describe the general approach "
    "and always tell the farmer to confirm exact amounts with their local agricultural extension office "
    "or product label before applying anything."
)

SYSTEM_PROMPT_UR = (
    "آپ کسان دوست AI ہیں، پاکستان کے کسانوں کے لیے ایک باخبر اور دوستانہ زرعی معاون۔ "
    "فصلوں، بیماریوں، کھادوں، آبپاشی، مٹی اور موسم سے متعلق فیصلوں کے بارے میں عملی جواب دیں۔ "
    "مختصر اور واضح رہیں، اور غیر یقینی صورت میں اندازہ لگانے کی بجائے ایمانداری سے بتائیں۔ "
    "سخت اصول: کبھی بھی کھاد یا کیمیکل کی مخصوص مقدار، فیصد یا وزن نہ بتائیں (مثلاً '20-40 کلو فی ایکڑ' یا '0.5%' نہ کہیں)۔ "
    "اس کی بجائے عمومی طریقہ بتائیں اور ہمیشہ کسان کو مقامی زرعی محکمہ یا پروڈکٹ لیبل سے صحیح مقدار معلوم کرنے کا مشورہ دیں۔"
)


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    language: str = "en"
    crop_id: Optional[str] = None


def get_user_supabase_client(token: str) -> Client:
    client = create_client(supabase_url, supabase_anon_key)
    client.postgrest.auth(token)
    return client


def call_qwen(message: str, language: str) -> str:
    client = OpenAI(api_key=DASHSCOPE_API_KEY, base_url=DASHSCOPE_BASE_URL)
    system_prompt = SYSTEM_PROMPT_UR if language == "ur" else SYSTEM_PROMPT_EN

    response = client.chat.completions.create(
        model="qwen-plus",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ],
    )
    return response.choices[0].message.content


FALLBACK_REPLY_EN = (
    "I'm having trouble reaching the assistant right now. Please try again in a moment, "
    "or check your latest disease scan results and weather info in the meantime."
)
FALLBACK_REPLY_UR = (
    "ابھی معاون سے رابطہ کرنے میں مسئلہ ہو رہا ہے۔ براہ کرم تھوڑی دیر بعد دوبارہ کوشش کریں۔"
)


@router.post("")
def chat(
    payload: ChatRequest,
    user: dict = Depends(get_current_user),
    authorization: str = Header(None),
):
    user_id = get_user_id(user)
    token = authorization.replace("Bearer ", "") if authorization else None
    client = get_user_supabase_client(token)

    session_id = payload.session_id
    if not session_id:
        session_result = client.table("chat_sessions").insert({
            "user_id": user_id,
            "crop_id": payload.crop_id,
        }).execute()
        session_id = session_result.data[0]["id"]

    try:
        reply = call_qwen(payload.message, payload.language)
    except Exception:
        reply = FALLBACK_REPLY_UR if payload.language == "ur" else FALLBACK_REPLY_EN

    created_at = datetime.now(timezone.utc).isoformat()

    try:
        client.table("chat_messages").insert({
            "session_id": session_id,
            "role": "user",
            "content": payload.message,
            "language": payload.language,
        }).execute()
        client.table("chat_messages").insert({
            "session_id": session_id,
            "role": "assistant",
            "content": reply,
            "language": payload.language,
        }).execute()
    except Exception:
        pass  # don't fail the reply just because history logging failed

    return {
        "success": True,
        "data": {
            "session_id": session_id,
            "reply": reply,
            "language": payload.language,
            "created_at": created_at,
        },
        "error": None,
    }
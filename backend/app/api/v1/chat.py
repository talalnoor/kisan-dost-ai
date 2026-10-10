import os
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from openai import OpenAI
from supabase import create_client, Client
from dotenv import load_dotenv
from app.core.security import get_current_user, get_user_id

load_dotenv()

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

supabase_url = os.environ.get("SUPABASE_URL")
supabase_anon_key = os.environ.get("SUPABASE_ANON_KEY")

# .strip() guards against stray spaces/quotes copied into .env or Railway variables
DASHSCOPE_API_KEY = (os.environ.get("DASHSCOPE_API_KEY") or "").strip().strip("\"'").strip()
DASHSCOPE_BASE_URL = (
    os.environ.get("DASHSCOPE_BASE_URL") or "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
).strip().strip("\"'").strip().rstrip("/")
DASHSCOPE_MODEL = (os.environ.get("DASHSCOPE_MODEL") or "qwen-plus").strip()

# In development the real error is returned in the response ("debug") to make fixing setup easy.
IS_DEV = (os.environ.get("ENVIRONMENT") or "").strip().lower() == "development"
MAX_HISTORY = 10  # previous messages sent to the model so it remembers the conversation

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


def get_history(client: Client, session_id: str) -> list:
    """Last few messages of this conversation, oldest first. Never raises."""
    try:
        result = (
            client.table("chat_messages")
            .select("role, content")
            .eq("session_id", session_id)
            .order("created_at", desc=True)
            .limit(MAX_HISTORY)
            .execute()
        )
        rows = list(reversed(result.data or []))
        return [{"role": r["role"], "content": r["content"]} for r in rows if r.get("content")]
    except Exception as e:
        print(f"[CHAT] could not load history: {e}")
        return []


def call_qwen(message: str, language: str, history: Optional[list] = None) -> str:
    if not DASHSCOPE_API_KEY:
        raise RuntimeError("DASHSCOPE_API_KEY is empty or not set")

    client = OpenAI(api_key=DASHSCOPE_API_KEY, base_url=DASHSCOPE_BASE_URL, timeout=30, max_retries=1)
    system_prompt = SYSTEM_PROMPT_UR if language == "ur" else SYSTEM_PROMPT_EN

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history or [])
    messages.append({"role": "user", "content": message})

    response = client.chat.completions.create(model=DASHSCOPE_MODEL, messages=messages)
    reply = response.choices[0].message.content
    if not reply or not reply.strip():
        raise RuntimeError("Qwen returned an empty reply")
    return reply.strip()


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
    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    language = payload.language if payload.language in ("en", "ur") else "en"

    user_id = get_user_id(user)
    token = authorization.replace("Bearer ", "") if authorization else None
    client = get_user_supabase_client(token)

    session_id = payload.session_id
    history = []
    if session_id:
        history = get_history(client, session_id)
    else:
        try:
            session_result = client.table("chat_sessions").insert({
                "user_id": user_id,
                "crop_id": payload.crop_id or None,
            }).execute()
            session_id = session_result.data[0]["id"]
        except Exception as e:
            print(f"[CHAT] could not create chat session: {e}")
            raise HTTPException(status_code=500, detail=f"Could not start chat session: {e}")

    debug_error = None
    try:
        reply = call_qwen(message, language, history)
    except Exception as e:
        debug_error = f"{type(e).__name__}: {e}"
        print(f"[CHAT FALLBACK] Qwen call failed ({debug_error}). Check DASHSCOPE_API_KEY / DASHSCOPE_BASE_URL / DASHSCOPE_MODEL")
        reply = FALLBACK_REPLY_UR if language == "ur" else FALLBACK_REPLY_EN

    created_at = datetime.now(timezone.utc).isoformat()

    # Only save real answers, so a fallback message never pollutes the conversation history
    if debug_error is None:
        try:
            client.table("chat_messages").insert([
                {"session_id": session_id, "role": "user", "content": message, "language": language},
                {"session_id": session_id, "role": "assistant", "content": reply, "language": language},
            ]).execute()
        except Exception as e:
            print(f"[CHAT] could not save chat history: {e}")

    data = {
        "session_id": session_id,
        "reply": reply,
        "language": language,
        "created_at": created_at,
    }
    if debug_error and IS_DEV:
        data["debug"] = debug_error

    return {"success": True, "data": data, "error": None}
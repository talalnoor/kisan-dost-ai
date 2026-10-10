import os
import re
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


def _clean(value: str) -> str:
    # guards against stray spaces/quotes copied into .env or Railway variables
    return (value or "").strip().strip("\"'").strip()


DASHSCOPE_API_KEY = _clean(os.environ.get("DASHSCOPE_API_KEY"))
DASHSCOPE_BASE_URL = _clean(
    os.environ.get("DASHSCOPE_BASE_URL") or "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
).rstrip("/")
DASHSCOPE_MODEL = _clean(os.environ.get("DASHSCOPE_MODEL")) or "qwen-plus"
# Used only when the main model is overloaded or times out
DASHSCOPE_FALLBACK_MODEL = _clean(os.environ.get("DASHSCOPE_FALLBACK_MODEL")) or "gemini-3.5-flash-lite"
REQUEST_TIMEOUT = 40  # seconds per model attempt

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
    "آپ کسان دوست ہیں، پاکستان کے کسانوں کے لیے ایک باخبر اور دوستانہ زرعی معاون۔ "
    "فصلوں، بیماریوں، کھادوں، آبپاشی، مٹی اور موسم سے متعلق فیصلوں کے بارے میں عملی جواب دیں۔ "
    "مختصر اور واضح رہیں، اور غیر یقینی صورت میں اندازہ لگانے کی بجائے ایمانداری سے بتائیں۔ "
    "سخت اصول: کبھی بھی کھاد یا کیمیکل کی مخصوص مقدار، فیصد یا وزن نہ بتائیں۔ "
    "اس کی بجائے عمومی طریقہ بتائیں اور ہمیشہ کسان کو مقامی زرعی محکمے یا پروڈکٹ لیبل سے صحیح مقدار معلوم کرنے کا مشورہ دیں۔ "
    "زبان کا اصول: صرف اردو (عربی رسم الخط) میں لکھیں۔ کوئی بھی انگریزی لفظ، قوسین میں انگریزی نام، یا ہندی، گرمکھی، تامل کے حروف ہرگز استعمال نہ کریں۔ "
    "بیماریوں کے نام بھی اردو میں لکھیں، مثلاً اگیتا جھلساؤ اور پچھیتا جھلساؤ۔ "
    "ہر چیز کے لیے آسان اردو لفظ استعمال کریں، مثلاً پھپھوندی، پھپھوندی کش دوا، کھاد۔ "
    "فارمیٹ کا اصول: نمبر والی فہرست، ہندسے، ستارے، ہیش یا بلٹ نہ بنائیں۔ جواب کو چھوٹے سادہ جملوں اور چھوٹے پیراگرافوں میں لکھیں، "
    "اور ترتیب بتانے کے لیے لفظ جیسے سب سے پہلے، اس کے بعد، پھر، آخر میں استعمال کریں۔"
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


def clean_urdu_reply(text: str) -> str:
    """Makes an Urdu answer safe for the speaker: no English words, digits, list numbers or markdown marks."""
    original = text
    # remove list numbers like "1." or "2)" at the start of a line
    text = re.sub(r"(?m)^\s*[0-9۰-۹]+\s*[\.\)\-:،]\s*", "", text)
    # remove bullets and markdown marks
    text = re.sub(r"(?m)^\s*[\*\-•]\s+", "", text)
    text = text.replace("**", "").replace("*", "").replace("#", "")
    # remove every English word and every digit
    text = re.sub(r"[A-Za-z]+(?:[\-'][A-Za-z]+)*", "", text)
    text = re.sub(r"[0-9]+(?:[\.,%][0-9]+)?%?", "", text)
    # remove brackets left empty and tidy spacing/punctuation
    text = re.sub(r"[\(\[]\s*[\)\]]", "", text)
    text = re.sub(r"[ \t]+([،۔:؟!])", r"\1", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text or original


def call_qwen(message: str, language: str, history: Optional[list] = None) -> str:
    """Tries the main model first, then the fallback model if the main one fails."""
    if not DASHSCOPE_API_KEY:
        raise RuntimeError("DASHSCOPE_API_KEY is empty or not set")

    client = OpenAI(
        api_key=DASHSCOPE_API_KEY,
        base_url=DASHSCOPE_BASE_URL,
        timeout=REQUEST_TIMEOUT,
        max_retries=0,
    )
    system_prompt = SYSTEM_PROMPT_UR if language == "ur" else SYSTEM_PROMPT_EN

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history or [])
    messages.append({"role": "user", "content": message})

    models = [DASHSCOPE_MODEL]
    if DASHSCOPE_FALLBACK_MODEL and DASHSCOPE_FALLBACK_MODEL != DASHSCOPE_MODEL:
        models.append(DASHSCOPE_FALLBACK_MODEL)

    last_error = None
    for model in models:
        try:
            response = client.chat.completions.create(model=model, messages=messages)
            reply = response.choices[0].message.content
            if not reply or not reply.strip():
                raise RuntimeError(f"{model} returned an empty reply")
            if model != DASHSCOPE_MODEL:
                print(f"[CHAT] answered by fallback model {model}")
            reply = reply.strip()
            if language == "ur":
                reply = clean_urdu_reply(reply)
            return reply
        except Exception as e:
            last_error = e
            print(f"[CHAT] model {model} failed: {type(e).__name__}: {e}")

    raise last_error


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
import os
from fastapi import FastAPI, Depends
from dotenv import load_dotenv
from supabase import create_client, Client
from app.core.security import get_current_user, get_user_id

load_dotenv()

app = FastAPI(title="Kisan Dost AI API")

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_ANON_KEY")
supabase: Client = create_client(supabase_url, supabase_key)


@app.get("/")
def root():
    return {"status": "ok", "message": "Kisan Dost AI backend is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/health/supabase")
def health_supabase():
    try:
        supabase.auth.get_session()
        return {"status": "connected", "supabase_url": supabase_url}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@app.get("/api/v1/auth/me")
def get_me(user: dict = Depends(get_current_user)):
    """
    Protected test endpoint. Requires a valid Supabase JWT in the
    Authorization header. Returns the authenticated user's ID.
    """
    return {"user_id": get_user_id(user), "email": user.get("email")}
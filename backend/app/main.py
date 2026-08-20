import os
from fastapi import FastAPI
from dotenv import load_dotenv
from supabase import create_client, Client

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
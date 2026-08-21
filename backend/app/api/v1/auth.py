
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

supabase_url = os.environ.get("SUPABASE_URL")
supabase_anon_key = os.environ.get("SUPABASE_ANON_KEY")
supabase_service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client = create_client(supabase_url, supabase_anon_key)
supabase_admin: Client = create_client(supabase_url, supabase_service_key)


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    preferred_language: str = "en"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/signup")
def signup(payload: SignupRequest):
    try:
        result = supabase.auth.sign_up({
            "email": payload.email,
            "password": payload.password,
        })

        if result.user is None:
            raise HTTPException(status_code=400, detail="Signup failed")

        # Create the matching profile row using the service role key
        # (bypasses RLS since this is a trusted server-side operation)
        supabase_admin.table("profiles").insert({
            "id": result.user.id,
            "full_name": payload.full_name,
            "preferred_language": payload.preferred_language,
        }).execute()

        return {
            "user_id": result.user.id,
            "email": result.user.email,
            "session": {
                "access_token": result.session.access_token if result.session else None,
                "refresh_token": result.session.refresh_token if result.session else None,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
def login(payload: LoginRequest):
    try:
        result = supabase.auth.sign_in_with_password({
            "email": payload.email,
            "password": payload.password,
        })

        return {
            "user_id": result.user.id,
            "email": result.user.email,
            "access_token": result.session.access_token,
            "refresh_token": result.session.refresh_token,
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid email or password")
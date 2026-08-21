import os
from fastapi import APIRouter, Depends, HTTPException, Header
from supabase import create_client, Client
from app.core.security import get_current_user, get_user_id
from app.models.schemas import CropCreate

router = APIRouter(prefix="/api/v1/crops", tags=["crops"])

supabase_url = os.environ.get("SUPABASE_URL")
supabase_anon_key = os.environ.get("SUPABASE_ANON_KEY")


def get_user_supabase_client(token: str) -> Client:
    """
    Creates a Supabase client authenticated as the specific user,
    so RLS policies apply correctly (not the anon/service role).
    """
    client = create_client(supabase_url, supabase_anon_key)
    client.postgrest.auth(token)
    return client


@router.get("")
def list_crops(user: dict = Depends(get_current_user), authorization: str = Header(None)):
    user_id = get_user_id(user)
    token = authorization.replace("Bearer ", "") if authorization else None
    client = get_user_supabase_client(token)

    try:
        result = client.table("crops").select("*").eq("user_id", user_id).execute()
        return {"success": True, "data": {"crops": result.data}, "error": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", status_code=201)
def create_crop(
    payload: CropCreate,
    user: dict = Depends(get_current_user),
    authorization: str = Header(None),
):
    user_id = get_user_id(user)
    token = authorization.replace("Bearer ", "") if authorization else None
    client = get_user_supabase_client(token)

    try:
        row = payload.model_dump(mode="json")
        row["user_id"] = user_id
        result = client.table("crops").insert(row).execute()
        return {"success": True, "data": result.data[0], "error": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
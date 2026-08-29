import os
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from supabase import create_client, Client
from app.core.security import get_current_user, get_user_id
from app.models.schemas import TaskCreate

router = APIRouter(prefix="/api/v1", tags=["history-tasks"])

supabase_url = os.environ.get("SUPABASE_URL")
supabase_anon_key = os.environ.get("SUPABASE_ANON_KEY")


def get_user_supabase_client(token: str) -> Client:
    client = create_client(supabase_url, supabase_anon_key)
    client.postgrest.auth(token)
    return client


@router.get("/history")
def get_history(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: dict = Depends(get_current_user),
    authorization: str = Header(None),
):
    user_id = get_user_id(user)
    token = authorization.replace("Bearer ", "") if authorization else None
    client = get_user_supabase_client(token)

    try:
        result = (
            client.table("disease_scans")
            .select("*", count="exact")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return {
            "success": True,
            "data": {"scans": result.data, "total": result.count},
            "error": None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks")
def list_tasks(user: dict = Depends(get_current_user), authorization: str = Header(None)):
    user_id = get_user_id(user)
    token = authorization.replace("Bearer ", "") if authorization else None
    client = get_user_supabase_client(token)

    try:
        result = client.table("farming_tasks").select("*").eq("user_id", user_id).execute()
        return {"success": True, "data": {"tasks": result.data}, "error": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks", status_code=201)
def create_task(
    payload: TaskCreate,
    user: dict = Depends(get_current_user),
    authorization: str = Header(None),
):
    user_id = get_user_id(user)
    token = authorization.replace("Bearer ", "") if authorization else None
    client = get_user_supabase_client(token)

    try:
        row = payload.model_dump(mode="json")
        row["user_id"] = user_id
        result = client.table("farming_tasks").insert(row).execute()
        return {"success": True, "data": result.data[0], "error": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
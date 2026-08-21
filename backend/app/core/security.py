import os
import jwt
from fastapi import Header, HTTPException
from jwt import PyJWTError

SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET")


def get_current_user(authorization: str = Header(None)) -> dict:
    """
    Verifies the Supabase JWT sent in the Authorization header.
    Use as a FastAPI dependency: user = Depends(get_current_user)
    Returns the decoded token payload, including 'sub' (the user's UUID).
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization.replace("Bearer ", "")

    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
        return payload
    except PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {str(e)}")


def get_user_id(user: dict) -> str:
    """Extracts the user's UUID from a decoded token payload."""
    return user["sub"]
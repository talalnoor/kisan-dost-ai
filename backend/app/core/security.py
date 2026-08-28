import os
import jwt
from jwt import PyJWKClient, PyJWTError
from fastapi import Header, HTTPException
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
JWKS_URL = f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"

_jwks_client = PyJWKClient(JWKS_URL)


def get_current_user(authorization: str = Header(None)) -> dict:
    """
    Verifies the Supabase JWT sent in the Authorization header,
    using Supabase's public JWKS (supports ES256-signed tokens).
    Use as a FastAPI dependency: user = Depends(get_current_user)
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization.replace("Bearer ", "")

    try:
        signing_key = _jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256", "RS256"],
            audience="authenticated",
        )
        return payload
    except PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {str(e)}")


def get_user_id(user: dict) -> str:
    """Extracts the user's UUID from a decoded token payload."""
    return user["sub"]
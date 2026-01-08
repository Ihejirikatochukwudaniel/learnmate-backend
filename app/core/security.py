import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import requests

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # Service role key if needed

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Validates Supabase JWT and returns user info.
    If Authorization header is missing or invalid, raises 401.
    """
    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme"
        )

    token = credentials.credentials

    # Verify token with Supabase REST endpoint
    response = requests.get(
        f"{SUPABASE_URL}/auth/v1/user",
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    user_data = response.json()
    return {
        "id": user_data.get("id"),
        "email": user_data.get("email"),
        "role": user_data.get("role", "student")  # optional role field
    }

# Dummy testing fallback
def get_dummy_user():
    return {
        "id": "test-user-id",
        "email": "test@example.com",
        "role": "student"
    }

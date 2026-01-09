import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.db.supabase import supabase

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

    try:
        # Verify token with Supabase client
        user_response = supabase.auth.get_user(token)

        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )

        user_data = user_response.user

        # Get profile data to include role and full_name
        profile_result = supabase.table("profiles").select("*").eq("id", user_data.id).execute()

        if not profile_result.data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User profile not found"
            )

        profile = profile_result.data[0]
        role = profile.get("role")
        full_name = profile.get("full_name")

        return {
            "id": str(user_data.id),
            "email": user_data.email,
            "role": role,
            "full_name": full_name
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

# Dummy testing fallback
def get_dummy_user():
    return {
        "id": "test-user-id",
        "email": "test@example.com",
        "role": "student",
        "full_name": "Test User"
    }

import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.db.supabase import supabase

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Validates Supabase JWT token and returns user profile information.

    Args:
        credentials: HTTP authorization credentials containing the Bearer token

    Returns:
        dict: User profile data with id, email, role, and full_name

    Raises:
        HTTPException: 401 if token is invalid, expired, or user profile not found
    """
    # Validate authorization scheme
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing authorization header. Use 'Bearer <token>'"
        )

    token = credentials.credentials

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing access token"
        )

    try:
        # Verify and decode the JWT token with Supabase
        user_response = supabase.auth.get_user(token)

        if not user_response or not hasattr(user_response, 'user') or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )

        user_data = user_response.user
        user_id = str(user_data.id)

        # Fetch fresh user profile from profiles table
        profile_response = supabase.table("profiles").select("id, full_name, email, role").eq("id", user_id).execute()

        if not profile_response.data or len(profile_response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User profile not found. Please complete your profile setup."
            )

        profile = profile_response.data[0]

        # Ensure required fields are present
        if not profile.get("role"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User profile incomplete. Role information missing."
            )

        return {
            "id": profile["id"],
            "email": profile["email"],
            "role": profile["role"],
            "full_name": profile.get("full_name")
        }

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Catch any other exceptions (network issues, Supabase errors, etc.)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed. Please check your token and try again."
        )

# Dummy testing fallback (only used when USE_REAL_JWT=false)
def get_dummy_user():
    """
    Returns dummy user data for testing purposes.
    Only used when USE_REAL_JWT is set to false.
    """
    return {
        "id": "test-user-id",
        "email": "test@example.com",
        "role": "student",
        "full_name": "Test User"
    }

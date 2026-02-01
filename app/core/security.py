import os
from fastapi import Depends, HTTPException, status, Query
from app.db.supabase import supabase
from app.core.config import settings
from uuid import UUID

def get_current_user(user_id: str = Query(..., description="User UUID for authentication")):
    """
    Fetches user profile information by UUID.

    Args:
        user_id: User UUID from query parameter

    Returns:
        dict: User profile data with id, email, role, and full_name

    Raises:
        HTTPException: 401 if user profile not found
    """
    try:
        # Validate UUID format
        try:
            UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid UUID format"
            )

        # Fetch user profile from profiles table
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
            detail="Authentication failed. Please check your UUID and try again."
        )

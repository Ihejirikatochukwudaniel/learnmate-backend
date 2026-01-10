from fastapi import APIRouter, HTTPException
from app.db.supabase import supabase
from app.schemas.auth import UserResponse, UserIdRequest

router = APIRouter(tags=["Auth"])

@router.post("/me", response_model=UserResponse)
def get_user_profile_by_id(request: UserIdRequest):
    """
    Get user profile information by user ID.

    Accepts user_id in request body and returns user data including:
    - id: User's unique identifier
    - full_name: User's full name
    - email: User's email address
    - role: User's role (admin, teacher, student)

    Returns 404 if user profile not found.
    """
    user_id = request.user_id

    try:
        # Fetch user profile from profiles table using the provided user_id
        profile_response = supabase.table("profiles").select("id, full_name, role").eq("id", user_id).execute()

        if not profile_response.data or len(profile_response.data) == 0:
            raise HTTPException(
                status_code=404,
                detail="User profile not found"
            )

        profile = profile_response.data[0]

        # Ensure required fields are present
        if not profile.get("role"):
            raise HTTPException(
                status_code=404,
                detail="User profile incomplete. Role information missing."
            )

        # Add email as null since it's not in the database
        profile["email"] = None
        return UserResponse(**profile)

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Catch any other exceptions (network issues, Supabase errors, etc.)
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch user profile. Please try again."
        )

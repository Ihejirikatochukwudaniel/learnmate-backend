from fastapi import APIRouter, Depends, HTTPException
from app.core.security import get_current_user
from app.schemas.auth import UserResponse

router = APIRouter(tags=["Auth"])

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user's profile information.

    Returns user data including:
    - id: User's unique identifier
    - full_name: User's full name
    - email: User's email address
    - role: User's role (admin, teacher, student)

    Requires authentication via Bearer token.
    """
    try:
        # The user data is already fetched and validated by get_current_user dependency
        return UserResponse(**current_user)

    except Exception as e:
        # Catch any unexpected exceptions
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch user profile. Please try again."
        )

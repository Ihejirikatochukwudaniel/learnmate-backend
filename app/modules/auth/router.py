from fastapi import APIRouter, Depends, HTTPException
from app.core.security import get_current_user
from app.schemas.auth import UserResponse

router = APIRouter(tags=["Auth"])

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(user: dict = Depends(get_current_user)):
    """
    Get current authenticated user's profile information.

    Returns user data including:
    - id: User's unique identifier
    - full_name: User's full name
    - email: User's email address
    - role: User's role (admin, teacher, student)

    Requires valid Supabase JWT token in Authorization header.
    Returns 401 for invalid, expired, or missing tokens.
    """
    return UserResponse(**user)

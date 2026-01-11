from fastapi import APIRouter, HTTPException, Depends
from app.db.supabase import supabase
from app.schemas.auth import UserResponse, UserIdRequest, TokenResponse
from app.core.security import get_current_user
from pydantic import BaseModel

class LoginRequest(BaseModel):
    email: str
    password: str

router = APIRouter(tags=["Auth"])

@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest):
    """
    Login with email and password to get JWT token.
    Uses Supabase authentication.
    """
    try:
        # Authenticate with Supabase
        auth_response = supabase.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })

        if not auth_response.user or not auth_response.session:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        # Return the access token
        return TokenResponse(access_token=auth_response.session.access_token)

    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail="Login failed. Please check your credentials."
        )

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(user: dict = Depends(get_current_user)):
    """
    Get current authenticated user's profile information.

    Returns user data including:
    - id: User's unique identifier
    - email: User's email address
    - role: User's role (admin, teacher, student)
    - full_name: User's full name

    Requires valid JWT token in Authorization header.
    """
    return UserResponse(**user)

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

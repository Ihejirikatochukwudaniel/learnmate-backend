from fastapi import APIRouter, HTTPException, Depends, Query
from app.db.supabase import supabase
from app.schemas.auth import UserResponse, UserIdRequest, LoginResponse
from app.core.security import get_current_user
from pydantic import BaseModel

class LoginRequest(BaseModel):
    email: str
    password: str

router = APIRouter(tags=["Auth"])

@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    """
    Login with email and password to get user ID.
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

        # Return the user ID directly
        return LoginResponse(user_id=str(auth_response.user.id))

    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail="Login failed. Please check your credentials."
        )

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(user_id: str = Query(..., description="User ID for authentication")):
    """
    Get current authenticated user's profile information.

    Requires user_id as query parameter.
    Returns user data including:
    - id: User's unique identifier
    - email: User's email address
    - role: User's role (admin, teacher, student)
    - full_name: User's full name
    """
    user = get_current_user(user_id)
    return UserResponse(**user)

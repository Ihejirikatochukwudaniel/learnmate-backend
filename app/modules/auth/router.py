from fastapi import APIRouter, HTTPException, Depends, Query, Header
from app.db.supabase import supabase
from app.schemas.auth import UserResponse, UserIdRequest, LoginResponse
from app.core.security import get_current_user
from app.core.session_cache import create_session, get_user_id_for_token
from pydantic import BaseModel
from typing import Optional

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

        # Create a short-lived server-side session token so the client can
        # authenticate subsequent requests without passing raw UUID every time.
        user_id = str(auth_response.user.id)
        token = create_session(user_id)

        return LoginResponse(user_id=user_id, token=token)

    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail="Login failed. Please check your credentials."
        )

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(user_id: Optional[str] = Query(None, description="User ID for authentication"),
                             authorization: Optional[str] = Header(None, alias="Authorization")):
    """
    Get current authenticated user's profile information.

    Requires user_id as query parameter.
    Returns user data including:
    - id: User's unique identifier
    - email: User's email address
    - role: User's role (admin, teacher, student)
    - full_name: User's full name
    """
    # If Authorization Bearer token provided, resolve user_id from cache
    uid = user_id
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        cached_uid = get_user_id_for_token(token)
        if cached_uid:
            uid = cached_uid

    if not uid:
        raise HTTPException(status_code=401, detail="User ID not provided")

    user = get_current_user(uid)
    return UserResponse(**user)

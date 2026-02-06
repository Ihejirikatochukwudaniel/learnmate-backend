from fastapi import APIRouter, HTTPException, Depends, Query, Header
from app.db.supabase import supabase
from app.schemas.auth import UserResponse, UserIdRequest, LoginResponse
from app.core.security import get_current_user
from app.core.session_cache import create_session, get_user_id_for_token
from pydantic import BaseModel
from typing import Optional
import logging

# Setup logging
logger = logging.getLogger(__name__)

class LoginRequest(BaseModel):
    email: str
    password: str

class SignupRequest(BaseModel):
    email: str
    password: str
    full_name: str
    school_id: Optional[str] = None

router = APIRouter(tags=["Auth"])

@router.post("/signup", response_model=LoginResponse)
def signup(request: SignupRequest):
    """
    Register a new user account with admin role.
    
    Creates both authentication user and profile entry.
    New users are automatically assigned admin role for their school.
    
    Returns:
    - user_id: The new user's unique identifier
    - token: Session token for authentication
    """
    try:
        # Check if user already exists in profiles by email
        existing_user = supabase.table('profiles').select("*").eq('email', request.email).execute()
        if existing_user.data:
            raise HTTPException(
                status_code=400,
                detail="An account with this email already exists. Please login instead."
            )

        # Create auth user in Supabase
        auth_response = supabase.auth.sign_up({
            "email": request.email,
            "password": request.password
        })

        if not auth_response.user:
            raise HTTPException(
                status_code=400,
                detail="Signup failed. Please try again."
            )

        user_id = str(auth_response.user.id)

        # Check if profile already exists for this user_id (from previous failed attempt)
        existing_profile = supabase.table('profiles').select("*").eq('id', user_id).execute()
        
        if existing_profile.data:
            # Profile already exists, just log them in
            logger.info(f"Profile already exists for user {user_id}, logging in")
            token = create_session(user_id)
            return LoginResponse(user_id=user_id, token=token)

        # Create profile with admin role (default for all new users)
        profile_data = {
            "id": user_id,
            "email": request.email,
            "full_name": request.full_name,
            
        }
        
        # Add school_id only if it's provided and not empty
        if request.school_id and request.school_id.strip():
            profile_data["school_id"] = request.school_id

        try:
            logger.info(f"Attempting to create profile with data: {profile_data}")
            profile_response = supabase.table('profiles').insert(profile_data).execute()
            logger.info(f"Profile created successfully")
        except Exception as profile_error:
            # Log the actual error for debugging
            logger.error(f"Profile creation error: {str(profile_error)}")
            raise HTTPException(
                status_code=400,
                detail=f"Profile creation failed: {str(profile_error)}"
            )

        # Create session token for immediate login
        token = create_session(user_id)

        return LoginResponse(user_id=user_id, token=token)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Signup failed: {str(e)}"
        )

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
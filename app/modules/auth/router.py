from fastapi import APIRouter, Depends
from app.core.security import get_current_user, get_dummy_user
from app.core.config import settings
from app.schemas.auth import UserResponse

router = APIRouter(tags=["Auth"])

@router.get("/me", response_model=UserResponse)
def me(user: dict = Depends(get_current_user if settings.USE_REAL_JWT else get_dummy_user)):
    """
    Returns current user info.
    Works with real Supabase JWT if USE_REAL_JWT=true, else returns dummy user.
    """
    return UserResponse(**user)

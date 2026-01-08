from fastapi import APIRouter, Depends
from app.core.security import get_current_user, get_dummy_user
import os

router = APIRouter(tags=["Auth"])

# Use real JWT if USE_REAL_JWT env is set, otherwise fallback to dummy
USE_REAL_JWT = os.getenv("USE_REAL_JWT", "false").lower() == "true"

@router.get("/me")
def me(user: dict = Depends(get_current_user if USE_REAL_JWT else get_dummy_user)):
    """
    Returns current user info.
    Works with real Supabase JWT if USE_REAL_JWT=true, else returns dummy user.
    """
    return user

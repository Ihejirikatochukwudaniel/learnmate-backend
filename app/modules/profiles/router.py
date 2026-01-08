from fastapi import APIRouter, Depends, HTTPException
from app.db.supabase import supabase
from app.schemas.profiles import ProfileCreate, ProfileUpdate, ProfileResponse
from app.core.dependencies import require_admin
from app.core.security import get_current_user
from datetime import datetime

router = APIRouter(tags=["Profiles"])

@router.post("/", response_model=ProfileResponse)
def create_profile(profile: ProfileCreate, user: dict = Depends(get_current_user)):
    """
    Create profile on first login. Only the authenticated user can create their own profile.
    """
    try:
        # Check if profile already exists
        existing = supabase.table("profiles").select("*").eq("id", user["id"]).execute()
        if existing.data:
            raise HTTPException(status_code=400, detail="Profile already exists")

        profile_data = {
            "id": user["id"],
            "email": user["email"],
            "full_name": profile.full_name,
            "role": profile.role,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        result = supabase.table("profiles").insert(profile_data).execute()
        return ProfileResponse(**result.data[0])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/me", response_model=ProfileResponse)
def get_my_profile(user: dict = Depends(get_current_user)):
    """
    Get current user's profile.
    """
    try:
        result = supabase.table("profiles").select("*").eq("id", user["id"]).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Profile not found")
        return ProfileResponse(**result.data[0])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/me", response_model=ProfileResponse)
def update_my_profile(profile: ProfileUpdate, user: dict = Depends(get_current_user)):
    """
    Update current user's profile.
    """
    try:
        update_data = {"updated_at": datetime.utcnow().isoformat()}
        if profile.full_name is not None:
            update_data["full_name"] = profile.full_name
        if profile.role is not None:
            update_data["role"] = profile.role

        result = supabase.table("profiles").update(update_data).eq("id", user["id"]).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Profile not found")
        return ProfileResponse(**result.data[0])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=list[ProfileResponse])
def get_all_profiles(_: dict = Depends(require_admin)):
    """
    Get all profiles. Admin only.
    """
    try:
        result = supabase.table("profiles").select("*").execute()
        return [ProfileResponse(**profile) for profile in result.data]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{user_id}", response_model=ProfileResponse)
def get_profile(user_id: str, _: dict = Depends(require_admin)):
    """
    Get specific profile by user ID. Admin only.
    """
    try:
        result = supabase.table("profiles").select("*").eq("id", user_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Profile not found")
        return ProfileResponse(**result.data[0])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
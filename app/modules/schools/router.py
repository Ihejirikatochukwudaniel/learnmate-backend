from fastapi import APIRouter, Depends, HTTPException
from app.db.supabase import supabase
from app.schemas.schools import SchoolCreate, SchoolResponse
from app.core.dependencies import require_admin
from app.core.security import get_current_user
from uuid import uuid4
from datetime import datetime

router = APIRouter(tags=["Schools"])

@router.post("/", response_model=SchoolResponse)
def create_school(
    school: SchoolCreate,
    user: dict = Depends(require_admin)
):
    """
    Register a new school. Only admins can create schools.
    """
    try:
        # Check if school name already exists
        existing = supabase.table("schools").select("id").eq("school_name", school.school_name).execute()
        if existing.data:
            raise HTTPException(status_code=400, detail="School name already exists")

        # Verify admin_id exists and is an admin
        admin_profile = supabase.table("profiles").select("id, role").eq("id", str(school.admin_id)).execute()
        if not admin_profile.data:
            raise HTTPException(status_code=400, detail="Admin user not found")
        if admin_profile.data[0]["role"] != "admin":
            raise HTTPException(status_code=400, detail="Specified user is not an admin")

        school_id = str(uuid4())
        school_data = {
            "id": school_id,
            "school_name": school.school_name,
            "admin_id": str(school.admin_id),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        # Insert school
        result = supabase.table("schools").insert(school_data).execute()
        
        # Update the admin's profile with the school_id
        supabase.table("profiles").update({
            "school_id": school_id
        }).eq("id", str(school.admin_id)).execute()

        return SchoolResponse(**result.data[0])

    except HTTPException:
        raise
    except Exception as e:
        print(f"Create school error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/admin/schools", response_model=list[SchoolResponse])
def get_all_schools(user: dict = Depends(require_admin)):
    """
    Get all schools. Only admins can view all schools.
    """
    try:
        result = supabase.table("schools").select("*").execute()
        return [SchoolResponse(**school) for school in result.data]
    except Exception as e:
        print(f"Get schools error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
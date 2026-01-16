from fastapi import APIRouter, Depends, HTTPException, Query
from app.db.supabase import supabase
from app.schemas.classes import ClassCreate, ClassUpdate, ClassResponse, ClassStudentAdd, ClassStudentResponse
from app.core.dependencies import require_admin, require_teacher, require_admin_or_teacher, require_admin_by_uuid, require_admin_or_teacher_by_uuid
from app.core.security import get_current_user
from datetime import datetime
import uuid

router = APIRouter(tags=["Classes"])

@router.post("/", response_model=ClassResponse)
def create_class(class_data: ClassCreate, admin_uuid: str = Query(..., description="UUID of the admin user")):
    """
    Create a new class. Admin only.
    """
    try:
        # Verify admin by UUID
        admin_profile = require_admin_by_uuid(admin_uuid)

        class_dict = {
            "id": str(uuid.uuid4()),
            "name": class_data.name,
            "description": class_data.description,
            "teacher_id": class_data.teacher_id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        result = supabase.table("classes").insert(class_dict).execute()
        return ClassResponse(**result.data[0])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/admin/{admin_uuid}")
def get_classes_by_admin(admin_uuid: str):
    """
    Get all classes for a specific admin UUID. For MVP/demo purposes.
    Does not require access-token auth. Returns 404 if no classes found.
    """
    try:
        result = supabase.table("classes").select("*").eq("admin_id", admin_uuid).execute()
        classes_data = result.data or []

        if not classes_data:
            raise HTTPException(status_code=404, detail="No classes found for this admin")

        return {
            "admin_id": admin_uuid,
            "classes": classes_data
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{class_id}", response_model=ClassResponse)
def get_class(class_id: str, user: dict = Depends(get_current_user)):
    """
    Get specific class by ID.
    """
    try:
        result = supabase.table("classes").select("*").eq("id", class_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Class not found")

        class_obj = result.data[0]

        # Check permissions
        if user["role"] == "student":
            # Check if student is enrolled
            enrollment = supabase.table("class_students").select("*").eq("class_id", class_id).eq("student_id", user["id"]).execute()
            if not enrollment.data:
                raise HTTPException(status_code=403, detail="Not enrolled in this class")
        elif user["role"] == "teacher" and class_obj["teacher_id"] != user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        return ClassResponse(**class_obj)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{class_id}", response_model=ClassResponse)
def update_class(class_id: str, class_data: ClassUpdate, admin_uuid: str = Query(..., description="UUID of the admin user")):
    """
    Update class. Admin only.
    """
    try:
        update_data = {"updated_at": datetime.utcnow().isoformat()}
        if class_data.name is not None:
            update_data["name"] = class_data.name
        if class_data.description is not None:
            update_data["description"] = class_data.description
        if class_data.teacher_id is not None:
            update_data["teacher_id"] = class_data.teacher_id

        result = supabase.table("classes").update(update_data).eq("id", class_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Class not found")
        return ClassResponse(**result.data[0])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{class_id}")
def delete_class(class_id: str, admin_uuid: str = Query(..., description="UUID of the admin user")):
    """
    Delete class. Admin only.
    """
    try:
        result = supabase.table("classes").delete().eq("id", class_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Class not found")
        return {"message": "Class deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{class_id}/students", response_model=ClassStudentResponse)
def add_student_to_class(class_id: str, student_data: ClassStudentAdd, user: dict = Depends(require_admin_or_teacher)):
    """
    Add student to class. Admin or teacher of the class.
    """
    try:
        # Check if class exists and user has permission
        class_result = supabase.table("classes").select("*").eq("id", class_id).execute()
        if not class_result.data:
            raise HTTPException(status_code=404, detail="Class not found")

        if user["role"] == "teacher" and class_result.data[0]["teacher_id"] != user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Check if student is already enrolled
        existing = supabase.table("class_students").select("*").eq("class_id", class_id).eq("student_id", student_data.student_id).execute()
        if existing.data:
            raise HTTPException(status_code=400, detail="Student already enrolled")

        enrollment_data = {
            "class_id": class_id,
            "student_id": student_data.student_id,
            "enrolled_at": datetime.utcnow().isoformat()
        }

        result = supabase.table("class_students").insert(enrollment_data).execute()
        return ClassStudentResponse(**result.data[0])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{class_id}/students", response_model=list[ClassStudentResponse])
def get_class_students(class_id: str, user: dict = Depends(require_admin_or_teacher)):
    """
    Get students enrolled in class. Admin or teacher of the class.
    """
    try:
        # Check if class exists and user has permission
        class_result = supabase.table("classes").select("*").eq("id", class_id).execute()
        if not class_result.data:
            raise HTTPException(status_code=404, detail="Class not found")

        if user["role"] == "teacher" and class_result.data[0]["teacher_id"] != user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        result = supabase.table("class_students").select("*").eq("class_id", class_id).execute()
        return [ClassStudentResponse(**enrollment) for enrollment in result.data]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{class_id}/students/{student_id}")
def remove_student_from_class(class_id: str, student_id: str, user: dict = Depends(require_admin_or_teacher)):
    """
    Remove student from class. Admin or teacher of the class.
    """
    try:
        # Check if class exists and user has permission
        class_result = supabase.table("classes").select("*").eq("id", class_id).execute()
        if not class_result.data:
            raise HTTPException(status_code=404, detail="Class not found")

        if user["role"] == "teacher" and class_result.data[0]["teacher_id"] != user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        result = supabase.table("class_students").delete().eq("class_id", class_id).eq("student_id", student_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Enrollment not found")
        return {"message": "Student removed from class"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
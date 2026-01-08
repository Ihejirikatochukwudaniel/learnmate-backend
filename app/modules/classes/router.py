from fastapi import APIRouter, Depends, HTTPException
from app.db.supabase import supabase
from app.schemas.classes import ClassCreate, ClassUpdate, ClassResponse, ClassStudentAdd, ClassStudentResponse
from app.core.dependencies import require_admin, require_teacher, require_admin_or_teacher
from app.core.security import get_current_user
from datetime import datetime

router = APIRouter(tags=["Classes"])

@router.post("/", response_model=ClassResponse)
def create_class(class_data: ClassCreate, _: dict = Depends(require_admin)):
    """
    Create a new class. Admin only.
    """
    try:
        class_dict = {
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

@router.get("/", response_model=list[ClassResponse])
def get_all_classes(user: dict = Depends(get_current_user)):
    """
    Get all classes. Students see classes they're enrolled in, teachers see their classes, admins see all.
    """
    try:
        if user["role"] == "admin":
            result = supabase.table("classes").select("*").execute()
        elif user["role"] == "teacher":
            result = supabase.table("classes").select("*").eq("teacher_id", user["id"]).execute()
        else:  # student
            # Get classes where student is enrolled
            enrollments = supabase.table("class_students").select("class_id").eq("student_id", user["id"]).execute()
            class_ids = [e["class_id"] for e in enrollments.data]
            if not class_ids:
                return []
            result = supabase.table("classes").select("*").in_("id", class_ids).execute()

        return [ClassResponse(**cls) for cls in result.data]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{class_id}", response_model=ClassResponse)
def get_class(class_id: int, user: dict = Depends(get_current_user)):
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
def update_class(class_id: int, class_data: ClassUpdate, _: dict = Depends(require_admin)):
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
def delete_class(class_id: int, _: dict = Depends(require_admin)):
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
def add_student_to_class(class_id: int, student_data: ClassStudentAdd, user: dict = Depends(require_admin_or_teacher)):
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
def get_class_students(class_id: int, user: dict = Depends(require_admin_or_teacher)):
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
def remove_student_from_class(class_id: int, student_id: str, user: dict = Depends(require_admin_or_teacher)):
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
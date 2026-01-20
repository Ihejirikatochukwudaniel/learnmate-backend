from fastapi import APIRouter, HTTPException, Query
from app.db.supabase import supabase
from app.schemas.classes import (
    ClassCreate,
    ClassUpdate,
    ClassResponse,
    ClassStudentAdd,
    ClassStudentResponse,
)
from app.core.dependencies import (
    require_admin_by_uuid,
    require_teacher_by_uuid,
    require_admin_or_teacher_by_uuid,
)
from datetime import datetime
import uuid

router = APIRouter(tags=["Classes"])


# -------------------------
# HELPER: ATTACH STUDENTS
# -------------------------
def attach_students_to_class(class_obj: dict) -> dict:
    enrollments = (
        supabase
        .table("class_students")
        .select("student_id")
        .eq("class_id", class_obj["id"])
        .execute()
    )

    student_ids = [row["student_id"] for row in enrollments.data]

    if not student_ids:
        class_obj["students"] = []
        return class_obj

    students = (
        supabase
        .table("profiles")
        .select("id, full_name, email")
        .in_("id", student_ids)
        .execute()
    )

    class_obj["students"] = students.data
    return class_obj


# -------------------------
# CREATE CLASS (ADMIN UID)
# -------------------------
@router.post("/", response_model=ClassResponse)
def create_class(
    class_data: ClassCreate,
    admin_uid: str = Query(..., description="Admin UID"),
):
    require_admin_by_uuid(admin_uid)

    class_dict = {
        "id": str(uuid.uuid4()),
        "name": class_data.name,
        "description": class_data.description,
        "teacher_id": class_data.teacher_id,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }

    result = supabase.table("classes").insert(class_dict).execute()
    return ClassResponse(**result.data[0])


# -------------------------
# GET CLASSES (UID BASED)
# -------------------------
@router.get("/", response_model=list[dict])
def get_classes(
    uid: str = Query(..., description="User UID"),
):
    user = require_admin_or_teacher_by_uuid(uid)

    # ADMIN: see all classes
    if user["role"] == "admin":
        result = supabase.table("classes").select("*").execute()
        return [attach_students_to_class(cls) for cls in result.data]

    # TEACHER: see own classes
    if user["role"] == "teacher":
        result = (
            supabase
            .table("classes")
            .select("*")
            .eq("teacher_id", uid)
            .execute()
        )
        return [attach_students_to_class(cls) for cls in result.data]

    # STUDENT: see enrolled classes
    enrollments = (
        supabase
        .table("class_students")
        .select("class_id")
        .eq("student_id", uid)
        .execute()
    )

    class_ids = [row["class_id"] for row in enrollments.data]

    if not class_ids:
        return []

    classes = (
        supabase
        .table("classes")
        .select("*")
        .in_("id", class_ids)
        .execute()
    )

    return [attach_students_to_class(cls) for cls in classes.data]


# -------------------------
# GET STUDENT'S ENROLLED CLASSES
# -------------------------
@router.get("/student/{student_id}", response_model=list[dict])
def get_student_classes(
    student_id: str,
):
    # Get all class enrollments for the student
    enrollments = (
        supabase
        .table("class_students")
        .select("class_id")
        .eq("student_id", student_id)
        .execute()
    )

    class_ids = [row["class_id"] for row in enrollments.data]

    if not class_ids:
        return []

    # Get all classes the student is enrolled in
    classes = (
        supabase
        .table("classes")
        .select("*")
        .in_("id", class_ids)
        .execute()
    )

    return [attach_students_to_class(cls) for cls in classes.data]


# -------------------------
# GET SINGLE CLASS
# -------------------------
@router.get("/{class_id}", response_model=dict)
def get_class(
    class_id: str,
    uid: str = Query(..., description="User UID"),
):
    user = require_admin_or_teacher_by_uuid(uid)

    result = supabase.table("classes").select("*").eq("id", class_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Class not found")

    class_obj = result.data[0]

    if user["role"] == "teacher" and class_obj["teacher_id"] != uid:
        raise HTTPException(status_code=403, detail="Access denied")

    if user["role"] == "student":
        enrollment = (
            supabase
            .table("class_students")
            .select("*")
            .eq("class_id", class_id)
            .eq("student_id", uid)
            .execute()
        )
        if not enrollment.data:
            raise HTTPException(status_code=403, detail="Not enrolled in this class")

    return attach_students_to_class(class_obj)


# -------------------------
# UPDATE CLASS (ADMIN UID)
# -------------------------
@router.put("/{class_id}", response_model=ClassResponse)
def update_class(
    class_id: str,
    class_data: ClassUpdate,
    admin_uid: str = Query(..., description="Admin UID"),
):
    require_admin_by_uuid(admin_uid)

    update_data = {"updated_at": datetime.utcnow().isoformat()}

    if class_data.name is not None:
        update_data["name"] = class_data.name
    if class_data.description is not None:
        update_data["description"] = class_data.description
    if class_data.teacher_id is not None:
        update_data["teacher_id"] = class_data.teacher_id

    result = (
        supabase
        .table("classes")
        .update(update_data)
        .eq("id", class_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Class not found")

    return ClassResponse(**result.data[0])


# -------------------------
# DELETE CLASS (ADMIN UID)
# -------------------------
@router.delete("/{class_id}")
def delete_class(
    class_id: str,
    admin_uid: str = Query(..., description="Admin UID"),
):
    require_admin_by_uuid(admin_uid)

    result = supabase.table("classes").delete().eq("id", class_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Class not found")

    return {"message": "Class deleted successfully"}


# -------------------------
# ADD STUDENT TO CLASS
# -------------------------
@router.post("/{class_id}/students", response_model=ClassStudentResponse)
def add_student_to_class(
    class_id: str,
    student_data: ClassStudentAdd,
    uid: str = Query(..., description="Admin or Teacher UID"),
):
    user = require_admin_or_teacher_by_uuid(uid)

    class_result = supabase.table("classes").select("*").eq("id", class_id).execute()
    if not class_result.data:
        raise HTTPException(status_code=404, detail="Class not found")

    if user["role"] == "teacher" and class_result.data[0]["teacher_id"] != uid:
        raise HTTPException(status_code=403, detail="Access denied")

    existing = (
        supabase
        .table("class_students")
        .select("*")
        .eq("class_id", class_id)
        .eq("student_id", student_data.student_id)
        .execute()
    )
    if existing.data:
        raise HTTPException(status_code=400, detail="Student already enrolled")

    enrollment_data = {
        "class_id": class_id,
        "student_id": student_data.student_id,
        "enrolled_at": datetime.utcnow().isoformat(),
    }

    result = supabase.table("class_students").insert(enrollment_data).execute()
    return ClassStudentResponse(**result.data[0])


# -------------------------
# REMOVE STUDENT FROM CLASS
# -------------------------
@router.delete("/{class_id}/students/{student_id}")
def remove_student_from_class(
    class_id: str,
    student_id: str,
    uid: str = Query(..., description="Admin or Teacher UID"),
):
    user = require_admin_or_teacher_by_uuid(uid)

    class_result = supabase.table("classes").select("*").eq("id", class_id).execute()
    if not class_result.data:
        raise HTTPException(status_code=404, detail="Class not found")

    if user["role"] == "teacher" and class_result.data[0]["teacher_id"] != uid:
        raise HTTPException(status_code=403, detail="Access denied")

    result = (
        supabase
        .table("class_students")
        .delete()
        .eq("class_id", class_id)
        .eq("student_id", student_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    return {"message": "Student removed from class"}

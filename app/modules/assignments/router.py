from fastapi import APIRouter, Depends, HTTPException
from app.db.supabase import supabase
from app.schemas.assignments import AssignmentCreate, AssignmentUpdate, AssignmentResponse
from app.core.dependencies import require_teacher, require_admin_or_teacher, get_current_school_id
from app.core.security import get_current_user
from datetime import datetime
from uuid import UUID

router = APIRouter(tags=["Assignments"])

@router.post("/", response_model=AssignmentResponse)
def create_assignment(
    assignment: AssignmentCreate,
    school_id: UUID = Depends(get_current_school_id),
    user: dict = Depends(require_admin_or_teacher)
):
    """
    Create a new assignment. Admin or teacher of the class, scoped to school.
    """
    try:
        # Check if class exists and user has permission, scoped to school
        class_result = supabase.table("classes").select("*").eq("id", assignment.class_id).eq("school_id", str(school_id)).execute()
        if not class_result.data:
            raise HTTPException(status_code=404, detail="Class not found")

        if user["role"] == "teacher" and class_result.data[0]["teacher_id"] != user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        assignment_data = {
            "class_id": assignment.class_id,
            "title": assignment.title,
            "description": assignment.description,
            "due_date": assignment.due_date.isoformat() if assignment.due_date else None,
            "file_url": assignment.file_url,
            "total_points": assignment.total_points,
            "created_by": user["id"],
            "school_id": str(school_id),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        result = supabase.table("assignments").insert(assignment_data).execute()
        return AssignmentResponse(**result.data[0])
    except HTTPException:
        raise
    except Exception as e:
        print(f"Create assignment error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/class/{class_id}", response_model=list[AssignmentResponse])
def get_class_assignments(
    class_id: str,                  # Changed from int to str
    school_id: UUID = Depends(get_current_school_id),
    user: dict = Depends(get_current_user)
):
    """
    Get assignments for a class, scoped to school. Students must be enrolled, teachers must teach the class.
    """
    try:
        # Check if class exists, scoped to school
        class_result = supabase.table("classes").select("*").eq("id", class_id).eq("school_id", str(school_id)).execute()
        if not class_result.data:
            raise HTTPException(status_code=404, detail="Class not found")

        # Check permissions
        if user["role"] == "student":
            enrollment = supabase.table("class_students").select("*").eq("class_id", class_id).eq("student_id", user["id"]).execute()
            if not enrollment.data:
                raise HTTPException(status_code=403, detail="Not enrolled in this class")
        elif user["role"] == "teacher" and class_result.data[0]["teacher_id"] != user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        result = supabase.table("assignments").select("*").eq("class_id", class_id).eq("school_id", str(school_id)).execute()
        return [AssignmentResponse(**assignment) for assignment in result.data]
    except HTTPException:
        raise
    except Exception as e:
        print(f"Get class assignments error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{assignment_id}", response_model=AssignmentResponse)
def get_assignment(
    assignment_id: str,             # Changed from int to str
    school_id: UUID = Depends(get_current_school_id),
    user: dict = Depends(get_current_user)
):
    """
    Get specific assignment by ID, scoped to school.
    """
    try:
        # Get assignment with class info, scoped to school
        result = supabase.table("assignments").select("*, classes(teacher_id)").eq("id", assignment_id).eq("school_id", str(school_id)).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Assignment not found")

        assignment = result.data[0]
        class_id = assignment["class_id"]
        teacher_id = assignment["classes"]["teacher_id"]

        # Check permissions
        if user["role"] == "student":
            enrollment = supabase.table("class_students").select("*").eq("class_id", class_id).eq("student_id", user["id"]).execute()
            if not enrollment.data:
                raise HTTPException(status_code=403, detail="Not enrolled in this class")
        elif user["role"] == "teacher" and teacher_id != user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Remove the nested class data before returning
        assignment.pop("classes", None)
        return AssignmentResponse(**assignment)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Get assignment error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{assignment_id}", response_model=AssignmentResponse)
def update_assignment(
    assignment_id: str,             # Changed from int to str
    assignment: AssignmentUpdate,
    school_id: UUID = Depends(get_current_school_id),
    user: dict = Depends(require_admin_or_teacher)
):
    """
    Update assignment, scoped to school. Admin or teacher of the class.
    """
    try:
        # Get assignment with class info, scoped to school
        existing = supabase.table("assignments").select("*, classes(teacher_id)").eq("id", assignment_id).eq("school_id", str(school_id)).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Assignment not found")

        record = existing.data[0]
        teacher_id = record["classes"]["teacher_id"]

        if user["role"] == "teacher" and teacher_id != user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        update_data = {"updated_at": datetime.utcnow().isoformat()}
        if assignment.title is not None:
            update_data["title"] = assignment.title
        if assignment.description is not None:
            update_data["description"] = assignment.description
        if assignment.due_date is not None:
            update_data["due_date"] = assignment.due_date.isoformat()
        if assignment.file_url is not None:
            update_data["file_url"] = assignment.file_url
        if assignment.total_points is not None:        # Added
            update_data["total_points"] = assignment.total_points

        result = supabase.table("assignments").update(update_data).eq("id", assignment_id).eq("school_id", str(school_id)).execute()
        return AssignmentResponse(**result.data[0])
    except HTTPException:
        raise
    except Exception as e:
        print(f"Update assignment error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{assignment_id}")
def delete_assignment(
    assignment_id: str,             # Changed from int to str
    school_id: UUID = Depends(get_current_school_id),
    user: dict = Depends(require_admin_or_teacher)
):
    """
    Delete assignment, scoped to school. Admin or teacher of the class.
    """
    try:
        # Get assignment with class info, scoped to school
        existing = supabase.table("assignments").select("*, classes(teacher_id)").eq("id", assignment_id).eq("school_id", str(school_id)).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Assignment not found")

        record = existing.data[0]
        teacher_id = record["classes"]["teacher_id"]

        if user["role"] == "teacher" and teacher_id != user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        result = supabase.table("assignments").delete().eq("id", assignment_id).eq("school_id", str(school_id)).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Assignment not found")
        return {"message": "Assignment deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Delete assignment error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
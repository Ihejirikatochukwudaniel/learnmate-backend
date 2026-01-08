from fastapi import APIRouter, Depends, HTTPException
from app.db.supabase import supabase
from app.schemas.submissions import SubmissionCreate, SubmissionUpdate, SubmissionResponse
from app.core.dependencies import require_admin_or_teacher
from app.core.security import get_current_user
from datetime import datetime

router = APIRouter(tags=["Submissions"])

@router.post("/", response_model=SubmissionResponse)
def submit_assignment(submission: SubmissionCreate, user: dict = Depends(get_current_user)):
    """
    Submit an assignment. Only students can submit.
    """
    try:
        if user["role"] != "student":
            raise HTTPException(status_code=403, detail="Only students can submit assignments")

        # Check if assignment exists
        assignment_result = supabase.table("assignments").select("*, classes(teacher_id)").eq("id", submission.assignment_id).execute()
        if not assignment_result.data:
            raise HTTPException(status_code=404, detail="Assignment not found")

        assignment = assignment_result.data[0]
        class_id = assignment["class_id"]

        # Check if student is enrolled in the class
        enrollment = supabase.table("class_students").select("*").eq("class_id", class_id).eq("student_id", user["id"]).execute()
        if not enrollment.data:
            raise HTTPException(status_code=403, detail="Not enrolled in this class")

        # Check if submission already exists
        existing = supabase.table("submissions").select("*").eq("assignment_id", submission.assignment_id).eq("student_id", user["id"]).execute()
        if existing.data:
            raise HTTPException(status_code=400, detail="Submission already exists")

        submission_data = {
            "assignment_id": submission.assignment_id,
            "student_id": user["id"],
            "submitted_at": datetime.utcnow().isoformat(),
            "file_url": submission.file_url,
            "notes": submission.notes
        }

        result = supabase.table("submissions").insert(submission_data).execute()
        return SubmissionResponse(**result.data[0])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/assignment/{assignment_id}", response_model=list[SubmissionResponse])
def get_assignment_submissions(assignment_id: int, user: dict = Depends(require_admin_or_teacher)):
    """
    Get all submissions for an assignment. Admin or teacher of the class.
    """
    try:
        # Get assignment with class info
        assignment_result = supabase.table("assignments").select("*, classes(teacher_id)").eq("id", assignment_id).execute()
        if not assignment_result.data:
            raise HTTPException(status_code=404, detail="Assignment not found")

        assignment = assignment_result.data[0]
        teacher_id = assignment["classes"]["teacher_id"]

        if user["role"] == "teacher" and teacher_id != user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        result = supabase.table("submissions").select("*").eq("assignment_id", assignment_id).execute()
        return [SubmissionResponse(**submission) for submission in result.data]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/my", response_model=list[SubmissionResponse])
def get_my_submissions(user: dict = Depends(get_current_user)):
    """
    Get current user's submissions. Only for students.
    """
    try:
        if user["role"] != "student":
            raise HTTPException(status_code=403, detail="Only students can view their submissions")

        result = supabase.table("submissions").select("*").eq("student_id", user["id"]).execute()
        return [SubmissionResponse(**submission) for submission in result.data]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{submission_id}", response_model=SubmissionResponse)
def get_submission(submission_id: int, user: dict = Depends(get_current_user)):
    """
    Get specific submission by ID.
    """
    try:
        # Get submission with assignment and class info
        result = supabase.table("submissions").select("*, assignments(class_id, classes(teacher_id))").eq("id", submission_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Submission not found")

        submission = result.data[0]
        teacher_id = submission["assignments"]["classes"]["teacher_id"]

        # Check permissions
        if user["role"] == "student" and submission["student_id"] != user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        elif user["role"] == "teacher" and teacher_id != user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Remove nested data before returning
        submission.pop("assignments", None)
        return SubmissionResponse(**submission)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{submission_id}", response_model=SubmissionResponse)
def update_submission(submission_id: int, submission: SubmissionUpdate, user: dict = Depends(get_current_user)):
    """
    Update submission. Only the student who submitted can update.
    """
    try:
        if user["role"] != "student":
            raise HTTPException(status_code=403, detail="Only students can update their submissions")

        # Check if submission exists and belongs to user
        existing = supabase.table("submissions").select("*").eq("id", submission_id).eq("student_id", user["id"]).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Submission not found")

        update_data = {}
        if submission.file_url is not None:
            update_data["file_url"] = submission.file_url
        if submission.notes is not None:
            update_data["notes"] = submission.notes

        if update_data:
            result = supabase.table("submissions").update(update_data).eq("id", submission_id).execute()
            return SubmissionResponse(**result.data[0])
        else:
            return SubmissionResponse(**existing.data[0])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{submission_id}")
def delete_submission(submission_id: int, user: dict = Depends(require_admin_or_teacher)):
    """
    Delete submission. Admin or teacher of the class.
    """
    try:
        # Get submission with assignment and class info
        submission_result = supabase.table("submissions").select("*, assignments(class_id, classes(teacher_id))").eq("id", submission_id).execute()
        if not submission_result.data:
            raise HTTPException(status_code=404, detail="Submission not found")

        submission = submission_result.data[0]
        teacher_id = submission["assignments"]["classes"]["teacher_id"]

        if user["role"] == "teacher" and teacher_id != user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        result = supabase.table("submissions").delete().eq("id", submission_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Submission not found")
        return {"message": "Submission deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
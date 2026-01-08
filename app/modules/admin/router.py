from fastapi import APIRouter, Depends, HTTPException
from app.db.supabase import supabase
from app.core.dependencies import require_admin
from typing import Dict

router = APIRouter(tags=["Admin"])

@router.get("/metrics")
def get_admin_metrics(_: dict = Depends(require_admin)):
    """
    Get admin metrics. Admin only.
    """
    try:
        # Total users
        total_users = supabase.table("profiles").select("id", count="exact").execute()
        total_users_count = total_users.count if hasattr(total_users, 'count') else len(total_users.data)

        # Active users (users with recent activity - last 30 days)
        # For simplicity, we'll count users who have logged in recently
        # This would need activity_logs table to be properly implemented
        active_users_count = total_users_count  # Placeholder

        # Attendance count (total attendance records)
        attendance_count = supabase.table("attendance").select("id", count="exact").execute()
        attendance_count = attendance_count.count if hasattr(attendance_count, 'count') else len(attendance_count.data)

        # Assignments created
        assignments_count = supabase.table("assignments").select("id", count="exact").execute()
        assignments_count = assignments_count.count if hasattr(assignments_count, 'count') else len(assignments_count.data)

        # Grades entered
        grades_count = supabase.table("grades").select("id", count="exact").execute()
        grades_count = grades_count.count if hasattr(grades_count, 'count') else len(grades_count.data)

        # Classes count
        classes_count = supabase.table("classes").select("id", count="exact").execute()
        classes_count = classes_count.count if hasattr(classes_count, 'count') else len(classes_count.data)

        # Students enrolled
        students_enrolled = supabase.table("class_students").select("student_id", count="exact").execute()
        students_enrolled_count = students_enrolled.count if hasattr(students_enrolled, 'count') else len(students_enrolled.data)

        return {
            "total_users": total_users_count,
            "active_users": active_users_count,
            "total_classes": classes_count,
            "students_enrolled": students_enrolled_count,
            "attendance_records": attendance_count,
            "assignments_created": assignments_count,
            "grades_entered": grades_count
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/users")
def get_all_users(_: dict = Depends(require_admin)):
    """
    Get all users with their profiles. Admin only.
    """
    try:
        result = supabase.table("profiles").select("*").execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/activity")
def get_recent_activity(limit: int = 50, _: dict = Depends(require_admin)):
    """
    Get recent activity logs. Admin only.
    """
    try:
        result = supabase.table("activity_logs").select("*").order("created_at", desc=True).limit(limit).execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
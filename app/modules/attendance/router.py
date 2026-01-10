from fastapi import APIRouter, Depends, HTTPException
from app.db.supabase import supabase
from app.schemas.attendance import AttendanceCreate, AttendanceUpdate, AttendanceResponse, AttendanceBulkCreate
from app.core.dependencies import require_teacher, require_admin_or_teacher
from app.core.security import get_current_user
from datetime import datetime
from typing import List

router = APIRouter(tags=["Attendance"])

@router.post("/", response_model=AttendanceResponse)
def mark_attendance(attendance: AttendanceCreate, user: dict = Depends(require_admin_or_teacher)):
    """
    Mark attendance for a student. Admin or teacher of the class.
    """
    try:
        # Check if class exists and user has permission
        class_result = supabase.table("classes").select("*").eq("id", attendance.class_id).execute()
        if not class_result.data:
            raise HTTPException(status_code=404, detail="Class not found")

        if user["role"] == "teacher" and class_result.data[0]["teacher_id"] != user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Check if attendance already exists for this student/date/class
        existing = supabase.table("attendance").select("*").eq("class_id", attendance.class_id).eq("student_id", attendance.student_id).eq("date", attendance.date.isoformat()).execute()
        if existing.data:
            raise HTTPException(status_code=400, detail="Attendance already marked for this date")

        attendance_data = {
            "class_id": attendance.class_id,
            "student_id": attendance.student_id,
            "date": attendance.date.isoformat(),
            "status": attendance.status,
            "marked_by": user["id"],
            "created_at": datetime.utcnow().isoformat()
        }

        result = supabase.table("attendance").insert(attendance_data).execute()
        return AttendanceResponse(**result.data[0])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/bulk", response_model=List[AttendanceResponse])
def mark_bulk_attendance(bulk_data: AttendanceBulkCreate, user: dict = Depends(require_admin_or_teacher)):
    """
    Mark attendance for multiple students at once. Admin or teacher of the class.
    """
    try:
        responses = []
        for attendance in bulk_data.attendances:
            # Check if class exists and user has permission
            class_result = supabase.table("classes").select("*").eq("id", attendance.class_id).execute()
            if not class_result.data:
                raise HTTPException(status_code=404, detail=f"Class {attendance.class_id} not found")

            if user["role"] == "teacher" and class_result.data[0]["teacher_id"] != user["id"]:
                raise HTTPException(status_code=403, detail="Access denied")

            # Check if attendance already exists
            existing = supabase.table("attendance").select("*").eq("class_id", attendance.class_id).eq("student_id", attendance.student_id).eq("date", attendance.date.isoformat()).execute()
            if existing.data:
                continue  # Skip if already marked

            attendance_data = {
                "class_id": attendance.class_id,
                "student_id": attendance.student_id,
                "date": attendance.date.isoformat(),
                "status": attendance.status,
                "marked_by": user["id"],
                "created_at": datetime.utcnow().isoformat()
            }

            result = supabase.table("attendance").insert(attendance_data).execute()
            responses.append(AttendanceResponse(**result.data[0]))

        return responses
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/class/{class_id}", response_model=List[AttendanceResponse])
def get_class_attendance(class_id: int, date: str = None, user: dict = Depends(require_admin_or_teacher)):
    """
    Get attendance for a class. Admin or teacher of the class.
    Optional date filter: YYYY-MM-DD format.
    """
    try:
        # Check if class exists and user has permission
        class_result = supabase.table("classes").select("*").eq("id", class_id).execute()
        if not class_result.data:
            raise HTTPException(status_code=404, detail="Class not found")

        if user["role"] == "teacher" and class_result.data[0]["teacher_id"] != user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        query = supabase.table("attendance").select("*").eq("class_id", class_id)
        if date:
            query = query.eq("date", date)

        result = query.execute()
        return [AttendanceResponse(**record) for record in result.data]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/student/{student_id}", response_model=List[AttendanceResponse])
def get_student_attendance(student_id: str, user: dict = Depends(get_current_user)):
    """
    Get attendance for a student. Student can only view their own, teachers can view their students.
    """
    try:
        # Check permissions
        if user["role"] == "student" and user["id"] != student_id:
            raise HTTPException(status_code=403, detail="Access denied")
        elif user["role"] == "teacher":
            # Check if student is in teacher's class
            enrollments = supabase.table("class_students").select("class_id").eq("student_id", student_id).execute()
            class_ids = [e["class_id"] for e in enrollments.data]
            if not class_ids:
                return []
            # Check if any of these classes belong to the teacher
            teacher_classes = supabase.table("classes").select("id").eq("teacher_id", user["id"]).in_("id", class_ids).execute()
            if not teacher_classes.data:
                raise HTTPException(status_code=403, detail="Access denied")

        result = supabase.table("attendance").select("*").eq("student_id", student_id).execute()
        return [AttendanceResponse(**record) for record in result.data]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{attendance_id}", response_model=AttendanceResponse)
def update_attendance(attendance_id: int, attendance: AttendanceUpdate, user: dict = Depends(require_admin_or_teacher)):
    """
    Update attendance record. Admin or teacher of the class.
    """
    try:
        # Get existing attendance record
        existing = supabase.table("attendance").select("*, classes(teacher_id)").eq("id", attendance_id).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Attendance record not found")

        record = existing.data[0]
        teacher_id = record["classes"]["teacher_id"]

        if user["role"] == "teacher" and teacher_id != user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        update_data = {"status": attendance.status}
        result = supabase.table("attendance").update(update_data).eq("id", attendance_id).execute()
        return AttendanceResponse(**result.data[0])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{attendance_id}")
def delete_attendance(attendance_id: int, user: dict = Depends(require_admin_or_teacher)):
    """
    Delete attendance record. Admin or teacher of the class.
    """
    try:
        # Get existing attendance record
        existing = supabase.table("attendance").select("*, classes(teacher_id)").eq("id", attendance_id).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Attendance record not found")

        record = existing.data[0]
        teacher_id = record["classes"]["teacher_id"]

        if user["role"] == "teacher" and teacher_id != user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        result = supabase.table("attendance").delete().eq("id", attendance_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Attendance record not found")
        return {"message": "Attendance record deleted"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/class/{class_id}/summary", response_model=dict)
def get_attendance_summary(class_id: int, date: str = None, user: dict = Depends(require_admin_or_teacher)):
    """
    Get attendance summary for a class. Admin or teacher of the class.
    Shows total students, present count, absent count, and percentage.
    """
    try:
        # Check if class exists and user has permission
        class_result = supabase.table("classes").select("*").eq("id", class_id).execute()
        if not class_result.data:
            raise HTTPException(status_code=404, detail="Class not found")

        if user["role"] == "teacher" and class_result.data[0]["teacher_id"] != user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Get enrolled students count
        enrollment_result = supabase.table("class_students").select("student_id", count="exact").eq("class_id", class_id).execute()
        total_students = enrollment_result.count if hasattr(enrollment_result, 'count') else len(enrollment_result.data)

        if total_students == 0:
            return {
                "class_id": class_id,
                "date": date,
                "total_students": 0,
                "present_count": 0,
                "absent_count": 0,
                "attendance_percentage": 0.0
            }

        # Get attendance records for the specified date (or today's date if not specified)
        if not date:
            from datetime import date as date_type
            date = date_type.today().isoformat()

        attendance_query = supabase.table("attendance").select("status").eq("class_id", class_id).eq("date", date)
        attendance_result = attendance_query.execute()

        present_count = sum(1 for record in attendance_result.data if record["status"] == "present")
        absent_count = total_students - present_count
        attendance_percentage = (present_count / total_students) * 100 if total_students > 0 else 0.0

        return {
            "class_id": class_id,
            "date": date,
            "total_students": total_students,
            "present_count": present_count,
            "absent_count": absent_count,
            "attendance_percentage": round(attendance_percentage, 2)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

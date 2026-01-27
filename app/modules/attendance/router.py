from fastapi import APIRouter, Depends, HTTPException
from app.db.supabase import supabase
from app.schemas.attendance import (
    AttendanceCreate,
    AttendanceUpdate,
    AttendanceResponse,
    AttendanceBulkCreate,
)
from app.core.dependencies import require_admin_or_teacher_by_uuid
from datetime import datetime, date as date_type
from typing import List
from uuid import UUID

router = APIRouter(tags=["Attendance"])


@router.post("/", response_model=AttendanceResponse)
def mark_attendance(
    attendance: AttendanceCreate,
    user: dict = Depends(require_admin_or_teacher_by_uuid),
):
    """
    Mark attendance for a student. Admin or teacher of the class.
    """
    try:
        class_id = str(attendance.class_id)
        student_id = str(attendance.student_id)

        # Check class existence and permission
        class_result = (
            supabase.table("classes")
            .select("id, teacher_id")
            .eq("id", class_id)
            .execute()
        )
        if not class_result.data:
            raise HTTPException(status_code=404, detail="Class not found")

        if user["role"] == "teacher" and class_result.data[0]["teacher_id"] != user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Check for existing attendance
        existing = (
            supabase.table("attendance")
            .select("id")
            .eq("class_id", class_id)
            .eq("student_id", student_id)
            .eq("date", attendance.date)
            .execute()
        )
        if existing.data:
            raise HTTPException(
                status_code=400, detail="Attendance already marked for this date"
            )

        attendance_data = {
            "class_id": class_id,
            "student_id": student_id,
            "date": attendance.date,
            "status": attendance.status,
            "marked_by": user["id"],
            "created_at": datetime.utcnow().isoformat(),
        }

        result = supabase.table("attendance").insert(attendance_data).execute()
        return AttendanceResponse(**result.data[0])

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/bulk", response_model=List[AttendanceResponse])
def mark_bulk_attendance(
    bulk_data: AttendanceBulkCreate,
    user: dict = Depends(require_admin_or_teacher_by_uuid),
):
    """
    Mark attendance for multiple students at once.
    """
    try:
        responses = []

        for attendance in bulk_data.attendances:
            class_id = str(attendance.class_id)
            student_id = str(attendance.student_id)

            class_result = (
                supabase.table("classes")
                .select("id, teacher_id")
                .eq("id", class_id)
                .execute()
            )
            if not class_result.data:
                continue

            if user["role"] == "teacher" and class_result.data[0]["teacher_id"] != user["id"]:
                continue

            existing = (
                supabase.table("attendance")
                .select("id")
                .eq("class_id", class_id)
                .eq("student_id", student_id)
                .eq("date", attendance.date)
                .execute()
            )
            if existing.data:
                continue

            attendance_data = {
                "class_id": class_id,
                "student_id": student_id,
                "date": attendance.date,
                "status": attendance.status,
                "marked_by": user["id"],
                "created_at": datetime.utcnow().isoformat(),
            }

            result = supabase.table("attendance").insert(attendance_data).execute()
            responses.append(AttendanceResponse(**result.data[0]))

        return responses

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/class/{class_id}", response_model=List[AttendanceResponse])
def get_class_attendance(
    class_id: UUID,
    date: date_type | None = None,
    user: dict = Depends(require_admin_or_teacher_by_uuid),
):
    """
    Get attendance for a class (optionally filtered by date).
    """
    try:
        class_id_str = str(class_id)

        class_result = (
            supabase.table("classes")
            .select("id, teacher_id")
            .eq("id", class_id_str)
            .execute()
        )
        if not class_result.data:
            raise HTTPException(status_code=404, detail="Class not found")

        if user["role"] == "teacher" and class_result.data[0]["teacher_id"] != user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        query = supabase.table("attendance").select("*").eq("class_id", class_id_str)
        if date:
            query = query.eq("date", date)

        result = query.execute()
        return [AttendanceResponse(**row) for row in result.data]

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/student/{student_id}", response_model=List[AttendanceResponse])
def get_student_attendance(
    student_id: UUID,
    user: dict = Depends(require_admin_or_teacher_by_uuid),
):
    """
    Get attendance for a student.
    """
    try:
        student_id_str = str(student_id)

        if user["role"] == "teacher":
            enrollments = (
                supabase.table("class_students")
                .select("class_id")
                .eq("student_id", student_id_str)
                .execute()
            )
            class_ids = [e["class_id"] for e in enrollments.data]

            if not class_ids:
                return []

            teacher_classes = (
                supabase.table("classes")
                .select("id")
                .eq("teacher_id", user["id"])
                .in_("id", class_ids)
                .execute()
            )
            if not teacher_classes.data:
                raise HTTPException(status_code=403, detail="Access denied")

        result = (
            supabase.table("attendance")
            .select("*")
            .eq("student_id", student_id_str)
            .execute()
        )

        return [AttendanceResponse(**row) for row in result.data]

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{attendance_id}", response_model=AttendanceResponse)
def update_attendance(
    attendance_id: UUID,
    attendance: AttendanceUpdate,
    user: dict = Depends(require_admin_or_teacher_by_uuid),
):
    """
    Update attendance record.
    """
    try:
        attendance_id_str = str(attendance_id)

        existing = (
            supabase.table("attendance")
            .select("id, classes(teacher_id)")
            .eq("id", attendance_id_str)
            .execute()
        )
        if not existing.data:
            raise HTTPException(status_code=404, detail="Attendance record not found")

        teacher_id = existing.data[0]["classes"]["teacher_id"]
        if user["role"] == "teacher" and teacher_id != user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        result = (
            supabase.table("attendance")
            .update({"status": attendance.status})
            .eq("id", attendance_id_str)
            .execute()
        )

        return AttendanceResponse(**result.data[0])

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{attendance_id}")
def delete_attendance(
    attendance_id: UUID,
    user: dict = Depends(require_admin_or_teacher_by_uuid),
):
    """
    Delete attendance record.
    """
    try:
        attendance_id_str = str(attendance_id)

        existing = (
            supabase.table("attendance")
            .select("id, classes(teacher_id)")
            .eq("id", attendance_id_str)
            .execute()
        )
        if not existing.data:
            raise HTTPException(status_code=404, detail="Attendance record not found")

        teacher_id = existing.data[0]["classes"]["teacher_id"]
        if user["role"] == "teacher" and teacher_id != user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        supabase.table("attendance").delete().eq("id", attendance_id_str).execute()
        return {"message": "Attendance record deleted"}

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/class/{class_id}/summary")
def get_attendance_summary(
    class_id: UUID,
    date: date_type | None = None,
    user: dict = Depends(require_admin_or_teacher_by_uuid),
):
    """
    Get attendance summary for a class.
    """
    try:
        class_id_str = str(class_id)

        class_result = (
            supabase.table("classes")
            .select("id, teacher_id")
            .eq("id", class_id_str)
            .execute()
        )
        if not class_result.data:
            raise HTTPException(status_code=404, detail="Class not found")

        if user["role"] == "teacher" and class_result.data[0]["teacher_id"] != user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        enrollment = (
            supabase.table("class_students")
            .select("student_id", count="exact")
            .eq("class_id", class_id_str)
            .execute()
        )
        total_students = enrollment.count or 0

        if not date:
            date = date_type.today()

        attendance_result = (
            supabase.table("attendance")
            .select("status")
            .eq("class_id", class_id_str)
            .eq("date", date)
            .execute()
        )

        present_count = sum(
            1 for r in attendance_result.data if r["status"] == "present"
        )
        absent_count = total_students - present_count
        percentage = (present_count / total_students * 100) if total_students else 0.0

        return {
            "class_id": class_id,
            "date": date,
            "total_students": total_students,
            "present_count": present_count,
            "absent_count": absent_count,
            "attendance_percentage": round(percentage, 2),
        }

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

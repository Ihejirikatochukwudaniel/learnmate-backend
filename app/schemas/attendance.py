from pydantic import BaseModel
from typing import List, Literal
from datetime import date, datetime
from uuid import UUID

# Allowed attendance states
AttendanceStatus = Literal["present", "absent", "late"]


class AttendanceCreate(BaseModel):
    class_id: UUID
    student_id: UUID
    date: date
    status: AttendanceStatus


class AttendanceUpdate(BaseModel):
    status: AttendanceStatus


class AttendanceResponse(BaseModel):
    id: UUID
    class_id: UUID
    student_id: UUID
    date: date
    status: AttendanceStatus
    marked_by: UUID
    created_at: datetime


class AttendanceBulkCreate(BaseModel):
    attendances: List[AttendanceCreate]

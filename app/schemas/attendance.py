from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime

class AttendanceCreate(BaseModel):
    class_id: str
    student_id: str
    date: date
    status: str  # 'present', 'absent', 'late'

class AttendanceUpdate(BaseModel):
    status: str  # 'present', 'absent', 'late'

class AttendanceResponse(BaseModel):
    id: int
    class_id: str
    student_id: str
    date: date
    status: str
    marked_by: str
    created_at: datetime

class AttendanceBulkCreate(BaseModel):
    attendances: List[AttendanceCreate]
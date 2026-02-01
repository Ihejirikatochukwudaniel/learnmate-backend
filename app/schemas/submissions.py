from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class SubmissionCreate(BaseModel):
    assignment_id: int
    file_url: Optional[str] = None
    notes: Optional[str] = None

class SubmissionUpdate(BaseModel):
    file_url: Optional[str] = None
    notes: Optional[str] = None

class SubmissionResponse(BaseModel):
    id: int
    assignment_id: int
    student_id: str
    submitted_at: datetime
    file_url: Optional[str] = None
    notes: Optional[str] = None
    school_id: UUID
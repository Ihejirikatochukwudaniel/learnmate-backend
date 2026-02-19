from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class SubmissionCreate(BaseModel):
    assignment_id: str              
    class_id: UUID                  # Changed from str to UUID
    file_url: Optional[str] = None
    notes: Optional[str] = None

class SubmissionUpdate(BaseModel):
    file_url: Optional[str] = None
    notes: Optional[str] = None

class SubmissionResponse(BaseModel):
    id: str                         
    assignment_id: str              
    class_id: UUID                  # Changed from str to UUID
    student_id: str
    submitted_at: datetime
    file_url: Optional[str] = None
    notes: Optional[str] = None
    school_id: UUID

    class Config:
        populate_by_name = True
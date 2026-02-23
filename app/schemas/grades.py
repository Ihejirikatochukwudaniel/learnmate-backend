from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class GradeCreate(BaseModel):
    submission_id: str          # Changed from int to str
    grade: str                  # 'A', 'B', 'C', 'D', 'F' or numeric
    feedback: Optional[str] = None

class GradeUpdate(BaseModel):
    grade: Optional[str] = None
    feedback: Optional[str] = None

class GradeResponse(BaseModel):
    id: str                     # Changed from int to str
    submission_id: str          # Changed from int to str
    grade: str
    feedback: Optional[str] = None
    graded_by: str
    school_id: UUID
    graded_at: datetime

    class Config:
        populate_by_name = True
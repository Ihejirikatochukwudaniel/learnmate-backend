from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class GradeCreate(BaseModel):
    submission_id: int
    grade: str  # 'A', 'B', 'C', 'D', 'F' or numeric
    feedback: Optional[str] = None

class GradeUpdate(BaseModel):
    grade: Optional[str] = None
    feedback: Optional[str] = None

class GradeResponse(BaseModel):
    id: int
    submission_id: int
    grade: str
    feedback: Optional[str] = None
    graded_by: str
    graded_at: datetime
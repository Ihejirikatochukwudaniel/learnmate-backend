from pydantic import BaseModel, field_validator
from typing import Optional, Union
from datetime import datetime
from uuid import UUID

class GradeCreate(BaseModel):
    submission_id: str
    grade: Union[str, int, float]  # Accept string, int, or float
    feedback: Optional[str] = None
    
    @field_validator('grade')
    def convert_grade_to_string(cls, v):
        """Convert grade to string if it's a number"""
        return str(v)

class GradeUpdate(BaseModel):
    grade: Optional[Union[str, int, float]] = None
    feedback: Optional[str] = None
    
    @field_validator('grade')
    def convert_grade_to_string(cls, v):
        """Convert grade to string if it's a number"""
        if v is not None:
            return str(v)
        return v

class GradeResponse(BaseModel):
    id: str
    submission_id: str
    grade: str
    feedback: Optional[str] = None
    graded_by: str
    school_id: UUID
    graded_at: datetime

    class Config:
        populate_by_name = True
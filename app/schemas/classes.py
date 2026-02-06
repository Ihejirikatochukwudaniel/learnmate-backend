from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class ClassCreate(BaseModel):
    name: str
    description: Optional[str] = None
    school_id: Optional[UUID] = Field(None, alias="schoolId")
    school_name: Optional[str] = None

class ClassUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    teacher_id: Optional[str] = None

class ClassResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    teacher_id: str
    school_id: UUID
    created_at: datetime
    updated_at: datetime

class ClassStudentAdd(BaseModel):
    student_id: str

class ClassStudentResponse(BaseModel):
    class_id: str
    student_id: str
    enrolled_at: datetime

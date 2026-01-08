from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ClassCreate(BaseModel):
    name: str
    description: Optional[str] = None
    teacher_id: str

class ClassUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    teacher_id: Optional[str] = None

class ClassResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    teacher_id: str
    created_at: datetime
    updated_at: datetime

class ClassStudentAdd(BaseModel):
    student_id: str

class ClassStudentResponse(BaseModel):
    class_id: int
    student_id: str
    enrolled_at: datetime
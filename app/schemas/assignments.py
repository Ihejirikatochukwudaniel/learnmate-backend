from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class AssignmentCreate(BaseModel):
    class_id: int
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    file_url: Optional[str] = None

class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[date] = None
    file_url: Optional[str] = None

class AssignmentResponse(BaseModel):
    id: int
    class_id: int
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    file_url: Optional[str] = None
    created_by: str
    created_at: datetime
    updated_at: datetime
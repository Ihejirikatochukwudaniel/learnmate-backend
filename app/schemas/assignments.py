from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from uuid import UUID

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
    school_id: UUID
    created_at: datetime
    updated_at: datetime
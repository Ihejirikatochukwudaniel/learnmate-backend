from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from uuid import UUID

class AssignmentCreate(BaseModel):
    class_id: str                           # Changed from int to str
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    file_url: Optional[str] = None
    total_points: Optional[str] = None      # Added

class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[date] = None
    file_url: Optional[str] = None
    total_points: Optional[str] = None      # Added

class AssignmentResponse(BaseModel):
    id: str                                 # Changed from int to str
    class_id: str                           # Changed from int to str
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    file_url: Optional[str] = None
    total_points: Optional[str] = None      # Added
    created_by: str
    school_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProfileCreate(BaseModel):
    full_name: Optional[str] = None
    role: str  # 'admin', 'teacher', 'student'

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None

class ProfileResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    role: str
    created_at: datetime
    updated_at: datetime
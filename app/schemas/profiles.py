from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProfileCreate(BaseModel):
    firstName: str
    lastName: str
    email: str
    role: str  # 'admin', 'teacher', 'student'
    password: Optional[str] = None

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None

class ProfileResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    role: str
    created_at: datetime
    updated_at: datetime

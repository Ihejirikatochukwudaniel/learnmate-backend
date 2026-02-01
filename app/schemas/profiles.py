from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class ProfileCreate(BaseModel):
    first_name: str = Field(..., alias="firstName")
    last_name: str = Field(..., alias="lastName")
    email: str
    role: str  # 'admin', 'teacher', 'student'
    password: Optional[str] = None

    class Config:
        populate_by_name = True  # Allow both snake_case and camelCase

class ProfileUpdate(BaseModel):
    first_name: Optional[str] = Field(None, alias="firstName")
    last_name: Optional[str] = Field(None, alias="lastName")
    role: Optional[str] = None

    class Config:
        populate_by_name = True

class ProfileResponse(BaseModel):
    id: str
    email: str
    first_name: str = Field(..., alias="firstName")
    last_name: str = Field(..., alias="lastName")
    role: str
    school_id: Optional[UUID] = Field(None, alias="schoolId")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    class Config:
        populate_by_name = True
        from_attributes = True
from pydantic import BaseModel
from typing import Optional

class UserResponse(BaseModel):
    id: str
    email: Optional[str] = None
    role: str
    full_name: Optional[str] = None
    school_id: Optional[str] = None  # Add this
    school_name: Optional[str] = None  # Add this

class UserIdRequest(BaseModel):
    user_id: str

class LoginResponse(BaseModel):
    user_id: str
    token: Optional[str] = None
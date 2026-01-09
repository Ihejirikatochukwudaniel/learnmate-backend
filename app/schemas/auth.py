from pydantic import BaseModel
from typing import Optional

class UserResponse(BaseModel):
    id: str
    email: Optional[str] = None
    role: str
    full_name: Optional[str] = None

class UserIdRequest(BaseModel):
    user_id: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

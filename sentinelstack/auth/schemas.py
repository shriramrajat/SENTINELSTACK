from pydantic import BaseModel, EmailStr, UUID4
from datetime import datetime
from typing import Optional

# Shared properties
class UserBase(BaseModel):
    email: EmailStr

# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str

# Properties to return via API
class UserResponse(UserBase):
    id: UUID4
    is_active: bool
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

# Token schema
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    id: Optional[str] = None
    role: Optional[str] = None
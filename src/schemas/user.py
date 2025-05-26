from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# Schema for user creation (input)
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    is_admin: Optional[bool] = False # Default to regular user

# Schema for user reading (output)
class UserRead(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    is_admin: bool

    class Config:
        from_attributes = True # Pydantic V2 uses this instead of orm_mode

# Schema for user update (input)
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None

# Schema for login
class UserLogin(BaseModel):
    email: EmailStr
    password: str


from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# Base schema for Client data
class ClientBase(BaseModel):
    name: str
    email: EmailStr
    cpf: str = Field(..., pattern=r'^\d{11}$') # Basic CPF format validation (11 digits)
    phone: Optional[str] = None
    address: Optional[str] = None

# Schema for Client creation (input)
class ClientCreate(ClientBase):
    pass

# Schema for Client update (input)
class ClientUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    # CPF usually shouldn't be updated, but included if needed
    # cpf: Optional[str] = Field(None, pattern=r'^\d{11}$')
    phone: Optional[str] = None
    address: Optional[str] = None

# Schema for Client reading (output)
class ClientRead(ClientBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


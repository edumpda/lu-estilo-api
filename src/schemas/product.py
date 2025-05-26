from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date

# Base schema for Product data
class ProductBase(BaseModel):
    description: str
    sale_value: float = Field(..., gt=0) # Ensure sale value is positive
    barcode: Optional[str] = None
    section: Optional[str] = None
    initial_stock: int = Field(..., ge=0) # Ensure stock is non-negative
    validity_date: Optional[date] = None
    image_urls: Optional[str] = None # Could be a List[str] if parsed/stored differently

# Schema for Product creation (input)
class ProductCreate(ProductBase):
    pass

# Schema for Product update (input)
class ProductUpdate(BaseModel):
    description: Optional[str] = None
    sale_value: Optional[float] = Field(None, gt=0)
    barcode: Optional[str] = None
    section: Optional[str] = None
    # Stock updates might need separate endpoints or logic
    # initial_stock: Optional[int] = Field(None, ge=0)
    current_stock: Optional[int] = Field(None, ge=0) # Allow updating current stock
    validity_date: Optional[date] = None
    image_urls: Optional[str] = None

# Schema for Product reading (output)
class ProductRead(ProductBase):
    id: int
    current_stock: int # Include current stock in read operations

    class Config:
        from_attributes = True


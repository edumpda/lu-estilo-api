from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from .product import ProductRead # Import ProductRead for nesting
from .client import ClientRead # Import ClientRead for nesting
from ..models.order import OrderStatus # Import Enum

# Schema for OrderItem data (used within Order schemas)
class OrderItemBase(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0) # Ensure quantity is positive

class OrderItemCreate(OrderItemBase):
    pass

class OrderItemRead(OrderItemBase):
    id: int
    unit_price: float # Price at the time of order
    product: ProductRead # Nested product details

    class Config:
        from_attributes = True

# Base schema for Order data
class OrderBase(BaseModel):
    client_id: int

# Schema for Order creation (input)
class OrderCreate(OrderBase):
    items: List[OrderItemCreate]

# Schema for Order update (input)
class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    # Other fields like client_id or items usually aren't updated directly
    # Might need specific endpoints for adding/removing items if required

# Schema for Order reading (output)
class OrderRead(OrderBase):
    id: int
    status: OrderStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    total_value: Optional[float] = None
    client: ClientRead # Nested client details
    items: List[OrderItemRead] # Nested list of order items

    class Config:
        from_attributes = True


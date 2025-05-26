from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import enum

# Enum for Order Status
class OrderStatus(str, enum.Enum):
    PENDING = "Pendente"
    PROCESSING = "Processando"
    SHIPPED = "Enviado"
    DELIVERED = "Entregue"
    CANCELLED = "Cancelado"

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    # user_id = Column(Integer, ForeignKey("users.id")) # Optional: Link to user who created/processed
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    total_value = Column(Float, nullable=True) # Calculated value

    client = relationship("Client") # Relationship to Client
    # owner = relationship("User", back_populates="orders") # If user_id is added
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False) # Price at the time of order

    order = relationship("Order", back_populates="items")
    product = relationship("Product") # Relationship to Product


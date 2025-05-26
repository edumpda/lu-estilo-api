from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from .. import schemas, services
from ..core.database import get_db
from ..auth.dependencies import get_current_active_user, get_current_admin_user # Use admin for delete?
from ..models.user import User # To use User model for dependency
from ..models.order import OrderStatus # Import Enum

router = APIRouter()

@router.post("/", response_model=schemas.OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(
    order: schemas.OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user) # Any authenticated user can create an order
):
    """Creates a new order. Requires authentication.

    Validates product existence and stock before creating the order.
    Decrements stock upon successful order creation.
    """
    try:
        # Validate client exists
        client = services.client_service.get_client(db, order.client_id)
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Client with ID {order.client_id} not found.")

        created_order = services.order_service.create_order(db=db, order=order)
        # Trigger WhatsApp notification (placeholder)
        # services.whatsapp_service.send_order_confirmation(client.phone, created_order.id)
        return created_order
    except HTTPException as http_exc:
        raise http_exc # Re-raise HTTPException
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        # Log the exception details
        print(f"Error creating order: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal error occurred while creating the order.")

@router.get("/", response_model=List[schemas.OrderRead])
def read_orders(
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[datetime] = Query(None, description="Filter by start date (YYYY-MM-DDTHH:MM:SS)"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date (YYYY-MM-DDTHH:MM:SS)"),
    section: Optional[str] = Query(None, description="Filter by product section/category within the order"),
    order_id: Optional[int] = Query(None, description="Filter by specific order ID"),
    status: Optional[OrderStatus] = Query(None, description="Filter by order status"),
    client_id: Optional[int] = Query(None, description="Filter by client ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user) # Or admin only?
):
    """Retrieves a list of orders with pagination and filtering. Requires authentication."""
    # Add logic to restrict access? Regular users see their orders, admins see all?
    # For now, any authenticated user can see all orders.
    orders = services.order_service.get_orders(
        db, skip=skip, limit=limit,
        start_date=start_date, end_date=end_date, section=section,
        order_id=order_id, status=status, client_id=client_id
    )
    return orders

@router.get("/{order_id}", response_model=schemas.OrderRead)
def read_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retrieves a specific order by ID. Requires authentication."""
    # Add logic: Check if user owns the order or is admin?
    db_order = services.order_service.get_order(db, order_id=order_id)
    if db_order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    # if not current_user.is_admin and db_order.client_id != current_user.client_id: # Assuming user linked to client
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this order")
    return db_order

@router.put("/{order_id}", response_model=schemas.OrderRead)
def update_order(
    order_id: int,
    order: schemas.OrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user) # Only admins can update order status
):
    """Updates a specific order by ID (currently only status). Requires admin authentication."""
    updated_order = services.order_service.update_order(db=db, order_id=order_id, order_update=order)
    if updated_order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    # Trigger WhatsApp notification on status change (placeholder)
    # if order.status:
    #     client = services.client_service.get_client(db, updated_order.client_id)
    #     if client and client.phone:
    #         services.whatsapp_service.send_status_update(client.phone, order_id, order.status)

    return updated_order

@router.delete("/{order_id}", response_model=schemas.OrderRead)
def delete_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user) # Only admins can delete orders
):
    """Deletes a specific order by ID. Requires admin authentication.

    Note: Consider using a 'soft delete' or 'cancel' status instead of hard delete.
    """
    deleted_order = services.order_service.delete_order(db=db, order_id=order_id)
    if deleted_order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return deleted_order


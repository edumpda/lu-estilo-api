from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from ..models.order import Order, OrderItem, OrderStatus
from ..models.product import Product
from ..schemas.order import OrderCreate, OrderUpdate, OrderItemCreate
from .product_service import get_product, _update_product_stock_no_commit # Import product service
from typing import List, Optional
from datetime import datetime
from .. import schemas # Add import for schemas

def get_order(db: Session, order_id: int) -> Optional[Order]:
    """Fetches a single order by ID, loading related items and client."""
    return db.query(Order).options(
        # Eager load related data to avoid N+1 queries
        # selectinload(Order.client),
        # selectinload(Order.items).selectinload(OrderItem.product)
    ).filter(Order.id == order_id).first()
    # Note: Eager loading might be complex to set up correctly with Alembic/SQLAlchemy versions.
    # Default lazy loading will work but might be less performant for lists.
    # For simplicity here, relying on lazy loading or explicit joins in get_orders.

def get_orders(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    section: Optional[str] = None,
    order_id: Optional[int] = None,
    status: Optional[OrderStatus] = None,
    client_id: Optional[int] = None
) -> List[Order]:
    """Fetches a list of orders with optional filtering and pagination."""
    query = db.query(Order)

    if order_id is not None:
        query = query.filter(Order.id == order_id)
    if client_id is not None:
        query = query.filter(Order.client_id == client_id)
    if status is not None:
        query = query.filter(Order.status == status)
    if start_date is not None:
        query = query.filter(Order.created_at >= start_date)
    if end_date is not None:
        # Add 1 day to end_date to include the whole day
        # end_date_inclusive = end_date + timedelta(days=1)
        # query = query.filter(Order.created_at < end_date_inclusive)
        # Simpler approach: filter up to the end of the given day
        query = query.filter(func.date(Order.created_at) <= end_date.date())

    if section:
        # Filter orders containing at least one product from the specified section
        query = query.join(OrderItem).join(Product).filter(Product.section.ilike(f"%{section}%")).distinct()

    return query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()

def create_order(db: Session, order: OrderCreate) -> Order:
    """Creates a new order, validates stock, updates stock, and calculates total value."""
    total_value = 0.0
    db_items = []

    # 1. Validate stock and calculate total value for all items first
    product_stock_updates = {}
    for item_data in order.items:
        db_product = get_product(db, item_data.product_id)
        if not db_product:
            raise ValueError(f"Product with ID {item_data.product_id} not found.")
        if db_product.current_stock < item_data.quantity:
            raise ValueError(f"Insufficient stock for product ID {item_data.product_id}. Available: {db_product.current_stock}, Requested: {item_data.quantity}")

        item_total = db_product.sale_value * item_data.quantity
        total_value += item_total
        product_stock_updates[item_data.product_id] = -item_data.quantity # Store stock change needed

        db_item = OrderItem(
            product_id=item_data.product_id,
            quantity=item_data.quantity,
            unit_price=db_product.sale_value # Store price at time of order
        )
        db_items.append(db_item)

    # 2. If all validations pass, create the order and items, then update stock
    db_order = Order(
        client_id=order.client_id,
        total_value=total_value,
        status=OrderStatus.PENDING # Initial status
    )
    db_order.items.extend(db_items) # Add items to the order session

    db.add(db_order)
    # We need the order ID before committing items if FK constraint is immediate,
    # but SQLAlchemy handles relationship linking.

    # 3. Update stock for all products involved in the order
    try:
        for product_id, quantity_change in product_stock_updates.items():
            updated_product = _update_product_stock_no_commit(db, product_id, quantity_change)
            if updated_product is None: # Should not happen if validation passed, but check anyway
                 raise ValueError(f"Failed to update stock for product ID {product_id}")

        db.commit() # Commit order creation and stock updates together
        db.refresh(db_order)
        # Eager load items after creation if needed
        # db.refresh(db_order, attribute_names=['items'])
        return db_order
    except Exception as e:
        db.rollback() # Rollback if any stock update fails
        raise e # Re-raise the exception

def update_order_status(db: Session, order_id: int, status: OrderStatus) -> Optional[Order]:
    """Updates the status of an existing order."""
    print(f"Updating order {order_id} to status: {status} (type: {type(status)})", flush=True) # Add print for debugging
    db_order = get_order(db, order_id)
    if not db_order:
        print(f"Order {order_id} not found for status update.", flush=True) # Add print
        return None

    # Add logic here if status changes trigger actions (e.g., stock return on cancellation)
    # if status == OrderStatus.CANCELLED and db_order.status != OrderStatus.CANCELLED:
        # Return stock for cancelled items
        # for item in db_order.items:
        #     update_product_stock(db, item.product_id, item.quantity)

    # Garantir que o status seja atualizado corretamente
    if isinstance(status, str):
        # Se for uma string, converter para o enum correspondente
        try:
            status = OrderStatus(status)
        except ValueError:
            print(f"Status inválido: {status}", flush=True)
            raise ValueError(f"Status inválido: {status}")
    
    # Atualizar o status e garantir que seja persistido
    db_order.status = status
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    # Verificar se o status foi atualizado corretamente
    db.expire_all()  # Forçar refresh de todos os objetos na sessão
    db_order = get_order(db, order_id)  # Buscar novamente para garantir
    
    print(f"Order {order_id} status after refresh: {db_order.status}", flush=True) # Add another debug print
    return db_order

def update_order(db: Session, order_id: int, order_update: OrderUpdate) -> Optional[Order]:
    """Updates an existing order (currently only status)."""
    db_order = get_order(db, order_id)
    if not db_order:
        return None

    update_data = order_update.model_dump(exclude_unset=True)
    if 'status' in update_data:
        # Use the dedicated status update function if more logic is involved
        updated_db_order = update_order_status(db, order_id, update_data['status'])
        return updated_db_order # Return the result from update_order_status
        # Simple update if no extra logic:
        # db_order.status = update_data['status']
        # db.add(db_order)
        # db.commit()
        # db.refresh(db_order)

    # Add other update logic here if needed

    return db_order # Return original if only other fields were updated

def delete_order(db: Session, order_id: int) -> Optional[schemas.OrderRead]:
    """Deletes an order. Consider implications like stock return."""
    db_order = get_order(db, order_id)
    if not db_order:
        return None

    # Capture data before deletion for the response
    order_data_before_delete = schemas.OrderRead.model_validate(db_order)

    # Add logic here: Should deleting an order return stock?
    # Typically, orders are cancelled (status change) rather than hard deleted.
    # If hard delete is required, stock adjustment might be needed based on status.
    # if db_order.status not in [OrderStatus.CANCELLED, OrderStatus.DELIVERED]:
    #     # Potentially return stock
    #     pass

    db.delete(db_order)
    db.commit()
    return order_data_before_delete # Return the captured data


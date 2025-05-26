from sqlalchemy.orm import Session
from ..models.product import Product
from ..schemas.product import ProductCreate, ProductUpdate
from typing import List, Optional
from .. import schemas # Add import for schemas

def get_product(db: Session, product_id: int) -> Optional[Product]:
    """Fetches a single product by ID."""
    return db.query(Product).filter(Product.id == product_id).first()

def get_products(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    # availability filter might depend on current_stock > 0
    # available: Optional[bool] = None
) -> List[Product]:
    """Fetches a list of products with optional filtering and pagination."""
    query = db.query(Product)
    if category:
        query = query.filter(Product.section.ilike(f"%{category}%"))
    if min_price is not None:
        query = query.filter(Product.sale_value >= min_price)
    if max_price is not None:
        query = query.filter(Product.sale_value <= max_price)
    # if available is not None:
    #     if available:
    #         query = query.filter(Product.current_stock > 0)
    #     else:
    #         query = query.filter(Product.current_stock <= 0)

    return query.offset(skip).limit(limit).all()

def create_product(db: Session, product: ProductCreate) -> Product:
    """Creates a new product, setting current_stock equal to initial_stock."""
    # Pydantic handles validation based on ProductCreate schema
    db_product = Product(
        description=product.description,
        sale_value=product.sale_value,
        barcode=product.barcode,
        section=product.section,
        initial_stock=product.initial_stock,
        current_stock=product.initial_stock, # Set current stock initially
        validity_date=product.validity_date,
        image_urls=product.image_urls
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def update_product(db: Session, product_id: int, product_update: ProductUpdate) -> Optional[Product]:
    """Updates an existing product."""
    db_product = get_product(db, product_id)
    if not db_product:
        return None

    update_data = product_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_product, key, value)

    db.add(db_product) # Add to session to mark as dirty
    db.commit()
    db.refresh(db_product)
    return db_product

def delete_product(db: Session, product_id: int) -> Optional[Product]:
    """Deletes a product."""
    db_product = get_product(db, product_id)
    if not db_product:
        return None
    # Consider implications: check if product is in active orders?
    product_data_before_delete = schemas.ProductRead.model_validate(db_product) # Capture state before delete
    db.delete(db_product)
    db.commit()
    # Return the data captured before deletion, as the object is now detached
    return product_data_before_delete

# Function to update stock (used internally by order service)
def _update_product_stock_no_commit(db: Session, product_id: int, quantity_change: int) -> Optional[Product]:
    """Updates the current stock of a product *without committing*.
       Returns the product object or None if not found.
       Raises ValueError if stock would become negative (if strict control needed).
    """
    db_product = get_product(db, product_id)
    if not db_product:
        return None # Indicate product not found

    if db_product.current_stock + quantity_change < 0:
        # Depending on requirements, either raise error or clamp to 0
        raise ValueError(f"Insufficient stock for product ID {product_id}. Available: {db_product.current_stock}, Change: {quantity_change}")
        # db_product.current_stock = 0
    else:
        db_product.current_stock += quantity_change

    db.add(db_product) # Add to session to track changes
    # NO COMMIT HERE - managed by the calling function (e.g., create_order)
    return db_product


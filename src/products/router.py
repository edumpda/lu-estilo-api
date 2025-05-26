from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import shutil
import os

from .. import schemas, services
from ..core.database import get_db
from ..auth.dependencies import get_current_active_user, get_current_admin_user # Admin for create/update/delete
from ..models.user import User # To use User model for dependency

# Define a directory to store product images (adjust path as needed)
IMAGE_DIR = "/home/ubuntu/lu_estilo_api/static/images/products"
# Ensure the directory exists
os.makedirs(IMAGE_DIR, exist_ok=True)

router = APIRouter()

@router.post("/", response_model=schemas.ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(
    product: schemas.ProductCreate, # Changed Depends() to expect body
    # files: List[UploadFile] = File(None, description="Optional product images"), # Handle file uploads separately if needed
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user) # Only admins can create products
):
    """Creates a new product. Requires admin authentication."""
    # Handle image uploads here if using the File parameter
    # image_urls = []
    # if files:
    #     for file in files:
    #         file_location = os.path.join(IMAGE_DIR, file.filename)
    #         with open(file_location, "wb+") as file_object:
    #             shutil.copyfileobj(file.file, file_object)
    #         # Store relative path or full URL depending on setup
    #         image_urls.append(f"/static/images/products/{file.filename}")
    # product_data = product.model_dump()
    # product_data["image_urls"] = ",".join(image_urls) # Or store as JSON string
    # db_product = services.product_service.create_product(db=db, product=schemas.ProductCreate(**product_data))

    # Simplified version without direct file upload handling in this step
    # Image URLs are expected in the product schema directly for now
    db_product = services.product_service.create_product(db=db, product=product)
    return db_product

@router.get("/", response_model=List[schemas.ProductRead])
def read_products(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = Query(None, description="Filter by product section/category (case-insensitive)"),
    min_price: Optional[float] = Query(None, description="Filter by minimum sale price"),
    max_price: Optional[float] = Query(None, description="Filter by maximum sale price"),
    # available: Optional[bool] = Query(None, description="Filter by availability (stock > 0)"),
    db: Session = Depends(get_db),
    # No auth required for listing products, as per common practice, but can be added
    # current_user: User = Depends(get_current_active_user)
):
    """Retrieves a list of products with pagination and filtering."""
    products = services.product_service.get_products(
        db, skip=skip, limit=limit, category=category, min_price=min_price, max_price=max_price #, available=available
    )
    return products

@router.get("/{product_id}", response_model=schemas.ProductRead)
def read_product(
    product_id: int,
    db: Session = Depends(get_db),
    # No auth required for viewing a specific product
    # current_user: User = Depends(get_current_active_user)
):
    """Retrieves a specific product by ID."""
    db_product = services.product_service.get_product(db, product_id=product_id)
    if db_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return db_product

@router.put("/{product_id}", response_model=schemas.ProductRead)
def update_product(
    product_id: int,
    product: schemas.ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user) # Only admins can update products
):
    """Updates a specific product by ID. Requires admin authentication."""
    updated_product = services.product_service.update_product(db=db, product_id=product_id, product_update=product)
    if updated_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return updated_product

@router.delete("/{product_id}", response_model=schemas.ProductRead)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user) # Only admins can delete products
):
    """Deletes a specific product by ID. Requires admin authentication."""
    # Add check: prevent deletion if product is in active orders?
    deleted_product = services.product_service.delete_product(db=db, product_id=product_id)
    if deleted_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return deleted_product

# Example of a dedicated endpoint for image uploads if needed later
# @router.post("/{product_id}/images", status_code=status.HTTP_200_OK)
# async def upload_product_image(
#     product_id: int,
#     file: UploadFile = File(...),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_admin_user)
# ):
#     db_product = services.product_service.get_product(db, product_id=product_id)
#     if not db_product:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

#     file_location = os.path.join(IMAGE_DIR, file.filename)
#     try:
#         with open(file_location, "wb+") as file_object:
#             shutil.copyfileobj(file.file, file_object)
#         # Update product's image_urls field
#         image_url = f"/static/images/products/{file.filename}"
#         current_urls = db_product.image_urls.split(',') if db_product.image_urls else []
#         if image_url not in current_urls:
#             current_urls.append(image_url)
#             services.product_service.update_product(db, product_id, schemas.ProductUpdate(image_urls=",".join(current_urls)))
#     except Exception as e:
#         # Handle file writing errors
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not save image: {e}")

#     return {"filename": file.filename, "location": image_url}


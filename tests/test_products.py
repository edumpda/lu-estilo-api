import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src import schemas
from src.services import product_service
from src.models import Product, User # Import User for auth dependency

# Test product creation (requires admin)
def test_create_product(client: TestClient, db_session: Session, admin_auth_headers: dict):
    """Test successful product creation by an admin."""
    product_data = {
        "description": "Test Product",
        "sale_value": 19.99,
        # "barcode": "1234567890123", # Comment out again
        "section": "Test Section",
        "initial_stock": 50,
        "image_urls": "/static/images/products/test.jpg"
        # validity_date can be added if needed
    }
    response = client.post("/products/", json=product_data, headers=admin_auth_headers)
    if response.status_code != 201:
        print("Create product failed:", response.json()) # Print response body on failure
    assert response.status_code == 201
    data = response.json()
    assert data["description"] == product_data["description"]
    assert data["sale_value"] == product_data["sale_value"]
    assert data["initial_stock"] == product_data["initial_stock"]
    assert data["current_stock"] == product_data["initial_stock"] # Check if current_stock is set
    assert "id" in data

    # Verify in DB
    db_product = product_service.get_product(db_session, data["id"])
    assert db_product is not None
    assert db_product.description == product_data["description"]

def test_create_product_non_admin(client: TestClient, auth_headers: dict):
    """Test creating a product by a non-admin user (should fail)."""
    product_data = {"description": "Unauthorized Product", "sale_value": 10.0, "initial_stock": 10}
    response = client.post("/products/", json=product_data, headers=auth_headers)
    assert response.status_code == 403 # Forbidden
    assert "doesn't have enough privileges" in response.json()["detail"]

def test_create_product_invalid_data(client: TestClient, admin_auth_headers: dict):
    """Test creating a product with invalid data (e.g., negative price)."""
    product_data = {"description": "Invalid Price Product", "sale_value": -5.0, "initial_stock": 10}
    response = client.post("/products/", json=product_data, headers=admin_auth_headers)
    assert response.status_code == 422 # Validation error

# Test reading products (no auth required by default)
def test_read_products(client: TestClient, db_session: Session):
    """Test reading a list of products."""
    # Create some products first (directly via service for setup)
    product_service.create_product(db_session, schemas.ProductCreate(description="Product A", sale_value=10.0, initial_stock=5))
    product_service.create_product(db_session, schemas.ProductCreate(description="Product B", sale_value=25.50, initial_stock=10, section="Category X"))

    response = client.get("/products/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    descriptions = [p["description"] for p in data]
    assert "Product A" in descriptions
    assert "Product B" in descriptions

def test_read_products_filtered(client: TestClient, db_session: Session):
    """Test reading products with filters."""
    product_service.create_product(db_session, schemas.ProductCreate(description="Filter Prod 1", sale_value=50.0, initial_stock=2, section="Filter Section"))
    product_service.create_product(db_session, schemas.ProductCreate(description="Filter Prod 2", sale_value=150.0, initial_stock=3, section="Another Section"))

    # Filter by category/section
    response_cat = client.get("/products/?category=Filter Section")
    assert response_cat.status_code == 200
    data_cat = response_cat.json()
    assert len(data_cat) == 1
    assert data_cat[0]["description"] == "Filter Prod 1"

    # Filter by price range
    response_price = client.get("/products/?min_price=100&max_price=200")
    assert response_price.status_code == 200
    data_price = response_price.json()
    assert len(data_price) == 1
    assert data_price[0]["description"] == "Filter Prod 2"

def test_read_specific_product(client: TestClient, db_session: Session):
    """Test reading a specific product by ID."""
    created_product = product_service.create_product(db_session, schemas.ProductCreate(description="Specific Product", sale_value=99.99, initial_stock=1))

    response = client.get(f"/products/{created_product.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created_product.id
    assert data["description"] == "Specific Product"

def test_read_nonexistent_product(client: TestClient):
    """Test reading a product that does not exist."""
    response = client.get("/products/99999")
    assert response.status_code == 404
    assert "Product not found" in response.json()["detail"]

# Test updating products (requires admin)
def test_update_product(client: TestClient, db_session: Session, admin_auth_headers: dict):
    """Test successfully updating a product by an admin."""
    created_product = product_service.create_product(db_session, schemas.ProductCreate(description="Update Me Prod", sale_value=5.0, initial_stock=10))
    update_data = {"description": "Updated Product Desc", "current_stock": 5}

    response = client.put(f"/products/{created_product.id}", json=update_data, headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created_product.id
    assert data["description"] == "Updated Product Desc"
    assert data["current_stock"] == 5
    assert data["sale_value"] == 5.0 # Not updated

    # Verify in DB
    db_product = product_service.get_product(db_session, created_product.id)
    db_session.refresh(db_product) # Refresh before assert
    assert db_product.description == "Updated Product Desc"
    assert db_product.current_stock == 5

def test_update_product_non_admin(client: TestClient, db_session: Session, auth_headers: dict):
    """Test updating a product by a non-admin user (should fail)."""
    created_product = product_service.create_product(db_session, schemas.ProductCreate(description="Cant Update Prod", sale_value=1.0, initial_stock=1))
    update_data = {"description": "Attempted Update"}
    response = client.put(f"/products/{created_product.id}", json=update_data, headers=auth_headers)
    assert response.status_code == 403

def test_update_nonexistent_product(client: TestClient, admin_auth_headers: dict):
    """Test updating a product that does not exist."""
    update_data = {"description": "Ghost Product"}
    response = client.put("/products/99999", json=update_data, headers=admin_auth_headers)
    assert response.status_code == 404

# Test deleting products (requires admin)
def test_delete_product(client: TestClient, db_session: Session, admin_auth_headers: dict):
    """Test successfully deleting a product by an admin."""
    created_product = product_service.create_product(db_session, schemas.ProductCreate(description="Delete Me Prod", sale_value=0.50, initial_stock=2))

    response = client.delete(f"/products/{created_product.id}", headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created_product.id
    assert data["description"] == "Delete Me Prod"

    # Verify deletion in DB
    db_product = product_service.get_product(db_session, created_product.id)
    assert db_product is None

def test_delete_product_non_admin(client: TestClient, db_session: Session, auth_headers: dict):
    """Test deleting a product by a non-admin user (should fail)."""
    created_product = product_service.create_product(db_session, schemas.ProductCreate(description="Cant Delete Prod", sale_value=1.0, initial_stock=1))
    response = client.delete(f"/products/{created_product.id}", headers=auth_headers)
    assert response.status_code == 403

def test_delete_nonexistent_product(client: TestClient, admin_auth_headers: dict):
    """Test deleting a product that does not exist."""
    response = client.delete("/products/99999", headers=admin_auth_headers)
    assert response.status_code == 404


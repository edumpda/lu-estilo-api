import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src import schemas
from src.services import client_service, product_service, order_service
from src.models import Client, Product, Order, OrderItem, User, OrderStatus

@pytest.fixture(scope="function")
def setup_order_data(db_session: Session) -> dict:
    """Fixture to create a client and products needed for order tests."""
    test_client = client_service.create_client(db_session, schemas.ClientCreate(name="Order Client", email="order_client@example.com", cpf="11223344556"))
    product1 = product_service.create_product(db_session, schemas.ProductCreate(description="Order Prod 1", sale_value=10.00, initial_stock=20, current_stock=20))
    product2 = product_service.create_product(db_session, schemas.ProductCreate(description="Order Prod 2", sale_value=5.50, initial_stock=10, current_stock=10))
    product_low_stock = product_service.create_product(db_session, schemas.ProductCreate(description="Low Stock Prod", sale_value=2.00, initial_stock=1, current_stock=1))
    return {"client": test_client, "product1": product1, "product2": product2, "product_low_stock": product_low_stock}

# Test order creation
def test_create_order(client: TestClient, db_session: Session, auth_headers: dict, setup_order_data: dict):
    """Test successful order creation."""
    client_id = setup_order_data["client"].id
    prod1_id = setup_order_data["product1"].id
    prod2_id = setup_order_data["product2"].id

    order_data = {
        "client_id": client_id,
        "items": [
            {"product_id": prod1_id, "quantity": 2},
            {"product_id": prod2_id, "quantity": 5}
        ]
    }

    response = client.post("/orders/", json=order_data, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["client_id"] == client_id
    assert data["status"] == OrderStatus.PENDING.value
    assert len(data["items"]) == 2
    assert data["total_value"] == (10.00 * 2) + (5.50 * 5) # 20 + 27.5 = 47.5

    # Verify stock update in DB
    prod1_db = product_service.get_product(db_session, prod1_id)
    prod2_db = product_service.get_product(db_session, prod2_id)
    db_session.refresh(prod1_db) # Refresh before assert
    db_session.refresh(prod2_db) # Refresh before assert
    assert prod1_db.current_stock == 18 # Initial 20 - 2
    assert prod2_db.current_stock == 5  # Initial 10 - 5

def test_create_order_insufficient_stock(client: TestClient, auth_headers: dict, setup_order_data: dict):
    """Test creating an order where product stock is insufficient."""
    client_id = setup_order_data["client"].id
    prod_low_stock_id = setup_order_data["product_low_stock"].id

    order_data = {
        "client_id": client_id,
        "items": [
            {"product_id": prod_low_stock_id, "quantity": 2} # Request 2, only 1 available
        ]
    }

    response = client.post("/orders/", json=order_data, headers=auth_headers)
    assert response.status_code == 400
    assert "Insufficient stock" in response.json()["detail"]

def test_create_order_nonexistent_product(client: TestClient, auth_headers: dict, setup_order_data: dict):
    """Test creating an order with a product ID that does not exist."""
    client_id = setup_order_data["client"].id
    order_data = {
        "client_id": client_id,
        "items": [
            {"product_id": 99999, "quantity": 1}
        ]
    }
    response = client.post("/orders/", json=order_data, headers=auth_headers)
    assert response.status_code == 400 # Or 404 depending on how service handles it
    assert "not found" in response.json()["detail"]

def test_create_order_nonexistent_client(client: TestClient, auth_headers: dict, setup_order_data: dict):
    """Test creating an order for a client ID that does not exist."""
    prod1_id = setup_order_data["product1"].id
    order_data = {
        "client_id": 99999,
        "items": [
            {"product_id": prod1_id, "quantity": 1}
        ]
    }
    response = client.post("/orders/", json=order_data, headers=auth_headers)
    assert response.status_code == 404
    assert "Client with ID 99999 not found" in response.json()["detail"]

# Test reading orders
def test_read_orders(client: TestClient, db_session: Session, auth_headers: dict, setup_order_data: dict):
    """Test reading a list of orders."""
    # Create an order first
    order_service.create_order(db_session, schemas.OrderCreate(
        client_id=setup_order_data["client"].id,
        items=[schemas.OrderItemCreate(product_id=setup_order_data["product1"].id, quantity=1)]
    ))

    response = client.get("/orders/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["client_id"] == setup_order_data["client"].id

def test_read_orders_filtered(client: TestClient, db_session: Session, auth_headers: dict, setup_order_data: dict):
    """Test reading orders with filters."""
    client_id = setup_order_data["client"].id
    prod1_id = setup_order_data["product1"].id

    # Create order 1
    order1 = order_service.create_order(db_session, schemas.OrderCreate(
        client_id=client_id,
        items=[schemas.OrderItemCreate(product_id=prod1_id, quantity=1)]
    ))
    # Create order 2 and update status
    order2 = order_service.create_order(db_session, schemas.OrderCreate(
        client_id=client_id,
        items=[schemas.OrderItemCreate(product_id=setup_order_data["product2"].id, quantity=1)]
    ))
    order_service.update_order_status(db_session, order2.id, OrderStatus.SHIPPED)

    # Filter by client_id
    response_client = client.get(f"/orders/?client_id={client_id}", headers=auth_headers)
    assert response_client.status_code == 200
    assert len(response_client.json()) >= 2

    # Filter by status
    response_status = client.get(f"/orders/?status={OrderStatus.SHIPPED.value}", headers=auth_headers)
    assert response_status.status_code == 200
    data_status = response_status.json()
    assert len(data_status) == 1
    assert data_status[0]["id"] == order2.id
    assert data_status[0]["status"] == OrderStatus.SHIPPED.value

    # Filter by order_id
    response_id = client.get(f"/orders/?order_id={order1.id}", headers=auth_headers)
    assert response_id.status_code == 200
    data_id = response_id.json()
    assert len(data_id) == 1
    assert data_id[0]["id"] == order1.id

def test_read_specific_order(client: TestClient, db_session: Session, auth_headers: dict, setup_order_data: dict):
    """Test reading a specific order by ID."""
    created_order = order_service.create_order(db_session, schemas.OrderCreate(
        client_id=setup_order_data["client"].id,
        items=[schemas.OrderItemCreate(product_id=setup_order_data["product1"].id, quantity=1)]
    ))

    response = client.get(f"/orders/{created_order.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created_order.id
    assert data["client_id"] == setup_order_data["client"].id
    assert len(data["items"]) == 1
    assert data["items"][0]["product_id"] == setup_order_data["product1"].id

def test_read_nonexistent_order(client: TestClient, auth_headers: dict):
    """Test reading an order that does not exist."""
    response = client.get("/orders/99999", headers=auth_headers)
    assert response.status_code == 404
    assert "Order not found" in response.json()["detail"]

# Test updating orders (requires admin)
def test_update_order_status(client: TestClient, db_session: Session, admin_auth_headers: dict, setup_order_data: dict):
    """Test successfully updating an order's status by an admin."""
    created_order = order_service.create_order(db_session, schemas.OrderCreate(
        client_id=setup_order_data["client"].id,
        items=[schemas.OrderItemCreate(product_id=setup_order_data["product1"].id, quantity=1)]
    ))
    assert created_order.status == OrderStatus.PENDING

    update_data = {"status": OrderStatus.PROCESSING.value}
    response = client.put(f"/orders/{created_order.id}", json=update_data, headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created_order.id
    assert data["status"] == OrderStatus.PROCESSING.value

    # Verificar o status atualizado através da API em vez de diretamente pelo serviço
    # Isso garante que estamos testando o comportamento real da aplicação
    response_get = client.get(f"/orders/{created_order.id}", headers=admin_auth_headers)
    assert response_get.status_code == 200
    data_get = response_get.json()
    assert data_get["status"] == OrderStatus.PROCESSING.value

def test_update_order_status_non_admin(client: TestClient, db_session: Session, auth_headers: dict, setup_order_data: dict):
    """Test updating order status by a non-admin user (should fail)."""
    created_order = order_service.create_order(db_session, schemas.OrderCreate(
        client_id=setup_order_data["client"].id,
        items=[schemas.OrderItemCreate(product_id=setup_order_data["product1"].id, quantity=1)]
    ))
    update_data = {"status": OrderStatus.SHIPPED.value}
    response = client.put(f"/orders/{created_order.id}", json=update_data, headers=auth_headers)
    assert response.status_code == 403 # Forbidden

def test_update_nonexistent_order(client: TestClient, admin_auth_headers: dict):
    """Test updating an order that does not exist."""
    update_data = {"status": OrderStatus.DELIVERED.value}
    response = client.put("/orders/99999", json=update_data, headers=admin_auth_headers)
    assert response.status_code == 404

# Test deleting orders (requires admin)
def test_delete_order(client: TestClient, db_session: Session, admin_auth_headers: dict, setup_order_data: dict):
    """Test successfully deleting an order by an admin."""
    # Note: Stock is NOT returned by default on delete in current service logic
    prod_id = setup_order_data["product2"].id
    initial_stock = product_service.get_product(db_session, prod_id).current_stock

    created_order = order_service.create_order(db_session, schemas.OrderCreate(
        client_id=setup_order_data["client"].id,
        items=[schemas.OrderItemCreate(product_id=prod_id, quantity=3)]
    ))
    stock_after_order = product_service.get_product(db_session, prod_id).current_stock
    assert stock_after_order == initial_stock - 3

    response = client.delete(f"/orders/{created_order.id}", headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created_order.id

    # Verify deletion in DB
    db_order = order_service.get_order(db_session, created_order.id)
    assert db_order is None

    # Verify stock was NOT returned (as per current logic)
    stock_after_delete = product_service.get_product(db_session, prod_id).current_stock
    assert stock_after_delete == stock_after_order

def test_delete_order_non_admin(client: TestClient, db_session: Session, auth_headers: dict, setup_order_data: dict):
    """Test deleting an order by a non-admin user (should fail)."""
    created_order = order_service.create_order(db_session, schemas.OrderCreate(
        client_id=setup_order_data["client"].id,
        items=[schemas.OrderItemCreate(product_id=setup_order_data["product1"].id, quantity=1)]
    ))
    response = client.delete(f"/orders/{created_order.id}", headers=auth_headers)
    assert response.status_code == 403

def test_delete_nonexistent_order(client: TestClient, admin_auth_headers: dict):
    """Test deleting an order that does not exist."""
    response = client.delete("/orders/99999", headers=admin_auth_headers)
    assert response.status_code == 404


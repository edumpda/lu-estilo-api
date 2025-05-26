import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src import schemas
from src.services import client_service
from src.models import Client, User # Import User for auth dependency

# Test client creation
def test_create_client(client: TestClient, db_session: Session, auth_headers: dict):
    """Test successful client creation."""
    client_data = {
        "name": "Test Client",
        "email": "client@example.com",
        "cpf": "12345678901", # 11 digits
        "phone": "11999998888",
        "address": "123 Test St"
    }
    response = client.post("/clients/", json=client_data, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == client_data["name"]
    assert data["email"] == client_data["email"]
    assert data["cpf"] == client_data["cpf"]
    assert "id" in data

    # Verify in DB
    db_client = client_service.get_client(db_session, data["id"])
    assert db_client is not None
    assert db_client.name == client_data["name"]

def test_create_client_duplicate_email(client: TestClient, db_session: Session, auth_headers: dict):
    """Test creating a client with an email that already exists."""
    # Create first client
    client_data1 = {"name": "Client One", "email": "duplicate@example.com", "cpf": "11122233344"}
    client.post("/clients/", json=client_data1, headers=auth_headers)

    # Attempt to create second client with same email
    client_data2 = {"name": "Client Two", "email": "duplicate@example.com", "cpf": "55566677788"}
    response = client.post("/clients/", json=client_data2, headers=auth_headers)
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]

def test_create_client_duplicate_cpf(client: TestClient, db_session: Session, auth_headers: dict):
    """Test creating a client with a CPF that already exists."""
    client_data1 = {"name": "Client CPF1", "email": "cpf1@example.com", "cpf": "99988877766"}
    client.post("/clients/", json=client_data1, headers=auth_headers)

    client_data2 = {"name": "Client CPF2", "email": "cpf2@example.com", "cpf": "99988877766"}
    response = client.post("/clients/", json=client_data2, headers=auth_headers)
    assert response.status_code == 400
    assert "CPF already registered" in response.json()["detail"]

def test_create_client_invalid_cpf_format(client: TestClient, auth_headers: dict):
    """Test creating a client with an invalid CPF format."""
    client_data = {"name": "Invalid CPF Client", "email": "invalidcpf@example.com", "cpf": "12345"}
    response = client.post("/clients/", json=client_data, headers=auth_headers)
    assert response.status_code == 422 # Validation error

# Test reading clients
def test_read_clients(client: TestClient, db_session: Session, auth_headers: dict):
    """Test reading a list of clients."""
    # Create some clients first
    client_service.create_client(db_session, schemas.ClientCreate(name="Alice", email="alice@example.com", cpf="10101010101"))
    client_service.create_client(db_session, schemas.ClientCreate(name="Bob", email="bob@example.com", cpf="20202020202"))

    response = client.get("/clients/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Check if at least the created clients are present (might include clients from other tests if session isn't fully isolated)
    assert len(data) >= 2
    emails = [c["email"] for c in data]
    assert "alice@example.com" in emails
    assert "bob@example.com" in emails

def test_read_clients_filtered(client: TestClient, db_session: Session, auth_headers: dict):
    """Test reading clients with name and email filters."""
    client_service.create_client(db_session, schemas.ClientCreate(name="Charlie Filter", email="charlie@filter.com", cpf="30303030303"))
    client_service.create_client(db_session, schemas.ClientCreate(name="David Filter", email="david@filter.com", cpf="40404040404"))

    # Filter by name
    response_name = client.get("/clients/?name=Charlie", headers=auth_headers)
    assert response_name.status_code == 200
    data_name = response_name.json()
    assert len(data_name) == 1
    assert data_name[0]["name"] == "Charlie Filter"

    # Filter by email
    response_email = client.get("/clients/?email=david@filter.com", headers=auth_headers)
    assert response_email.status_code == 200
    data_email = response_email.json()
    assert len(data_email) == 1
    assert data_email[0]["email"] == "david@filter.com"

def test_read_specific_client(client: TestClient, db_session: Session, auth_headers: dict):
    """Test reading a specific client by ID."""
    created_client = client_service.create_client(db_session, schemas.ClientCreate(name="Specific Client", email="specific@example.com", cpf="50505050505"))

    response = client.get(f"/clients/{created_client.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created_client.id
    assert data["name"] == "Specific Client"
    assert data["email"] == "specific@example.com"

def test_read_nonexistent_client(client: TestClient, auth_headers: dict):
    """Test reading a client that does not exist."""
    response = client.get("/clients/99999", headers=auth_headers)
    assert response.status_code == 404
    assert "Client not found" in response.json()["detail"]

# Test updating clients
def test_update_client(client: TestClient, db_session: Session, auth_headers: dict):
    """Test successfully updating a client."""
    created_client = client_service.create_client(db_session, schemas.ClientCreate(name="Update Me", email="update@example.com", cpf="60606060606"))
    update_data = {"name": "Updated Name", "phone": "1122334455"}

    response = client.put(f"/clients/{created_client.id}", json=update_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created_client.id
    assert data["name"] == "Updated Name"
    assert data["email"] == "update@example.com" # Email not updated
    assert data["phone"] == "1122334455"

    # Verify in DB
    db_client = client_service.get_client(db_session, created_client.id)
    db_session.refresh(db_client) # Add refresh
    assert db_client.name == "Updated Name"
    assert db_client.phone == "1122334455"

def test_update_client_email_conflict(client: TestClient, db_session: Session, auth_headers: dict):
    """Test updating a client's email to one that already exists for another client."""
    client1 = client_service.create_client(db_session, schemas.ClientCreate(name="Client A", email="emailA@example.com", cpf="70707070707"))
    client2 = client_service.create_client(db_session, schemas.ClientCreate(name="Client B", email="emailB@example.com", cpf="80808080808"))

    update_data = {"email": client1.email} # Try to update client B's email to client A's email
    response = client.put(f"/clients/{client2.id}", json=update_data, headers=auth_headers)
    assert response.status_code == 400
    assert "Email already registered by another client" in response.json()["detail"]

def test_update_nonexistent_client(client: TestClient, auth_headers: dict):
    """Test updating a client that does not exist."""
    update_data = {"name": "Ghost Client"}
    response = client.put("/clients/99999", json=update_data, headers=auth_headers)
    assert response.status_code == 404
    assert "Client not found" in response.json()["detail"]

# Test deleting clients
def test_delete_client(client: TestClient, db_session: Session, auth_headers: dict):
    """Test successfully deleting a client."""
    created_client = client_service.create_client(db_session, schemas.ClientCreate(name="Delete Me", email="delete@example.com", cpf="90909090909"))

    response = client.delete(f"/clients/{created_client.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created_client.id
    assert data["name"] == "Delete Me"

    # Verify deletion in DB
    db_client = client_service.get_client(db_session, created_client.id)
    assert db_client is None

def test_delete_nonexistent_client(client: TestClient, auth_headers: dict):
    """Test deleting a client that does not exist."""
    response = client.delete("/clients/99999", headers=auth_headers)
    assert response.status_code == 404
    assert "Client not found" in response.json()["detail"]


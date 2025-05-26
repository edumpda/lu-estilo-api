import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src import schemas
from src.services import user_service
from src.models import User

# Test user registration
def test_register_user(client: TestClient, db_session: Session):
    """Test successful user registration."""
    response = client.post(
        "/auth/register",
        json={"email": "newuser@example.com", "password": "newpassword", "is_admin": False}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "id" in data
    assert data["is_admin"] == False
    assert data["is_active"] == True # Default should be active

    # Verify user exists in DB
    user = user_service.get_user_by_email(db_session, "newuser@example.com")
    assert user is not None
    assert user.email == "newuser@example.com"

def test_register_existing_user(client: TestClient, test_user: User):
    """Test registration attempt with an existing email."""
    response = client.post(
        "/auth/register",
        json={"email": test_user.email, "password": "anotherpassword"}
    )
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]

# Test user login
def test_login_user(client: TestClient, test_user: User):
    """Test successful user login."""
    login_data = {"username": test_user.email, "password": "testpassword"}
    response = client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password(client: TestClient, test_user: User):
    """Test login attempt with incorrect password."""
    login_data = {"username": test_user.email, "password": "wrongpassword"}
    response = client.post("/auth/login", data=login_data)
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]

def test_login_nonexistent_user(client: TestClient):
    """Test login attempt with a non-existent email."""
    login_data = {"username": "nosuchuser@example.com", "password": "password"}
    response = client.post("/auth/login", data=login_data)
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]

# Test refresh token endpoint (currently placeholder)
def test_refresh_token_not_implemented(client: TestClient):
    """Test the refresh token endpoint which is not implemented."""
    # This test assumes no valid refresh token mechanism is in place yet
    response = client.post("/auth/refresh-token")
    assert response.status_code == 501 # Or 404 if route doesn't exist, but we defined it
    assert "not fully implemented" in response.json()["detail"]



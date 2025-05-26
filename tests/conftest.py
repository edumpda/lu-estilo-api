import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from src.main import app
from src.core.database import Base, get_db
from src.models import User # Import User model
from src.core.security import get_password_hash # Import hashing function

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}, # Needed only for SQLite
    poolclass=StaticPool, # Use StaticPool for SQLite in-memory
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency override for testing database
def override_get_db():
    """Override get_db dependency to use the testing database session."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Fixture to create tables once before all tests and drop them after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function", autouse=True)
def clean_db_tables():
    """Fixture to clean all tables after each test function."""
    yield # Run the test
    # Clean up data after test
    with engine.connect() as connection:
        transaction = connection.begin()
        # Find all tables and delete data
        # Order matters for foreign key constraints if not using TRUNCATE CASCADE (SQLite doesn't support CASCADE easily)
        # We need to delete in reverse order of creation or dependency
        # A simpler approach for testing might be to drop/create tables per test, but let's try delete first.
        # Get table names in a safe order (children first)
        table_names = reversed(Base.metadata.sorted_tables)
        for table in table_names:
            connection.execute(text(f"DELETE FROM {table.name}"))
        transaction.commit()


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Provides a TestClient instance for making API requests."""
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="function")
def db_session() -> Session:
    """Provides a database session for direct interaction in tests."""
    # This session is managed by the override_get_db for the app
    # For direct use in tests, we can get one here
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

# Fixtures to create users remain the same, but will now operate on a clean DB for each test
@pytest.fixture(scope="function")
def test_user(db_session: Session) -> User:
    """Creates a test user in the database for testing purposes."""
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword"),
        is_active=True,
        is_admin=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def test_admin_user(db_session: Session) -> User:
    """Creates a test admin user in the database."""
    admin_user = User(
        email="admin@example.com",
        hashed_password=get_password_hash("adminpassword"),
        is_active=True,
        is_admin=True
    )
    db_session.add(admin_user)
    db_session.commit()
    db_session.refresh(admin_user)
    return admin_user

@pytest.fixture(scope="function")
def auth_headers(client: TestClient, test_user: User) -> dict:
    """Provides authorization headers for a regular test user."""
    login_data = {"username": test_user.email, "password": "testpassword"}
    response = client.post("/auth/login", data=login_data)
    if response.status_code != 200:
        pytest.fail(f"Login failed for test_user: {response.text}")
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
def admin_auth_headers(client: TestClient, test_admin_user: User) -> dict:
    """Provides authorization headers for an admin test user."""
    login_data = {"username": test_admin_user.email, "password": "adminpassword"}
    response = client.post("/auth/login", data=login_data)
    if response.status_code != 200:
        pytest.fail(f"Login failed for test_admin_user: {response.text}")
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


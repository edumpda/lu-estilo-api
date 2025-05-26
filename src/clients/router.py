from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import schemas, services
from ..core.database import get_db
from ..auth.dependencies import get_current_active_user # Assuming all logged-in users can manage clients for now
from ..models.user import User # To use User model for dependency

router = APIRouter()

@router.post("/", response_model=schemas.ClientRead, status_code=status.HTTP_201_CREATED)
def create_client(
    client: schemas.ClientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Creates a new client. Requires authentication."""
    # Check for existing email
    db_client_email = services.client_service.get_client_by_email(db, email=client.email)
    if db_client_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    # Check for existing CPF
    db_client_cpf = services.client_service.get_client_by_cpf(db, cpf=client.cpf)
    if db_client_cpf:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CPF already registered")

    return services.client_service.create_client(db=db, client=client)

@router.get("/", response_model=List[schemas.ClientRead])
def read_clients(
    skip: int = 0,
    limit: int = 100,
    name: Optional[str] = Query(None, description="Filter by client name (case-insensitive)"),
    email: Optional[str] = Query(None, description="Filter by client email (case-insensitive)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retrieves a list of clients with pagination and filtering. Requires authentication."""
    clients = services.client_service.get_clients(db, skip=skip, limit=limit, name=name, email=email)
    return clients

@router.get("/{client_id}", response_model=schemas.ClientRead)
def read_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retrieves a specific client by ID. Requires authentication."""
    db_client = services.client_service.get_client(db, client_id=client_id)
    if db_client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return db_client

@router.put("/{client_id}", response_model=schemas.ClientRead)
def update_client(
    client_id: int,
    client: schemas.ClientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Updates a specific client by ID. Requires authentication."""
    # Check if updated email already exists for another client
    if client.email:
        existing_client = services.client_service.get_client_by_email(db, email=client.email)
        if existing_client and existing_client.id != client_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered by another client")

    updated_client = services.client_service.update_client(db=db, client_id=client_id, client_update=client)
    if updated_client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return updated_client

@router.delete("/{client_id}", response_model=schemas.ClientRead)
def delete_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user) # Or get_current_admin_user if required
):
    """Deletes a specific client by ID. Requires authentication."""
    deleted_client = services.client_service.delete_client(db=db, client_id=client_id)
    if deleted_client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    # Consider implications: should orders be deleted/anonymized?
    # For now, just delete the client.
    return deleted_client


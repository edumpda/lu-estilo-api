from sqlalchemy.orm import Session
from ..models.client import Client
from ..schemas.client import ClientCreate, ClientUpdate
from typing import List, Optional


def get_client(db: Session, client_id: int) -> Optional[Client]:
    """Fetches a single client by ID."""
    return db.query(Client).filter(Client.id == client_id).first()

def get_clients(db: Session, skip: int = 0, limit: int = 100, name: Optional[str] = None, email: Optional[str] = None) -> List[Client]:
    """Fetches a list of clients with optional filtering and pagination."""
    query = db.query(Client)
    if name:
        query = query.filter(Client.name.ilike(f"%{name}%")) # Case-insensitive search
    if email:
        query = query.filter(Client.email.ilike(f"%{email}%"))
    return query.offset(skip).limit(limit).all()

def get_client_by_email(db: Session, email: str) -> Optional[Client]:
    """Fetches a client by email."""
    return db.query(Client).filter(Client.email == email).first()

def get_client_by_cpf(db: Session, cpf: str) -> Optional[Client]:
    """Fetches a client by CPF."""
    return db.query(Client).filter(Client.cpf == cpf).first()

def create_client(db: Session, client: ClientCreate) -> Client:
    """Creates a new client."""
    db_client = Client(**client.model_dump())
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client

def update_client(db: Session, client_id: int, client_update: ClientUpdate) -> Optional[Client]:
    """Updates an existing client."""
    db_client = get_client(db, client_id)
    if not db_client:
        return None

    update_data = client_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_client, key, value)

    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client

def delete_client(db: Session, client_id: int) -> Optional[Client]:
    """Deletes a client."""
    db_client = get_client(db, client_id)
    if not db_client:
        return None
    db.delete(db_client)
    db.commit()
    return db_client


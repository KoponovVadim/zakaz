from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Client, Order, Site, User
from app.schemas.client import ClientCreate, ClientRead, ClientUpdate

router = APIRouter(dependencies=[Depends(get_current_user)])


def serialize_client(db: Session, client: Client) -> ClientRead:
    sites_count = db.scalar(select(func.count(Site.id)).where(Site.client_id == client.id)) or 0
    orders_count = db.scalar(select(func.count(Order.id)).where(Order.client_id == client.id)) or 0
    data = ClientRead.model_validate(client).model_dump()
    data["sites_count"] = sites_count
    data["orders_count"] = orders_count
    return ClientRead(**data)


@router.get("", response_model=list[ClientRead])
def list_clients(db: Session = Depends(get_db)):
    clients = db.scalars(select(Client).order_by(Client.name)).all()
    return [serialize_client(db, client) for client in clients]


@router.post("", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
def create_client(payload: ClientCreate, db: Session = Depends(get_db)):
    client = Client(name=payload.name, comment=payload.comment)
    db.add(client)
    db.commit()
    db.refresh(client)
    return serialize_client(db, client)


@router.get("/{client_id}", response_model=ClientRead)
def get_client(client_id: int, db: Session = Depends(get_db)):
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return serialize_client(db, client)


@router.put("/{client_id}", response_model=ClientRead)
def update_client(client_id: int, payload: ClientUpdate, db: Session = Depends(get_db)):
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    client.name = payload.name
    client.comment = payload.comment
    db.commit()
    db.refresh(client)
    return serialize_client(db, client)


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(client_id: int, db: Session = Depends(get_db)):
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    if db.scalar(select(func.count(Site.id)).where(Site.client_id == client.id)):
        raise HTTPException(status_code=409, detail="Client has sites")
    db.delete(client)
    db.commit()
    return None

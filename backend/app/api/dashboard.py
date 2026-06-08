from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Client, Order, Site
from app.services.analytics_service import dashboard_summary

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    return dashboard_summary(db)


@router.get("/recent-orders")
def recent_orders(db: Session = Depends(get_db)):
    clients = {client.id: client.name for client in db.scalars(select(Client)).all()}
    sites = {site.id: site.name for site in db.scalars(select(Site)).all()}
    orders = db.scalars(select(Order).order_by(Order.created_at.desc()).limit(10)).all()
    return [
        {
            "id": order.id,
            "client_name": clients.get(order.client_id),
            "site_name": sites.get(order.site_id),
            "source_type": order.source_type,
            "external_number": order.external_number,
            "customer_name": order.customer_name,
            "customer_phone": order.customer_phone,
            "amount": order.amount,
            "currency": order.currency,
            "internal_status": order.internal_status,
            "created_at": order.created_at,
        }
        for order in orders
    ]

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Client, Order, Site


def dashboard_summary(db: Session) -> dict:
    return {
        "clients": db.scalar(select(func.count(Client.id))) or 0,
        "sites": db.scalar(select(func.count(Site.id))) or 0,
        "active_sites": db.scalar(select(func.count(Site.id)).where(Site.status == "active")) or 0,
        "orders": db.scalar(select(func.count(Order.id))) or 0,
        "new_orders": db.scalar(select(func.count(Order.id)).where(Order.internal_status == "new")) or 0,
    }

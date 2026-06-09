import csv
from datetime import datetime, time
from io import StringIO

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Client, Order, OrderComment, OrderStatusHistory, Site, User
from app.schemas.order import OrderCommentCreate, OrderCommentRead, OrderDetailRead, OrderRead, OrderStatusUpdate

router = APIRouter(dependencies=[Depends(get_current_user)])


def order_names(db: Session) -> tuple[dict[int, str], dict[int, str]]:
    clients = {client.id: client.name for client in db.scalars(select(Client)).all()}
    sites = {site.id: site.name for site in db.scalars(select(Site)).all()}
    return clients, sites


def serialize_order(order: Order, clients: dict[int, str], sites: dict[int, str]) -> OrderRead:
    data = OrderRead.model_validate(order).model_dump()
    data["client_name"] = clients.get(order.client_id)
    data["site_name"] = sites.get(order.site_id)
    return OrderRead(**data)


def serialize_order_detail(
    order: Order,
    clients: dict[int, str],
    sites: dict[int, str],
    status_history: list[OrderStatusHistory],
) -> OrderDetailRead:
    data = OrderDetailRead.model_validate(order).model_dump()
    data["client_name"] = clients.get(order.client_id)
    data["site_name"] = sites.get(order.site_id)
    data["comments"] = sorted(order.comments, key=lambda item: item.created_at, reverse=True)
    data["status_history"] = status_history
    return OrderDetailRead(**data)


def build_orders_query(
    date_from=None,
    date_to=None,
    client_id: int | None = None,
    site_id: int | None = None,
    source_type: str | None = None,
    source_form_id: str | None = None,
    source_form_name: str | None = None,
    internal_status: str | None = None,
    search: str | None = None,
):
    query = select(Order)
    if date_from:
        query = query.where(Order.created_at >= datetime.combine(datetime.fromisoformat(date_from).date(), time.min))
    if date_to:
        query = query.where(Order.created_at <= datetime.combine(datetime.fromisoformat(date_to).date(), time.max))
    if client_id:
        query = query.where(Order.client_id == client_id)
    if site_id:
        query = query.where(Order.site_id == site_id)
    if source_type:
        query = query.where(Order.source_type == source_type)
    if source_form_id:
        query = query.where(Order.source_form_id == source_form_id)
    if source_form_name:
        query = query.where(Order.source_form_name.ilike(f"%{source_form_name}%"))
    if internal_status:
        query = query.where(Order.internal_status == internal_status)
    if search:
        pattern = f"%{search}%"
        query = query.where(
            or_(
                Order.external_number.ilike(pattern),
                Order.customer_name.ilike(pattern),
                Order.customer_phone.ilike(pattern),
                Order.customer_email.ilike(pattern),
                Order.title.ilike(pattern),
                Order.message.ilike(pattern),
            )
        )
    return query


def get_order_or_404(db: Session, order_id: int) -> Order:
    order = db.scalar(
        select(Order)
        .options(selectinload(Order.items), selectinload(Order.comments))
        .where(Order.id == order_id)
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.get("", response_model=list[OrderRead])
def list_orders(
    date_from: str | None = None,
    date_to: str | None = None,
    client_id: int | None = None,
    site_id: int | None = None,
    source_type: str | None = None,
    source_form_id: str | None = None,
    source_form_name: str | None = None,
    internal_status: str | None = None,
    search: str | None = None,
    limit: int = Query(default=200, le=1000),
    db: Session = Depends(get_db),
):
    clients, sites = order_names(db)
    query = build_orders_query(
        date_from,
        date_to,
        client_id,
        site_id,
        source_type,
        source_form_id,
        source_form_name,
        internal_status,
        search,
    )
    orders = db.scalars(query.order_by(Order.created_at.desc()).limit(limit)).all()
    return [serialize_order(order, clients, sites) for order in orders]


@router.get("/export.csv")
def export_orders(
    date_from: str | None = None,
    date_to: str | None = None,
    client_id: int | None = None,
    site_id: int | None = None,
    source_type: str | None = None,
    source_form_id: str | None = None,
    source_form_name: str | None = None,
    internal_status: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
):
    clients = {client.id: client.name for client in db.scalars(select(Client)).all()}
    sites = {site.id: site.name for site in db.scalars(select(Site)).all()}
    query = build_orders_query(
        date_from,
        date_to,
        client_id,
        site_id,
        source_type,
        source_form_id,
        source_form_name,
        internal_status,
        search,
    )
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "date",
        "client",
        "site",
        "source_type",
        "source_form_name",
        "external_number",
        "customer_name",
        "customer_phone",
        "customer_email",
        "title",
        "message",
        "amount",
        "currency",
        "external_status",
        "internal_status",
    ])
    for order in db.scalars(query.order_by(Order.created_at.desc())).all():
        writer.writerow([
            order.external_created_at or order.created_at,
            clients.get(order.client_id, order.client_id),
            sites.get(order.site_id, order.site_id),
            order.source_type,
            order.source_form_name,
            order.external_number,
            order.customer_name,
            order.customer_phone,
            order.customer_email,
            order.title,
            order.message,
            order.amount,
            order.currency,
            order.external_status,
            order.internal_status,
        ])
    return Response("\ufeff" + output.getvalue(), media_type="text/csv; charset=utf-8")


@router.get("/{order_id}", response_model=OrderDetailRead)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = get_order_or_404(db, order_id)
    clients, sites = order_names(db)
    status_history = db.scalars(
        select(OrderStatusHistory)
        .where(OrderStatusHistory.order_id == order.id)
        .order_by(OrderStatusHistory.created_at.desc())
    ).all()
    return serialize_order_detail(order, clients, sites, status_history)


@router.put("/{order_id}/status", response_model=OrderRead)
def update_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = get_order_or_404(db, order_id)
    old_status = order.internal_status
    order.internal_status = payload.internal_status
    if old_status != payload.internal_status:
        db.add(
            OrderStatusHistory(
                order_id=order.id,
                user_id=user.id,
                old_status=old_status,
                new_status=payload.internal_status,
            )
        )
    db.commit()
    db.refresh(order)
    return order


@router.post("/{order_id}/comments", response_model=OrderCommentRead)
def add_order_comment(
    order_id: int,
    payload: OrderCommentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = get_order_or_404(db, order_id)
    comment = OrderComment(order_id=order.id, user_id=user.id, text=payload.text)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment

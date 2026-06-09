import csv
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from io import StringIO

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Client, Order, OrderItem, Site

router = APIRouter(dependencies=[Depends(get_current_user)])


def parse_day(value: str | None) -> date:
    if not value:
        return datetime.now(timezone.utc).date()
    return date.fromisoformat(value)


def day_start(value: date) -> datetime:
    return datetime.combine(value, time.min, tzinfo=timezone.utc)


def next_month(value: date) -> date:
    if value.month == 12:
        return date(value.year + 1, 1, 1)
    return date(value.year, value.month + 1, 1)


def period_bounds(mode: str, value: str | None) -> tuple[date, date]:
    current = parse_day(value)
    if mode == "day":
        return current, current
    if mode == "week":
        start = current - timedelta(days=current.weekday())
        return start, start + timedelta(days=6)
    if mode == "month":
        start = date(current.year, current.month, 1)
        return start, next_month(start) - timedelta(days=1)
    if mode == "year":
        return date(current.year, 1, 1), date(current.year, 12, 31)
    return current, current


def work_datetime():
    return func.coalesce(Order.created_at_source, Order.received_at)


def filters_query(
    query,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
    client_id: int | None = None,
    site_id: int | None = None,
    source_type: str | None = None,
    source_form_id: str | None = None,
    internal_status: str | None = None,
    external_status: str | None = None,
    search: str | None = None,
):
    work_dt = work_datetime()
    if date_from:
        query = query.where(work_dt >= day_start(date_from))
    if date_to:
        query = query.where(work_dt < day_start(date_to + timedelta(days=1)))
    if client_id:
        query = query.where(Order.client_id == client_id)
    if site_id:
        query = query.where(Order.site_id == site_id)
    if source_type and source_type != "all":
        query = query.where(Order.source_type == source_type)
    if source_form_id:
        query = query.where(Order.source_form_id == source_form_id)
    if internal_status:
        query = query.where(Order.internal_status == internal_status)
    if external_status:
        query = query.where(Order.external_status == external_status)
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
                Order.source_form_name.ilike(pattern),
            )
        )
    return query


def query_params(
    client_id: int | None = None,
    site_id: int | None = None,
    source_type: str | None = None,
    source_form_id: str | None = None,
    internal_status: str | None = None,
    external_status: str | None = None,
    search: str | None = None,
) -> dict:
    return {
        "client_id": client_id,
        "site_id": site_id,
        "source_type": source_type,
        "source_form_id": source_form_id,
        "internal_status": internal_status,
        "external_status": external_status,
        "search": search,
    }


def amount(value) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value or 0))


def base_summary(db: Session, date_from: date, date_to: date, params: dict) -> dict:
    total_query = filters_query(select(func.count(Order.id)), date_from=date_from, date_to=date_to, **params)
    total_count = db.scalar(total_query) or 0

    requested_source = params.get("source_type")
    rsform_count = 0
    if requested_source in (None, "", "all", "rsform"):
        rsform_count = db.scalar(
            filters_query(
                select(func.count(Order.id)),
                date_from=date_from,
                date_to=date_to,
                **{**params, "source_type": "rsform"},
            )
        ) or 0

    virtuemart_count = 0
    revenue = Decimal("0")
    if requested_source in (None, "", "all", "virtuemart"):
        virtuemart_count = db.scalar(
            filters_query(
                select(func.count(Order.id)),
                date_from=date_from,
                date_to=date_to,
                **{**params, "source_type": "virtuemart"},
            )
        ) or 0
        revenue = amount(
            db.scalar(
                filters_query(
                    select(func.coalesce(func.sum(Order.amount), 0)),
                    date_from=date_from,
                    date_to=date_to,
                    **{**params, "source_type": "virtuemart"},
                )
            )
        )
    average = revenue / virtuemart_count if virtuemart_count else Decimal("0")

    status_counts = {"new": 0, "in_progress": 0, "done": 0, "cancelled": 0, "spam": 0}
    status_rows = db.execute(
        filters_query(
            select(Order.internal_status, func.count(Order.id)).group_by(Order.internal_status),
            date_from=date_from,
            date_to=date_to,
            **params,
        )
    ).all()
    for status, count in status_rows:
        status_counts[status or "new"] = count

    return {
        "total_count": total_count,
        "rsform_count": rsform_count,
        "virtuemart_count": virtuemart_count,
        "revenue": float(revenue),
        "average_order_amount": float(average),
        "status_counts": status_counts,
    }


def bucket_template(mode: str, start: date, end: date) -> list[dict]:
    buckets = []
    if mode == "day":
        for hour in range(24):
            buckets.append({"key": f"{hour:02d}", "date": start.isoformat(), "hour": hour, "label": f"{hour:02d}:00"})
        return buckets
    if mode in ("week", "month"):
        current = start
        while current <= end:
            buckets.append({"key": current.isoformat(), "date": current.isoformat(), "label": current.strftime("%d.%m")})
            current += timedelta(days=1)
        return buckets
    for month in range(1, 13):
        current = date(start.year, month, 1)
        buckets.append({"key": current.strftime("%Y-%m"), "date": current.isoformat(), "label": current.strftime("%m.%Y")})
    return buckets


def top_products(db: Session, date_from: date, date_to: date, params: dict) -> list[dict]:
    if params.get("source_type") == "rsform":
        return []
    query = (
        select(
            OrderItem.name,
            func.coalesce(OrderItem.sku, "").label("sku"),
            func.coalesce(func.sum(OrderItem.quantity), 0).label("quantity"),
            func.coalesce(func.sum(OrderItem.quantity * OrderItem.price), 0).label("total"),
        )
        .join(Order, Order.id == OrderItem.order_id)
        .where(Order.source_type == "virtuemart")
        .group_by(OrderItem.name, OrderItem.sku)
        .order_by(func.coalesce(func.sum(OrderItem.quantity), 0).desc())
        .limit(3)
    )
    query = filters_query(query, date_from=date_from, date_to=date_to, **{**params, "source_type": "virtuemart"})
    return [
        {"name": name, "sku": sku or None, "quantity": float(quantity or 0), "total": float(total or 0)}
        for name, sku, quantity, total in db.execute(query).all()
    ]


@router.get("/summary")
def calendar_summary(
    mode: str = Query(default="month", pattern="^(day|week|month|year)$"),
    selected_date: str | None = Query(default=None, alias="date"),
    client_id: int | None = None,
    site_id: int | None = None,
    source_type: str | None = None,
    source_form_id: str | None = None,
    internal_status: str | None = None,
    external_status: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
):
    date_from, date_to = period_bounds(mode, selected_date)
    params = query_params(client_id, site_id, source_type, source_form_id, internal_status, external_status, search)
    return {"mode": mode, "date_from": date_from.isoformat(), "date_to": date_to.isoformat(), **base_summary(db, date_from, date_to, params)}


@router.get("/buckets")
def calendar_buckets(
    mode: str = Query(default="month", pattern="^(day|week|month|year)$"),
    selected_date: str | None = Query(default=None, alias="date"),
    client_id: int | None = None,
    site_id: int | None = None,
    source_type: str | None = None,
    source_form_id: str | None = None,
    internal_status: str | None = None,
    external_status: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
):
    date_from, date_to = period_bounds(mode, selected_date)
    params = query_params(client_id, site_id, source_type, source_form_id, internal_status, external_status, search)
    buckets = {
        item["key"]: {
            **item,
            "total_count": 0,
            "rsform_count": 0,
            "virtuemart_count": 0,
            "revenue": 0.0,
            "average_order_amount": 0.0,
            "latest_orders": [],
            "top_products": [],
        }
        for item in bucket_template(mode, date_from, date_to)
    }

    if mode == "day":
        group_expr = func.to_char(work_datetime(), "HH24")
    elif mode in ("week", "month"):
        group_expr = func.to_char(work_datetime(), "YYYY-MM-DD")
    else:
        group_expr = func.to_char(work_datetime(), "YYYY-MM")

    rows = db.execute(
        filters_query(
            select(
                group_expr.label("bucket"),
                func.count(Order.id),
                func.sum(case((Order.source_type == "rsform", 1), else_=0)),
                func.sum(case((Order.source_type == "virtuemart", 1), else_=0)),
                func.coalesce(func.sum(case((Order.source_type == "virtuemart", Order.amount), else_=0)), 0),
            ).group_by(group_expr),
            date_from=date_from,
            date_to=date_to,
            **params,
        )
    ).all()

    for key, total, rsform, virtuemart, revenue in rows:
        if key in buckets:
            buckets[key]["total_count"] = total or 0
            buckets[key]["rsform_count"] = rsform or 0
            buckets[key]["virtuemart_count"] = virtuemart or 0
            buckets[key]["revenue"] = float(revenue or 0)
            buckets[key]["average_order_amount"] = float(amount(revenue) / virtuemart) if virtuemart else 0.0

    if mode == "week":
        for bucket in buckets.values():
            bucket_date = date.fromisoformat(bucket["date"])
            bucket["latest_orders"] = compact_orders(db, bucket_date, bucket_date, params, limit=5)
    if mode == "year":
        for bucket in buckets.values():
            month_start = date.fromisoformat(bucket["date"])
            month_end = next_month(month_start) - timedelta(days=1)
            bucket["top_products"] = top_products(db, month_start, month_end, params)

    return {"mode": mode, "date_from": date_from.isoformat(), "date_to": date_to.isoformat(), "buckets": list(buckets.values())}


def order_composition(order: Order) -> list[dict]:
    if order.source_type == "virtuemart":
        result = []
        for item in order.items:
            price = amount(item.price)
            quantity = amount(item.quantity)
            result.append(
                {
                    "name": item.name,
                    "sku": item.sku,
                    "quantity": float(quantity),
                    "price": float(price),
                    "total": float(quantity * price),
                }
            )
        return result

    fields = (order.raw_payload or {}).get("fields") or {}
    composition = [
        {"label": "Форма", "value": order.source_form_name or "Форма не определена"},
        {"label": "Имя", "value": order.customer_name},
        {"label": "Телефон", "value": order.customer_phone},
        {"label": "Email", "value": order.customer_email},
        {"label": "Сообщение", "value": order.message},
    ]
    for key, value in fields.items():
        if value and key not in ("name", "Name", "phone", "Phone", "email", "Email", "message", "Message"):
            composition.append({"label": key, "value": value})
    return [item for item in composition if item.get("value")]


def serialize_calendar_order(order: Order, clients: dict[int, str], sites: dict[int, str]) -> dict:
    work_dt = order.created_at_source or order.received_at
    return {
        "id": order.id,
        "work_datetime": work_dt.isoformat() if work_dt else None,
        "client_id": order.client_id,
        "client_name": clients.get(order.client_id),
        "site_id": order.site_id,
        "site_name": sites.get(order.site_id),
        "source_type": order.source_type,
        "external_id": order.external_id,
        "external_number": order.external_number,
        "source_form_id": order.source_form_id,
        "source_form_name": order.source_form_name,
        "customer_name": order.customer_name,
        "customer_phone": order.customer_phone,
        "customer_email": order.customer_email,
        "message": order.message,
        "amount": float(order.amount or 0) if order.amount is not None else None,
        "currency": order.currency,
        "external_status": order.external_status,
        "internal_status": order.internal_status,
        "raw_fields": (order.raw_payload or {}).get("fields") or {},
        "composition": order_composition(order),
    }


def calendar_orders_list(db: Session, date_from: date, date_to: date, params: dict, limit: int) -> list[dict]:
    query = filters_query(
        select(Order).options(selectinload(Order.items)),
        date_from=date_from,
        date_to=date_to,
        **params,
    ).order_by(work_datetime().desc(), Order.id.desc()).limit(limit)
    orders = db.scalars(query).all()
    clients = {client.id: client.name for client in db.scalars(select(Client)).all()}
    sites = {site.id: site.name for site in db.scalars(select(Site)).all()}
    return [serialize_calendar_order(order, clients, sites) for order in orders]


def compact_orders(db: Session, date_from: date, date_to: date, params: dict, limit: int) -> list[dict]:
    return [
        {
            "id": order["id"],
            "work_datetime": order["work_datetime"],
            "source_type": order["source_type"],
            "client_name": order["client_name"],
            "site_name": order["site_name"],
            "title": order["source_form_name"] or order["external_number"] or order["external_id"],
            "amount": order["amount"],
        }
        for order in calendar_orders_list(db, date_from, date_to, params, limit)
    ]


@router.get("/orders")
def calendar_orders(
    date_from: str,
    date_to: str,
    client_id: int | None = None,
    site_id: int | None = None,
    source_type: str | None = None,
    source_form_id: str | None = None,
    internal_status: str | None = None,
    external_status: str | None = None,
    search: str | None = None,
    limit: int = 1000,
    db: Session = Depends(get_db),
):
    params = query_params(client_id, site_id, source_type, source_form_id, internal_status, external_status, search)
    return calendar_orders_list(db, date.fromisoformat(date_from), date.fromisoformat(date_to), params, limit)


@router.get("/export.csv")
def calendar_export_csv(
    date_from: str,
    date_to: str,
    client_id: int | None = None,
    site_id: int | None = None,
    source_type: str | None = None,
    source_form_id: str | None = None,
    internal_status: str | None = None,
    external_status: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
):
    params = query_params(client_id, site_id, source_type, source_form_id, internal_status, external_status, search)
    orders = calendar_orders_list(db, date.fromisoformat(date_from), date.fromisoformat(date_to), params, 10000)
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "date",
            "time",
            "client",
            "site",
            "source",
            "rsform_form",
            "virtuemart_number",
            "name",
            "phone",
            "email",
            "amount",
            "status",
            "composition",
        ]
    )
    for order in orders:
        work_dt = datetime.fromisoformat(order["work_datetime"]) if order["work_datetime"] else None
        composition = "; ".join(
            [
                f"{item.get('label') or item.get('name')}: {item.get('value') or item.get('quantity', '')}"
                for item in order["composition"]
            ]
        )
        writer.writerow(
            [
                work_dt.date().isoformat() if work_dt else "",
                work_dt.strftime("%H:%M") if work_dt else "",
                order["client_name"],
                order["site_name"],
                order["source_type"],
                order["source_form_name"],
                order["external_number"] if order["source_type"] == "virtuemart" else "",
                order["customer_name"],
                order["customer_phone"],
                order["customer_email"],
                order["amount"],
                order["internal_status"],
                composition,
            ]
        )
    return Response("\ufeff" + output.getvalue(), media_type="text/csv; charset=utf-8")

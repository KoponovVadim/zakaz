from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Order, OrderItem, Site, SyncCursor, SyncLog
from app.services.connector_client import call_connector


async def sync_site_source(base_url: str, secret: str, site_uid: str, source_type: str, since_id: str = "0"):
    return await call_connector(base_url, secret, site_uid, "sync", type=source_type, since_id=since_id)


def parse_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        normalized = str(value).replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        return None


def parse_decimal(value):
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def get_cursor(db: Session, site_id: int, source_type: str) -> SyncCursor:
    cursor = db.scalar(
        select(SyncCursor).where(SyncCursor.site_id == site_id, SyncCursor.source_type == source_type)
    )
    if cursor:
        return cursor
    cursor = SyncCursor(site_id=site_id, source_type=source_type, last_external_id="0")
    db.add(cursor)
    db.flush()
    return cursor


def save_connector_items(db: Session, site: Site, source_type: str, items: list[dict]) -> dict:
    created = 0
    updated = 0
    max_external_id = None

    for item in items:
        external_id = str(item.get("external_id") or item.get("id") or "")
        if not external_id:
            continue

        order = db.scalar(
            select(Order).where(
                Order.site_id == site.id,
                Order.source_type == source_type,
                Order.external_id == external_id,
            )
        )
        if not order:
            order = Order(
                client_id=site.client_id,
                site_id=site.id,
                source_type=source_type,
                external_id=external_id,
                internal_status="new",
            )
            db.add(order)
            created += 1
        else:
            updated += 1

        order.external_number = item.get("external_number") or item.get("number")
        order.external_created_at = parse_datetime(item.get("external_created_at") or item.get("created_at"))
        order.customer_name = item.get("customer_name")
        order.customer_phone = item.get("customer_phone")
        order.customer_email = item.get("customer_email")
        order.title = item.get("title")
        order.message = item.get("message")
        order.amount = parse_decimal(item.get("amount"))
        order.currency = item.get("currency")
        order.external_status = item.get("external_status") or item.get("status")
        order.raw_payload = item

        if source_type == "virtuemart":
            order.items.clear()
            for raw_item in item.get("items") or []:
                name = raw_item.get("name") or raw_item.get("product_name") or "Товар"
                order.items.append(
                    OrderItem(
                        sku=raw_item.get("sku"),
                        name=name,
                        quantity=parse_decimal(raw_item.get("quantity")) or Decimal("1"),
                        price=parse_decimal(raw_item.get("price")),
                    )
                )

        try:
            numeric_id = int(external_id)
            if max_external_id is None or numeric_id > int(max_external_id):
                max_external_id = external_id
        except ValueError:
            max_external_id = external_id

    return {"created": created, "updated": updated, "max_external_id": max_external_id}


async def run_site_sync(db: Session, site: Site, secret: str, source_type: str | None = None) -> dict:
    source_types = [
        source.source_type
        for source in site.sources
        if source.is_enabled and (source_type is None or source.source_type == source_type)
    ]
    totals = {"created": 0, "updated": 0, "sources": {}}

    for current_type in source_types:
        cursor = get_cursor(db, site.id, current_type)
        try:
            response = await sync_site_source(
                site.normalized_url,
                secret,
                site.site_uid,
                current_type,
                cursor.last_external_id or "0",
            )
            items = response.get("items", []) if isinstance(response, dict) else []
            result = save_connector_items(db, site, current_type, items)
            if result["max_external_id"]:
                cursor.last_external_id = str(result["max_external_id"])
            db.add(
                SyncLog(
                    site_id=site.id,
                    source_type=current_type,
                    action="sync",
                    status="ok",
                    message=f"Created {result['created']}, updated {result['updated']}",
                    payload={"items": len(items)},
                )
            )
            totals["created"] += result["created"]
            totals["updated"] += result["updated"]
            totals["sources"][current_type] = result
        except Exception as exc:
            db.add(
                SyncLog(
                    site_id=site.id,
                    source_type=current_type,
                    action="sync",
                    status="error",
                    message=str(exc),
                )
            )
            totals["sources"][current_type] = {"error": str(exc)}

    site.last_sync_at = datetime.now(timezone.utc)
    db.commit()
    return totals

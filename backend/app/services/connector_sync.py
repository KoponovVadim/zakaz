from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Order, OrderItem, RsformForm, Site, SyncCursor, SyncLog
from app.services.connector_client import call_connector


async def sync_site_source(
    base_url: str,
    secret: str,
    site_uid: str,
    source_type: str,
    since_id: str = "0",
    limit: int = 500,
):
    return await call_connector(base_url, secret, site_uid, "sync", type=source_type, since_id=since_id, limit=limit)


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


def clean_text(value, limit: int | None = None):
    if value in (None, ""):
        return None
    text = str(value).strip()
    if not text:
        return None
    if limit and len(text) > limit:
        return text[:limit]
    return text


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


def upsert_rsform_form(
    db: Session,
    site: Site,
    external_form_id: str | None,
    name: str | None,
    submissions_count: int | None = None,
) -> None:
    external_id = clean_text(external_form_id, 120)
    if not external_id:
        return

    form = db.scalar(
        select(RsformForm).where(RsformForm.site_id == site.id, RsformForm.external_form_id == external_id)
    )
    if not form:
        form = RsformForm(site_id=site.id, external_form_id=external_id)
        db.add(form)

    form.name = clean_text(name, 255) or form.name
    if submissions_count is not None:
        form.submissions_count = submissions_count
    form.last_seen_at = datetime.now(timezone.utc)


def save_discovered_rsform_forms(db: Session, site: Site, forms: list[dict]) -> None:
    for raw_form in forms:
        upsert_rsform_form(
            db,
            site,
            str(raw_form.get("form_id") or raw_form.get("external_form_id") or ""),
            raw_form.get("form_name") or raw_form.get("name"),
            int(raw_form.get("submissions_count") or 0),
        )


def save_connector_items(db: Session, site: Site, source_type: str, items: list[dict]) -> dict:
    created = 0
    updated = 0
    max_external_id = None

    for item in items:
        external_id = clean_text(item.get("external_id") or item.get("id"), 120) or ""
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

        order.source_form_id = clean_text(item.get("source_form_id"), 120)
        order.source_form_name = clean_text(item.get("source_form_name"), 255)
        order.external_number = clean_text(item.get("external_number") or item.get("number"), 120)
        order.external_created_at = parse_datetime(item.get("external_created_at") or item.get("created_at"))
        order.created_at_source = order.external_created_at
        if not order.received_at:
            order.received_at = datetime.now(timezone.utc)
        order.customer_name = clean_text(item.get("customer_name"), 255)
        order.customer_phone = clean_text(item.get("customer_phone"), 80)
        order.customer_email = clean_text(item.get("customer_email"), 255)
        order.title = clean_text(item.get("title"), 500)
        order.message = clean_text(item.get("message"))
        order.amount = parse_decimal(item.get("amount"))
        order.currency = clean_text(item.get("currency"), 10)
        order.external_status = clean_text(item.get("external_status") or item.get("status"), 120)
        order.raw_payload = item

        if source_type == "rsform" and order.source_form_id:
            upsert_rsform_form(db, site, order.source_form_id, order.source_form_name)

        if source_type == "virtuemart":
            order.items.clear()
            for raw_item in item.get("items") or []:
                name = clean_text(raw_item.get("name") or raw_item.get("product_name"), 500) or "Товар"
                order.items.append(
                    OrderItem(
                        sku=clean_text(raw_item.get("sku"), 120),
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


def response_next_since_id(response: dict, result: dict) -> str | None:
    next_since_id = response.get("next_since_id")
    if next_since_id not in (None, ""):
        return str(next_since_id)
    if result["max_external_id"]:
        return str(result["max_external_id"])
    return None


async def run_site_sync(
    db: Session,
    site: Site,
    secret: str,
    source_type: str | None = None,
    *,
    full_backfill: bool = False,
) -> dict:
    source_types = [
        source.source_type
        for source in site.sources
        if source.is_enabled and (source_type is None or source.source_type == source_type)
    ]
    limit = min(max(settings.connector_sync_limit, 1), 1000)
    max_batches = settings.connector_sync_backfill_max_batches if full_backfill else settings.connector_sync_max_batches
    totals = {"created": 0, "updated": 0, "sources": {}, "limit": limit, "max_batches": max_batches}

    for current_type in source_types:
        cursor = get_cursor(db, site.id, current_type)
        source_total = {"created": 0, "updated": 0, "received": 0, "batches": 0, "has_more": False}
        try:
            for batch_number in range(1, max_batches + 1):
                response = await sync_site_source(
                    site.normalized_url,
                    secret,
                    site.site_uid,
                    current_type,
                    cursor.last_external_id or "0",
                    limit,
                )
                if not isinstance(response, dict):
                    break

                items = response.get("items", [])
                if not isinstance(items, list):
                    items = []

                result = save_connector_items(db, site, current_type, items)
                next_since_id = response_next_since_id(response, result)
                if next_since_id:
                    cursor.last_external_id = next_since_id

                db.add(
                    SyncLog(
                        site_id=site.id,
                        source_type=current_type,
                        action="full_backfill" if full_backfill else "sync",
                        status="ok",
                        message=(
                            f"Batch {batch_number}: received {len(items)}, "
                            f"created {result['created']}, updated {result['updated']}"
                        ),
                        payload={
                            "batch": batch_number,
                            "items": len(items),
                            "limit": response.get("limit", limit),
                            "has_more": bool(response.get("has_more")),
                            "next_since_id": next_since_id,
                        },
                    )
                )
                db.commit()

                source_total["created"] += result["created"]
                source_total["updated"] += result["updated"]
                source_total["received"] += len(items)
                source_total["batches"] = batch_number
                source_total["has_more"] = bool(response.get("has_more"))

                if not response.get("has_more") or not items or not next_since_id:
                    break

            totals["created"] += source_total["created"]
            totals["updated"] += source_total["updated"]
            totals["sources"][current_type] = source_total
        except Exception as exc:
            db.rollback()
            db.add(
                SyncLog(
                    site_id=site.id,
                    source_type=current_type,
                    action="sync",
                    status="error",
                    message=str(exc),
                )
            )
            db.commit()
            totals["sources"][current_type] = {"error": str(exc)}

    site.last_sync_at = datetime.now(timezone.utc)
    db.commit()
    return totals

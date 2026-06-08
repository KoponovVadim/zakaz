import secrets
from datetime import datetime, timezone
from urllib.parse import urlparse, urlunparse

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.crypto import decrypt_secret, encrypt_secret, generate_secret, hash_secret
from app.db.session import get_db
from app.models import Client, Order, OrderComment, OrderItem, OrderStatusHistory, Site, SiteSource, SyncCursor, SyncLog
from app.schemas.site import ConnectorCheckResponse, SiteCreate, SiteRead, SiteUpdate
from app.services.connector_client import call_connector
from app.services.connector_generator import render_connector
from app.services.connector_sync import run_site_sync

router = APIRouter(dependencies=[Depends(get_current_user)])


def normalize_url(url: str) -> str:
    parsed = urlparse(str(url))
    scheme = parsed.scheme or "https"
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip("/")
    return urlunparse((scheme, netloc, path, "", "", ""))


def get_site_or_404(db: Session, site_id: int) -> Site:
    site = db.scalar(select(Site).options(selectinload(Site.sources)).where(Site.id == site_id))
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return site


@router.get("", response_model=list[SiteRead])
def list_sites(client_id: int | None = None, db: Session = Depends(get_db)):
    query = select(Site).options(selectinload(Site.sources))
    if client_id:
        query = query.where(Site.client_id == client_id)
    return db.scalars(query.order_by(Site.created_at.desc())).all()


@router.post("", response_model=SiteRead, status_code=status.HTTP_201_CREATED)
def create_site(payload: SiteCreate, db: Session = Depends(get_db)):
    if not db.get(Client, payload.client_id):
        raise HTTPException(status_code=404, detail="Client not found")
    secret = generate_secret()
    site = Site(
        client_id=payload.client_id,
        name=payload.name,
        url=str(payload.url),
        normalized_url=normalize_url(str(payload.url)),
        joomla_version=payload.joomla_version,
        site_uid=secrets.token_hex(16),
        connector_secret_encrypted=encrypt_secret(secret),
        connector_secret_hash=hash_secret(secret),
        connector_version=settings.connector_version,
        status="pending_install",
    )
    if payload.rsform_enabled:
        site.sources.append(SiteSource(source_type="rsform", is_enabled=True))
    if payload.virtuemart_enabled:
        site.sources.append(SiteSource(source_type="virtuemart", is_enabled=True))
    db.add(site)
    db.commit()
    return get_site_or_404(db, site.id)


@router.get("/{site_id}", response_model=SiteRead)
def get_site(site_id: int, db: Session = Depends(get_db)):
    return get_site_or_404(db, site_id)


@router.put("/{site_id}", response_model=SiteRead)
def update_site(site_id: int, payload: SiteUpdate, db: Session = Depends(get_db)):
    site = get_site_or_404(db, site_id)
    data = payload.model_dump(exclude_unset=True)
    if "client_id" in data and not db.get(Client, data["client_id"]):
        raise HTTPException(status_code=404, detail="Client not found")
    if "url" in data and data["url"] is not None:
        site.url = str(data.pop("url"))
        site.normalized_url = normalize_url(site.url)
    for key, value in data.items():
        setattr(site, key, value)
    db.commit()
    return get_site_or_404(db, site_id)


@router.delete("/{site_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_site(site_id: int, db: Session = Depends(get_db)):
    site = get_site_or_404(db, site_id)
    order_ids = select(Order.id).where(Order.site_id == site_id)
    db.execute(delete(OrderItem).where(OrderItem.order_id.in_(order_ids)))
    db.execute(delete(OrderComment).where(OrderComment.order_id.in_(order_ids)))
    db.execute(delete(OrderStatusHistory).where(OrderStatusHistory.order_id.in_(order_ids)))
    db.execute(delete(Order).where(Order.site_id == site_id))
    db.execute(delete(SyncCursor).where(SyncCursor.site_id == site_id))
    db.execute(delete(SyncLog).where(SyncLog.site_id == site_id))
    db.execute(delete(SiteSource).where(SiteSource.site_id == site_id))
    db.delete(site)
    db.commit()
    return None


@router.get("/{site_id}/connector/download")
def download_connector(
    site_id: int,
    filename: str = Query(default="leadhub-connector.php", pattern="^(leadhub-connector\\.php|lh\\.php)$"),
    db: Session = Depends(get_db),
):
    site = get_site_or_404(db, site_id)
    content = render_connector(site.joomla_version, site.site_uid, decrypt_secret(site.connector_secret_encrypted))
    return Response(
        content=content,
        media_type="application/x-httpd-php",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/{site_id}/ping", response_model=ConnectorCheckResponse)
async def ping_site(site_id: int, db: Session = Depends(get_db)):
    site = get_site_or_404(db, site_id)
    try:
        data = await call_connector(site.normalized_url, decrypt_secret(site.connector_secret_encrypted), site.site_uid, "ping")
        site.status = "connected"
        site.last_ping_at = datetime.now(timezone.utc)
        site.last_error = None
        db.commit()
        return ConnectorCheckResponse(status="ok", message="Connector responded", data=data)
    except Exception as exc:
        site.status = "error"
        site.last_error = str(exc)
        db.commit()
        return ConnectorCheckResponse(status="error", message=str(exc))


@router.post("/{site_id}/discover", response_model=ConnectorCheckResponse)
async def discover_site(site_id: int, db: Session = Depends(get_db)):
    site = get_site_or_404(db, site_id)
    try:
        data = await call_connector(site.normalized_url, decrypt_secret(site.connector_secret_encrypted), site.site_uid, "discover")
        found = data.get("sources", {}) if isinstance(data, dict) else {}
        for source in site.sources:
            source.discovered = bool(found.get(source.source_type))
        site.status = "connected"
        site.last_discover_at = datetime.now(timezone.utc)
        site.last_error = None
        db.commit()
        return ConnectorCheckResponse(status="ok", message="Discover completed", data=data)
    except Exception as exc:
        site.status = "error"
        site.last_error = str(exc)
        db.commit()
        return ConnectorCheckResponse(status="error", message=str(exc))


@router.post("/{site_id}/sync", response_model=ConnectorCheckResponse)
async def sync_site(site_id: int, db: Session = Depends(get_db)):
    site = get_site_or_404(db, site_id)
    result = await run_site_sync(db, site, decrypt_secret(site.connector_secret_encrypted))
    return ConnectorCheckResponse(status="ok", message="Sync completed", data=result)


@router.post("/{site_id}/sync-rsform", response_model=ConnectorCheckResponse)
async def sync_rsform(site_id: int, db: Session = Depends(get_db)):
    site = get_site_or_404(db, site_id)
    result = await run_site_sync(db, site, decrypt_secret(site.connector_secret_encrypted), "rsform")
    return ConnectorCheckResponse(status="ok", message="RSForm sync completed", data=result)


@router.post("/{site_id}/sync-virtuemart", response_model=ConnectorCheckResponse)
async def sync_virtuemart(site_id: int, db: Session = Depends(get_db)):
    site = get_site_or_404(db, site_id)
    result = await run_site_sync(db, site, decrypt_secret(site.connector_secret_encrypted), "virtuemart")
    return ConnectorCheckResponse(status="ok", message="VirtueMart sync completed", data=result)


@router.post("/{site_id}/activate", response_model=SiteRead)
def activate_site(site_id: int, db: Session = Depends(get_db)):
    site = get_site_or_404(db, site_id)
    site.status = "active"
    db.commit()
    return get_site_or_404(db, site_id)


@router.post("/{site_id}/disable", response_model=SiteRead)
def disable_site(site_id: int, db: Session = Depends(get_db)):
    site = get_site_or_404(db, site_id)
    site.status = "disabled"
    db.commit()
    return get_site_or_404(db, site_id)

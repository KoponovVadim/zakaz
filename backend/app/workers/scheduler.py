import asyncio
import time

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.crypto import decrypt_secret
from app.db.session import SessionLocal
from app.models import Site
from app.services.connector_sync import run_site_sync


async def sync_active_sites() -> None:
    with SessionLocal() as db:
        sites = db.scalars(
            select(Site).options(selectinload(Site.sources)).where(Site.status == "active")
        ).all()
        for site in sites:
            try:
                await run_site_sync(db, site, decrypt_secret(site.connector_secret_encrypted))
            except Exception as exc:
                site.status = "error"
                site.last_error = str(exc)
                db.commit()


def main() -> None:
    print("Worker started. Active sites sync interval: 300 seconds.")
    while True:
        asyncio.run(sync_active_sites())
        time.sleep(300)


if __name__ == "__main__":
    main()

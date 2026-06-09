from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Client, RsformForm, Site
from app.schemas.rsform import RsformFormRead

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/forms", response_model=list[RsformFormRead])
def list_rsform_forms(
    client_id: int | None = None,
    site_id: int | None = None,
    db: Session = Depends(get_db),
):
    query = (
        select(RsformForm, Site, Client)
        .join(Site, Site.id == RsformForm.site_id)
        .join(Client, Client.id == Site.client_id)
    )
    if client_id:
        query = query.where(Site.client_id == client_id)
    if site_id:
        query = query.where(RsformForm.site_id == site_id)

    rows = db.execute(query.order_by(Site.name, RsformForm.name, RsformForm.external_form_id)).all()
    result = []
    for form, site, client in rows:
        result.append(
            RsformFormRead(
                id=form.id,
                site_id=form.site_id,
                site_name=site.name,
                client_id=client.id,
                client_name=client.name,
                external_form_id=form.external_form_id,
                name=form.name,
                submissions_count=form.submissions_count,
                last_seen_at=form.last_seen_at,
            )
        )
    return result

from datetime import datetime

from pydantic import BaseModel


class RsformFormRead(BaseModel):
    id: int
    site_id: int
    site_name: str | None = None
    client_id: int
    client_name: str | None = None
    external_form_id: str
    name: str | None = None
    submissions_count: int
    last_seen_at: datetime | None = None

    model_config = {"from_attributes": True}

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class SiteSourceRead(BaseModel):
    source_type: str
    is_enabled: bool
    discovered: bool
    last_external_id: str | None = None

    model_config = {"from_attributes": True}


class SiteBase(BaseModel):
    client_id: int
    name: str = Field(min_length=1, max_length=255)
    url: HttpUrl
    joomla_version: str = Field(pattern="^(3|4|5)$")


class SiteCreate(SiteBase):
    rsform_enabled: bool = True
    virtuemart_enabled: bool = True


class SiteUpdate(BaseModel):
    client_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    url: HttpUrl | None = None
    joomla_version: str | None = Field(default=None, pattern="^(3|4|5)$")
    status: str | None = None


class SiteRead(BaseModel):
    id: int
    client_id: int
    name: str
    url: str
    normalized_url: str
    joomla_version: str
    site_uid: str
    connector_version: str
    status: str
    last_ping_at: datetime | None = None
    last_discover_at: datetime | None = None
    last_sync_at: datetime | None = None
    last_error: str | None = None
    created_at: datetime
    updated_at: datetime
    sources: list[SiteSourceRead] = []

    model_config = {"from_attributes": True}


class ConnectorCheckResponse(BaseModel):
    status: str
    message: str
    data: dict | None = None

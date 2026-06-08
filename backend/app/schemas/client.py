from datetime import datetime

from pydantic import BaseModel, Field


class ClientBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    comment: str | None = None


class ClientCreate(ClientBase):
    pass


class ClientUpdate(ClientBase):
    pass


class ClientRead(ClientBase):
    id: int
    created_at: datetime
    updated_at: datetime
    sites_count: int = 0
    orders_count: int = 0

    model_config = {"from_attributes": True}

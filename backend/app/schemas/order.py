from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class OrderItemRead(BaseModel):
    id: int
    sku: str | None = None
    name: str
    quantity: Decimal
    price: Decimal | None = None

    model_config = {"from_attributes": True}


class OrderCommentRead(BaseModel):
    id: int
    user_id: int
    text: str
    created_at: datetime

    model_config = {"from_attributes": True}


class OrderStatusHistoryRead(BaseModel):
    id: int
    user_id: int
    old_status: str | None = None
    new_status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class OrderRead(BaseModel):
    id: int
    client_id: int
    client_name: str | None = None
    site_id: int
    site_name: str | None = None
    source_type: str
    external_id: str
    external_number: str | None = None
    source_form_id: str | None = None
    source_form_name: str | None = None
    external_created_at: datetime | None = None
    created_at_source: datetime | None = None
    received_at: datetime
    customer_name: str | None = None
    customer_phone: str | None = None
    customer_email: str | None = None
    title: str | None = None
    message: str | None = None
    amount: Decimal | None = None
    currency: str | None = None
    external_status: str | None = None
    internal_status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrderDetailRead(OrderRead):
    items: list[OrderItemRead] = []
    comments: list[OrderCommentRead] = []
    status_history: list[OrderStatusHistoryRead] = []
    raw_payload: dict | None = None


class OrderStatusUpdate(BaseModel):
    internal_status: str = Field(pattern="^(new|in_progress|done|cancelled)$")


class OrderCommentCreate(BaseModel):
    text: str = Field(min_length=1, max_length=2000)

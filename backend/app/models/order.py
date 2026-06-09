from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, utcnow


class Order(Base, TimestampMixin):
    __tablename__ = "orders"
    __table_args__ = (UniqueConstraint("site_id", "source_type", "external_id", name="uq_order_external"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), index=True, nullable=False)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id"), index=True, nullable=False)
    source_type: Mapped[str] = mapped_column(String(30), index=True, nullable=False)
    external_id: Mapped[str] = mapped_column(String(120), nullable=False)
    external_number: Mapped[str | None] = mapped_column(String(120))
    source_form_id: Mapped[str | None] = mapped_column(String(120), index=True)
    source_form_name: Mapped[str | None] = mapped_column(String(255))
    external_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at_source: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True, nullable=False)
    customer_name: Mapped[str | None] = mapped_column(String(255))
    customer_phone: Mapped[str | None] = mapped_column(String(80))
    customer_email: Mapped[str | None] = mapped_column(String(255))
    title: Mapped[str | None] = mapped_column(String(500))
    message: Mapped[str | None] = mapped_column(Text)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str | None] = mapped_column(String(10))
    external_status: Mapped[str | None] = mapped_column(String(120))
    internal_status: Mapped[str] = mapped_column(String(60), default="new", index=True, nullable=False)
    raw_payload: Mapped[dict | None] = mapped_column(JSON)

    site: Mapped["Site"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    comments: Mapped[list["OrderComment"]] = relationship(back_populates="order", cascade="all, delete-orphan")

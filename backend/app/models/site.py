from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Site(Base, TimestampMixin):
    __tablename__ = "sites"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    normalized_url: Mapped[str] = mapped_column(String(500), index=True, nullable=False)
    joomla_version: Mapped[str] = mapped_column(String(10), nullable=False)
    site_uid: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    connector_secret_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    connector_secret_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    connector_version: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="pending_install", nullable=False)
    last_ping_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_discover_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)

    client: Mapped["Client"] = relationship(back_populates="sites")
    sources: Mapped[list["SiteSource"]] = relationship(back_populates="site", cascade="all, delete-orphan")
    orders: Mapped[list["Order"]] = relationship(back_populates="site")

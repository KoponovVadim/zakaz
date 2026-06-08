from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class SyncCursor(Base, TimestampMixin):
    __tablename__ = "sync_cursors"
    __table_args__ = (UniqueConstraint("site_id", "source_type", name="uq_sync_cursor_site_source"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"), index=True, nullable=False)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False)
    last_external_id: Mapped[str | None] = mapped_column(String(120))

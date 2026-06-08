from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class SiteSource(Base, TimestampMixin):
    __tablename__ = "site_sources"
    __table_args__ = (UniqueConstraint("site_id", "source_type", name="uq_site_source_type"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"), index=True, nullable=False)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    discovered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_external_id: Mapped[str | None] = mapped_column(String(120))

    site: Mapped["Site"] = relationship(back_populates="sources")

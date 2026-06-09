from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class RsformForm(Base, TimestampMixin):
    __tablename__ = "rsform_forms"
    __table_args__ = (UniqueConstraint("site_id", "external_form_id", name="uq_rsform_form_site_external"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"), index=True, nullable=False)
    external_form_id: Mapped[str] = mapped_column(String(120), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255))
    submissions_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    site: Mapped["Site"] = relationship(back_populates="rsform_forms")

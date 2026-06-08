from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Client(Base, TimestampMixin):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)

    sites: Mapped[list["Site"]] = relationship(back_populates="client", cascade="all, delete-orphan")

from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, JSON, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class DirectDailyStat(Base, TimestampMixin):
    __tablename__ = "direct_daily_stats"
    __table_args__ = (UniqueConstraint("site_id", "date", "campaign_name", name="uq_direct_daily_site_date_campaign"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), index=True, nullable=False)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id"), index=True, nullable=False)
    date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    campaign_name: Mapped[str] = mapped_column(String(255), nullable=False)
    impressions: Mapped[int] = mapped_column(default=0, nullable=False)
    clicks: Mapped[int] = mapped_column(default=0, nullable=False)
    cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)


class DirectImportLog(Base, TimestampMixin):
    __tablename__ = "direct_import_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    rows_total: Mapped[int] = mapped_column(default=0, nullable=False)
    rows_success: Mapped[int] = mapped_column(default=0, nullable=False)
    rows_error: Mapped[int] = mapped_column(default=0, nullable=False)
    errors: Mapped[list | None] = mapped_column(JSON)


class DirectAccount(Base, TimestampMixin):
    __tablename__ = "direct_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    login: Mapped[str | None] = mapped_column(String(255))
    token_encrypted: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String(30), default="disabled", nullable=False)


class DirectCampaign(Base, TimestampMixin):
    __tablename__ = "direct_campaigns"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), index=True, nullable=False)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id"), index=True, nullable=False)
    direct_account_id: Mapped[int | None] = mapped_column(ForeignKey("direct_accounts.id"))
    campaign_id: Mapped[str | None] = mapped_column(String(120))
    campaign_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)


class AnalyticsDaily(Base, TimestampMixin):
    __tablename__ = "analytics_daily"
    __table_args__ = (UniqueConstraint("site_id", "date", name="uq_analytics_daily_site_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), index=True, nullable=False)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id"), index=True, nullable=False)
    date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    impressions: Mapped[int] = mapped_column(default=0, nullable=False)
    clicks: Mapped[int] = mapped_column(default=0, nullable=False)
    rsform_leads_count: Mapped[int] = mapped_column(default=0, nullable=False)
    virtuemart_orders_count: Mapped[int] = mapped_column(default=0, nullable=False)
    total_requests_count: Mapped[int] = mapped_column(default=0, nullable=False)
    revenue: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    cpl: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    cpo: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))

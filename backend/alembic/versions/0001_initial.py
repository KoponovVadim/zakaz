"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-08
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(30), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *timestamps(),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "clients",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("comment", sa.Text()),
        *timestamps(),
    )
    op.create_index("ix_clients_name", "clients", ["name"])

    op.create_table(
        "sites",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("normalized_url", sa.String(500), nullable=False),
        sa.Column("joomla_version", sa.String(10), nullable=False),
        sa.Column("site_uid", sa.String(64), nullable=False),
        sa.Column("connector_secret_encrypted", sa.Text(), nullable=False),
        sa.Column("connector_secret_hash", sa.String(64), nullable=False),
        sa.Column("connector_version", sa.String(30), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("last_ping_at", sa.DateTime(timezone=True)),
        sa.Column("last_discover_at", sa.DateTime(timezone=True)),
        sa.Column("last_sync_at", sa.DateTime(timezone=True)),
        sa.Column("last_error", sa.Text()),
        *timestamps(),
    )
    op.create_index("ix_sites_client_id", "sites", ["client_id"])
    op.create_index("ix_sites_normalized_url", "sites", ["normalized_url"])
    op.create_index("ix_sites_site_uid", "sites", ["site_uid"], unique=True)

    op.create_table(
        "site_sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("site_id", sa.Integer(), sa.ForeignKey("sites.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_type", sa.String(30), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False),
        sa.Column("discovered", sa.Boolean(), nullable=False),
        sa.Column("last_external_id", sa.String(120)),
        *timestamps(),
        sa.UniqueConstraint("site_id", "source_type", name="uq_site_source_type"),
    )
    op.create_index("ix_site_sources_site_id", "site_sources", ["site_id"])

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("site_id", sa.Integer(), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("source_type", sa.String(30), nullable=False),
        sa.Column("external_id", sa.String(120), nullable=False),
        sa.Column("external_number", sa.String(120)),
        sa.Column("external_created_at", sa.DateTime(timezone=True)),
        sa.Column("customer_name", sa.String(255)),
        sa.Column("customer_phone", sa.String(80)),
        sa.Column("customer_email", sa.String(255)),
        sa.Column("title", sa.String(500)),
        sa.Column("message", sa.Text()),
        sa.Column("amount", sa.Numeric(12, 2)),
        sa.Column("currency", sa.String(10)),
        sa.Column("external_status", sa.String(120)),
        sa.Column("internal_status", sa.String(60), nullable=False),
        sa.Column("raw_payload", sa.JSON()),
        *timestamps(),
        sa.UniqueConstraint("site_id", "source_type", "external_id", name="uq_order_external"),
    )
    op.create_index("ix_orders_client_id", "orders", ["client_id"])
    op.create_index("ix_orders_site_id", "orders", ["site_id"])
    op.create_index("ix_orders_source_type", "orders", ["source_type"])
    op.create_index("ix_orders_internal_status", "orders", ["internal_status"])

    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sku", sa.String(120)),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("quantity", sa.Numeric(12, 3), nullable=False),
        sa.Column("price", sa.Numeric(12, 2)),
        *timestamps(),
    )
    op.create_index("ix_order_items_order_id", "order_items", ["order_id"])

    op.create_table(
        "order_comments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        *timestamps(),
    )
    op.create_index("ix_order_comments_order_id", "order_comments", ["order_id"])

    op.create_table(
        "order_status_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("old_status", sa.String(60)),
        sa.Column("new_status", sa.String(60), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_order_status_history_order_id", "order_status_history", ["order_id"])

    op.create_table(
        "sync_cursors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("site_id", sa.Integer(), sa.ForeignKey("sites.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_type", sa.String(30), nullable=False),
        sa.Column("last_external_id", sa.String(120)),
        *timestamps(),
        sa.UniqueConstraint("site_id", "source_type", name="uq_sync_cursor_site_source"),
    )
    op.create_index("ix_sync_cursors_site_id", "sync_cursors", ["site_id"])

    op.create_table(
        "sync_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("site_id", sa.Integer(), sa.ForeignKey("sites.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_type", sa.String(30)),
        sa.Column("action", sa.String(30), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("message", sa.Text()),
        sa.Column("payload", sa.JSON()),
        *timestamps(),
    )
    op.create_index("ix_sync_logs_site_id", "sync_logs", ["site_id"])

    op.create_table(
        "direct_daily_stats",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("site_id", sa.Integer(), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("campaign_name", sa.String(255), nullable=False),
        sa.Column("impressions", sa.Integer(), nullable=False),
        sa.Column("clicks", sa.Integer(), nullable=False),
        sa.Column("cost", sa.Numeric(12, 2), nullable=False),
        *timestamps(),
        sa.UniqueConstraint("site_id", "date", "campaign_name", name="uq_direct_daily_site_date_campaign"),
    )
    op.create_index("ix_direct_daily_stats_client_id", "direct_daily_stats", ["client_id"])
    op.create_index("ix_direct_daily_stats_site_id", "direct_daily_stats", ["site_id"])
    op.create_index("ix_direct_daily_stats_date", "direct_daily_stats", ["date"])

    op.create_table(
        "direct_import_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("rows_total", sa.Integer(), nullable=False),
        sa.Column("rows_success", sa.Integer(), nullable=False),
        sa.Column("rows_error", sa.Integer(), nullable=False),
        sa.Column("errors", sa.JSON()),
        *timestamps(),
    )

    op.create_table(
        "direct_accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("login", sa.String(255)),
        sa.Column("token_encrypted", sa.String()),
        sa.Column("status", sa.String(30), nullable=False),
        *timestamps(),
    )
    op.create_index("ix_direct_accounts_client_id", "direct_accounts", ["client_id"])

    op.create_table(
        "direct_campaigns",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("site_id", sa.Integer(), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("direct_account_id", sa.Integer(), sa.ForeignKey("direct_accounts.id")),
        sa.Column("campaign_id", sa.String(120)),
        sa.Column("campaign_name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        *timestamps(),
    )
    op.create_index("ix_direct_campaigns_client_id", "direct_campaigns", ["client_id"])
    op.create_index("ix_direct_campaigns_site_id", "direct_campaigns", ["site_id"])

    op.create_table(
        "analytics_daily",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("site_id", sa.Integer(), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("cost", sa.Numeric(12, 2), nullable=False),
        sa.Column("impressions", sa.Integer(), nullable=False),
        sa.Column("clicks", sa.Integer(), nullable=False),
        sa.Column("rsform_leads_count", sa.Integer(), nullable=False),
        sa.Column("virtuemart_orders_count", sa.Integer(), nullable=False),
        sa.Column("total_requests_count", sa.Integer(), nullable=False),
        sa.Column("revenue", sa.Numeric(12, 2), nullable=False),
        sa.Column("cpl", sa.Numeric(12, 2)),
        sa.Column("cpo", sa.Numeric(12, 2)),
        *timestamps(),
        sa.UniqueConstraint("site_id", "date", name="uq_analytics_daily_site_date"),
    )
    op.create_index("ix_analytics_daily_client_id", "analytics_daily", ["client_id"])
    op.create_index("ix_analytics_daily_site_id", "analytics_daily", ["site_id"])
    op.create_index("ix_analytics_daily_date", "analytics_daily", ["date"])


def downgrade() -> None:
    for table in [
        "analytics_daily",
        "direct_campaigns",
        "direct_accounts",
        "direct_import_logs",
        "direct_daily_stats",
        "sync_logs",
        "sync_cursors",
        "order_status_history",
        "order_comments",
        "order_items",
        "orders",
        "site_sources",
        "sites",
        "clients",
        "users",
    ]:
        op.drop_table(table)

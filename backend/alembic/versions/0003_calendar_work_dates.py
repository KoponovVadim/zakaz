"""calendar work dates

Revision ID: 0003_calendar_work_dates
Revises: 0002_rsform_forms_and_batch_sync
Create Date: 2026-06-09
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_calendar_work_dates"
down_revision = "0002_rsform_forms_and_batch_sync"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("created_at_source", sa.DateTime(timezone=True), nullable=True))
    op.add_column("orders", sa.Column("received_at", sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE orders SET created_at_source = external_created_at")
    op.execute("UPDATE orders SET received_at = created_at WHERE received_at IS NULL")
    op.alter_column("orders", "received_at", nullable=False)
    op.create_index("ix_orders_created_at_source", "orders", ["created_at_source"])
    op.create_index("ix_orders_received_at", "orders", ["received_at"])


def downgrade() -> None:
    op.drop_index("ix_orders_received_at", table_name="orders")
    op.drop_index("ix_orders_created_at_source", table_name="orders")
    op.drop_column("orders", "received_at")
    op.drop_column("orders", "created_at_source")

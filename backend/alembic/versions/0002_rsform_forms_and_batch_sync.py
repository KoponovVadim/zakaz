"""rsform forms and batch sync metadata

Revision ID: 0002_rsform_forms_and_batch_sync
Revises: 0001_initial
Create Date: 2026-06-09
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_rsform_forms_and_batch_sync"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade() -> None:
    op.add_column("orders", sa.Column("source_form_id", sa.String(length=120), nullable=True))
    op.add_column("orders", sa.Column("source_form_name", sa.String(length=255), nullable=True))
    op.create_index("ix_orders_source_form_id", "orders", ["source_form_id"])
    op.create_index("ix_orders_external_created_at", "orders", ["external_created_at"])

    op.create_table(
        "rsform_forms",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("site_id", sa.Integer(), sa.ForeignKey("sites.id", ondelete="CASCADE"), nullable=False),
        sa.Column("external_form_id", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=255)),
        sa.Column("submissions_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_seen_at", sa.DateTime(timezone=True)),
        *timestamps(),
        sa.UniqueConstraint("site_id", "external_form_id", name="uq_rsform_form_site_external"),
    )
    op.create_index("ix_rsform_forms_site_id", "rsform_forms", ["site_id"])


def downgrade() -> None:
    op.drop_index("ix_rsform_forms_site_id", table_name="rsform_forms")
    op.drop_table("rsform_forms")
    op.drop_index("ix_orders_external_created_at", table_name="orders")
    op.drop_index("ix_orders_source_form_id", table_name="orders")
    op.drop_column("orders", "source_form_name")
    op.drop_column("orders", "source_form_id")

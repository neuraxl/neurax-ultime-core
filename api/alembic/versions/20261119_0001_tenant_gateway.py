"""Create UNX2 tenant identity and audit foundation.

Revision ID: 20261119_0001
"""
from alembic import op
import sqlalchemy as sa

revision = "20261119_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "unx2_organizations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False, unique=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_unx2_organizations_slug", "unx2_organizations", ["slug"], unique=True)
    op.create_table(
        "unx2_api_credentials",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("unx2_organizations.id"), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("key_prefix", sa.String(length=32), nullable=False, unique=True),
        sa.Column("secret_hash", sa.String(length=64), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False, server_default="member"),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_unx2_api_credentials_organization_id", "unx2_api_credentials", ["organization_id"])
    op.create_index("ix_unx2_api_credentials_key_prefix", "unx2_api_credentials", ["key_prefix"], unique=True)
    op.create_table(
        "unx2_memberships",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("unx2_organizations.id"), nullable=False),
        sa.Column("principal_id", sa.String(length=36), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False, server_default="member"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_unx2_memberships_organization_id", "unx2_memberships", ["organization_id"])
    op.create_index("ix_unx2_memberships_principal_id", "unx2_memberships", ["principal_id"])
    op.create_table(
        "unx2_audit_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("unx2_organizations.id"), nullable=True),
        sa.Column("actor_id", sa.String(length=36), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("resource_type", sa.String(length=80), nullable=False),
        sa.Column("resource_id", sa.String(length=160), nullable=True),
        sa.Column("outcome", sa.String(length=20), nullable=False, server_default="success"),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_unx2_audit_events_organization_id", "unx2_audit_events", ["organization_id"])


def downgrade() -> None:
    op.drop_index("ix_unx2_audit_events_organization_id", table_name="unx2_audit_events")
    op.drop_table("unx2_audit_events")
    op.drop_index("ix_unx2_memberships_principal_id", table_name="unx2_memberships")
    op.drop_index("ix_unx2_memberships_organization_id", table_name="unx2_memberships")
    op.drop_table("unx2_memberships")
    op.drop_index("ix_unx2_api_credentials_key_prefix", table_name="unx2_api_credentials")
    op.drop_index("ix_unx2_api_credentials_organization_id", table_name="unx2_api_credentials")
    op.drop_table("unx2_api_credentials")
    op.drop_index("ix_unx2_organizations_slug", table_name="unx2_organizations")
    op.drop_table("unx2_organizations")

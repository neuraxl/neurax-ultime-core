"""Add organization ownership to registry resources.

Existing global connector records are assigned to a quarantined legacy organization.
No registry rows are deleted. New API access is tenant-scoped.
Revision ID: 20261119_0002
"""
from alembic import op
import sqlalchemy as sa

revision = "20261119_0002"
down_revision = "20261119_0001"
branch_labels = None
depends_on = None

LEGACY_ORG_ID = "00000000-0000-4000-8000-000000000001"


def _tables():
    return set(sa.inspect(op.get_bind()).get_table_names())


def _indexes(table):
    return {item["name"] for item in sa.inspect(op.get_bind()).get_indexes(table)}


def _ensure_tenant_column(table):
    columns = {item["name"] for item in sa.inspect(op.get_bind()).get_columns(table)}
    if "organization_id" not in columns:
        op.add_column(table, sa.Column("organization_id", sa.String(36), nullable=True))
    op.execute(sa.text(
        f'UPDATE "{table}" SET organization_id = :org WHERE organization_id IS NULL'
    ).bindparams(org=LEGACY_ORG_ID))
    op.alter_column(table, "organization_id", existing_type=sa.String(36), nullable=False)
    foreign_keys = sa.inspect(op.get_bind()).get_foreign_keys(table)
    has_org_fk = any(item.get("referred_table") == "unx2_organizations" and item.get("constrained_columns") == ["organization_id"] for item in foreign_keys)
    fk_name = f"fk_{table}_organization"
    if not has_org_fk:
        op.create_foreign_key(fk_name, table, "unx2_organizations", ["organization_id"], ["id"])
    index_name = f"ix_{table}_organization_id"
    if index_name not in _indexes(table):
        op.create_index(index_name, table, ["organization_id"])


def upgrade():
    bind = op.get_bind()
    tables = _tables()

    # Keep pre-migration global records in a dedicated organization. It has no
    # tenant credential and therefore is not visible to ordinary tenant keys.
    bind.execute(sa.text(
        "INSERT INTO unx2_organizations (id, name, slug, status, created_at) "
        "VALUES (:id, 'Legacy Registry (quarantined)', 'legacy-registry-quarantine', 'active', CURRENT_TIMESTAMP) "
        "ON CONFLICT (id) DO NOTHING"
    ), {"id": LEGACY_ORG_ID})

    if "unx2_os_projects" not in tables:
        op.create_table(
            "unx2_os_projects",
            sa.Column("id", sa.String(255), primary_key=True),
            sa.Column("repo_url", sa.String(500), nullable=False, unique=True),
            sa.Column("full_name", sa.String(200), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("license_spdx", sa.String(100), nullable=True),
            sa.Column("default_branch", sa.String(200), nullable=True),
            sa.Column("latest_release", sa.String(100), nullable=True),
            sa.Column("stars", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("forks", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("open_issues", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("pushed_at", sa.String(80), nullable=True),
            sa.Column("maturity_score", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("maturity_details", sa.JSON(), nullable=False),
            sa.Column("dependencies", sa.JSON(), nullable=False),
            sa.Column("features", sa.JSON(), nullable=False),
            sa.Column("topics", sa.JSON(), nullable=False),
            sa.Column("status", sa.String(30), nullable=False, server_default="discovered"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_unx2_os_projects_repo_url", "unx2_os_projects", ["repo_url"], unique=True)
        op.create_index("ix_unx2_os_projects_full_name", "unx2_os_projects", ["full_name"])

    if "unx2_os_connectors" not in tables:
        op.create_table(
            "unx2_os_connectors",
            sa.Column("id", sa.String(255), primary_key=True),
            sa.Column("organization_id", sa.String(36), sa.ForeignKey("unx2_organizations.id"), nullable=False),
            sa.Column("project_id", sa.String(255), sa.ForeignKey("unx2_os_projects.id"), nullable=False),
            sa.Column("name", sa.String(200), nullable=False),
            sa.Column("kind", sa.String(30), nullable=False, server_default="api"),
            sa.Column("version", sa.String(100), nullable=True),
            sa.Column("endpoint", sa.String(1000), nullable=True),
            sa.Column("capabilities", sa.JSON(), nullable=False),
            sa.Column("permissions", sa.JSON(), nullable=False),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_unx2_os_connectors_project_id", "unx2_os_connectors", ["project_id"])
        op.create_index("ix_unx2_os_connectors_organization_id", "unx2_os_connectors", ["organization_id"])

    if "unx2_os_agent_grants" not in tables:
        op.create_table(
            "unx2_os_agent_grants",
            sa.Column("id", sa.String(80), primary_key=True),
            sa.Column("organization_id", sa.String(36), sa.ForeignKey("unx2_organizations.id"), nullable=False),
            sa.Column("agent_id", sa.String(200), nullable=False),
            sa.Column("connector_id", sa.String(255), sa.ForeignKey("unx2_os_connectors.id"), nullable=False),
            sa.Column("tool_name", sa.String(200), nullable=False),
            sa.Column("allowed", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("max_cost_usd", sa.Float(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_unx2_os_agent_grants_agent_id", "unx2_os_agent_grants", ["agent_id"])
        op.create_index("ix_unx2_os_agent_grants_connector_id", "unx2_os_agent_grants", ["connector_id"])
        op.create_index("ix_unx2_os_agent_grants_organization_id", "unx2_os_agent_grants", ["organization_id"])

    if "unx2_os_integration_plans" not in tables:
        op.create_table(
            "unx2_os_integration_plans",
            sa.Column("id", sa.String(80), primary_key=True),
            sa.Column("organization_id", sa.String(36), sa.ForeignKey("unx2_organizations.id"), nullable=False),
            sa.Column("connector_id", sa.String(255), sa.ForeignKey("unx2_os_connectors.id"), nullable=False),
            sa.Column("compose_yaml", sa.Text(), nullable=False),
            sa.Column("snapshot", sa.JSON(), nullable=False),
            sa.Column("status", sa.String(30), nullable=False, server_default="planned"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_unx2_os_integration_plans_connector_id", "unx2_os_integration_plans", ["connector_id"])
        op.create_index("ix_unx2_os_integration_plans_organization_id", "unx2_os_integration_plans", ["organization_id"])

    if "unx2_os_usage_events" not in tables:
        op.create_table(
            "unx2_os_usage_events",
            sa.Column("id", sa.String(80), primary_key=True),
            sa.Column("organization_id", sa.String(36), sa.ForeignKey("unx2_organizations.id"), nullable=False),
            sa.Column("agent_id", sa.String(200), nullable=False),
            sa.Column("connector_id", sa.String(255), sa.ForeignKey("unx2_os_connectors.id"), nullable=False),
            sa.Column("tool_name", sa.String(200), nullable=False),
            sa.Column("cost_usd", sa.Float(), nullable=False, server_default="0"),
            sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_unx2_os_usage_events_agent_id", "unx2_os_usage_events", ["agent_id"])
        op.create_index("ix_unx2_os_usage_events_connector_id", "unx2_os_usage_events", ["connector_id"])
        op.create_index("ix_unx2_os_usage_events_organization_id", "unx2_os_usage_events", ["organization_id"])

    # Existing tables created by the previous API release are adopted in place.
    for table in ("unx2_os_connectors", "unx2_os_agent_grants", "unx2_os_integration_plans", "unx2_os_usage_events"):
        _ensure_tenant_column(table)


def downgrade():
    # Intentionally forward-only: removing tenant ownership columns would
    # destroy the isolation boundary and could expose or orphan customer data.
    pass

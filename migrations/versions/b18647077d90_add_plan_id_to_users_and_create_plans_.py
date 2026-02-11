"""Add plan_id to users and create plans table

Revision ID: b18647077d90
Revises: a37d81d50dd7
Create Date: 2025-10-20 13:12:03.712637

Author: Mohamad Hamza Mehmalat
Project: Ouhud QR
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
from sqlalchemy import inspect

# Revision identifiers
revision: str = "b18647077d90"
down_revision: Union[str, Sequence[str], None] = "a37d81d50dd7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ─────────────────────────────────────────────
# ✅ UPGRADE
# ─────────────────────────────────────────────
def upgrade() -> None:
    """Upgrade schema."""
    print("🚀 Upgrade: Erstelle Tabelle 'plans' und füge 'plan_id' zu 'users' hinzu...")

    # Tabelle 'plans' erstellen
    op.create_table(
        "plans",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("qr_limit", sa.Integer(), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("has_api_access", sa.Boolean(), nullable=True),
        sa.Column("free_months", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # Index hinzufügen
    op.create_index(op.f("ix_plans_id"), "plans", ["id"], unique=False)

    # Spalte plan_id zu users hinzufügen
    op.add_column("users", sa.Column("plan_id", sa.Integer(), nullable=True))

    # Foreign Key erstellen
    op.create_foreign_key(
        "fk_users_plan_id",  # 🔹 expliziter Name, damit MySQL ihn wiederfindet
        "users",
        "plans",
        ["plan_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Alte Spalte 'plan' entfernen (falls sie existiert)
    conn = op.get_bind()
    inspector = inspect(conn)
    user_columns = [col["name"] for col in inspector.get_columns("users")]
    if "plan" in user_columns:
        op.drop_column("users", "plan")
        print("🧹 Alte Spalte 'plan' wurde entfernt.")

    print("✅ Upgrade abgeschlossen!")


# ─────────────────────────────────────────────
# ⬅️ DOWNGRADE
# ─────────────────────────────────────────────
def downgrade() -> None:
    """Downgrade schema."""
    print("⬅️ Downgrade: Entferne 'plans' und Foreign Key aus 'users'...")

    # Alte Spalte wiederherstellen
    op.add_column(
        "users",
        sa.Column(
            "plan",
            mysql.VARCHAR(length=50, collation="utf8mb4_unicode_ci"),
            nullable=True,
        ),
    )

    # Sicherer Foreign Key-Drop (nur wenn existiert)
    conn = op.get_bind()
    inspector = inspect(conn)
    fk_names = [fk["name"] for fk in inspector.get_foreign_keys("users")]

    if "fk_users_plan_id" in fk_names:
        op.drop_constraint("fk_users_plan_id", "users", type_="foreignkey")
        print("🗑️ Foreign Key 'fk_users_plan_id' entfernt.")
    else:
        print("⚠️ Foreign Key 'fk_users_plan_id' nicht gefunden – übersprungen.")

    # Spalte 'plan_id' löschen, falls vorhanden
    user_columns = [col["name"] for col in inspector.get_columns("users")]
    if "plan_id" in user_columns:
        op.drop_column("users", "plan_id")

    # Tabelle 'plans' löschen, falls sie existiert
    table_names = inspector.get_table_names()
    if "plans" in table_names:
        op.drop_index(op.f("ix_plans_id"), table_name="plans")
        op.drop_table("plans")

    print("✅ Downgrade abgeschlossen.")
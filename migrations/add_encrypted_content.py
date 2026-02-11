"""
Database Migration: Add encrypted_content column to qr_codes table
Run this migration to add the encrypted_content column for QR content encryption.
"""

from pathlib import Path
import sys

# Ensure project root is on sys.path when running as a script
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import text
from database import engine

def _column_exists(conn) -> bool:
    dialect = engine.dialect.name
    if dialect == "sqlite":
        check_sql = """
        SELECT COUNT(*)
        FROM pragma_table_info('qr_codes')
        WHERE name = 'encrypted_content';
        """
        result = conn.execute(text(check_sql))
        return (result.scalar() or 0) > 0
    if dialect in {"mysql", "mariadb"}:
        check_sql = """
        SELECT COUNT(*)
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'qr_codes'
          AND COLUMN_NAME = 'encrypted_content';
        """
        result = conn.execute(text(check_sql))
        return (result.scalar() or 0) > 0
    if dialect == "postgresql":
        check_sql = """
        SELECT COUNT(*)
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'qr_codes'
          AND column_name = 'encrypted_content';
        """
        result = conn.execute(text(check_sql))
        return (result.scalar() or 0) > 0
    raise RuntimeError(f"Unsupported dialect: {dialect}")


def migrate():
    """Add encrypted_content column to qr_codes table."""
    with engine.connect() as conn:
        if _column_exists(conn):
            print("ℹ️  Column 'encrypted_content' already exists. Skipping migration.")
            return

        dialect = engine.dialect.name
        if dialect in {"mysql", "mariadb"}:
            alter_sql = """
            ALTER TABLE qr_codes
            ADD COLUMN encrypted_content TEXT COMMENT 'Verschlüsselter QR-Inhalt (AES-256-GCM)';
            """
        else:
            alter_sql = """
            ALTER TABLE qr_codes
            ADD COLUMN encrypted_content TEXT;
            """
        conn.execute(text(alter_sql))
        conn.commit()
        print("✅ Migration completed: Added 'encrypted_content' column to qr_codes table.")


if __name__ == "__main__":
    migrate()

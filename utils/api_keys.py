from __future__ import annotations

import hashlib
import secrets
from typing import Any

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def generate_api_key() -> str:
    return f"ouh_live_{secrets.token_urlsafe(32)}"


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def key_prefix(api_key: str) -> str:
    return api_key[:12]


def key_last4(api_key: str) -> str:
    return api_key[-4:]


def mask_presented_key(api_key: str | None) -> str | None:
    if not api_key:
        return None
    return f"{key_prefix(api_key)}...{key_last4(api_key)}"


def serialize_api_key_row(row: Any) -> dict[str, Any]:
    return {
        "id": row.id,
        "name": row.name,
        "prefix": row.key_prefix,
        "last4": row.last4,
        "created_at": row.created_at,
        "last_used_at": row.last_used_at,
    }


def ensure_api_key_columns(engine: Engine) -> None:
    """
    Legacy compatibility for old single-key fields on users table.
    """
    try:
        insp = inspect(engine)
        if "users" not in insp.get_table_names():
            return
        cols = {c["name"] for c in insp.get_columns("users")}

        statements: list[str] = []
        if "api_key" not in cols:
            statements.append("ALTER TABLE users ADD COLUMN api_key VARCHAR(128) NULL")
        if "api_key_created_at" not in cols:
            statements.append("ALTER TABLE users ADD COLUMN api_key_created_at DATETIME NULL")

        with engine.begin() as conn:
            for stmt in statements:
                conn.execute(text(stmt))
            if "api_key" not in cols:
                try:
                    conn.execute(text("CREATE UNIQUE INDEX ix_users_api_key ON users (api_key)"))
                except Exception:
                    pass

        if statements:
            print("✅ Legacy API-Key-Spalten geprüft/ergänzt.")
    except Exception as exc:
        print(f"⚠️ Konnte API-Key-Spalten nicht automatisch ergänzen: {exc}")


def ensure_api_keys_table(engine: Engine) -> None:
    """
    Creates api_keys table for OpenAI-style key management.
    """
    try:
        dialect = engine.dialect.name.lower()
        with engine.begin() as conn:
            if dialect == "sqlite":
                conn.execute(
                    text(
                        """
                        CREATE TABLE IF NOT EXISTS api_keys (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER NOT NULL,
                            name VARCHAR(120) NOT NULL DEFAULT 'Default',
                            active_name VARCHAR(120) NULL,
                            key_prefix VARCHAR(24) NOT NULL,
                            key_hash VARCHAR(128) NOT NULL UNIQUE,
                            last4 VARCHAR(4) NOT NULL,
                            created_at DATETIME NOT NULL,
                            last_used_at DATETIME NULL,
                            revoked_at DATETIME NULL
                        )
                        """
                    )
                )
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_api_keys_user_id ON api_keys (user_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_api_keys_active_name ON api_keys (active_name)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_api_keys_key_prefix ON api_keys (key_prefix)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_api_keys_key_hash ON api_keys (key_hash)"))
                conn.execute(
                    text(
                        "CREATE UNIQUE INDEX IF NOT EXISTS uq_api_keys_user_active_name ON api_keys (user_id, active_name)"
                    )
                )
            else:
                conn.execute(
                    text(
                        """
                        CREATE TABLE IF NOT EXISTS api_keys (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            user_id INT NOT NULL,
                            name VARCHAR(120) NOT NULL DEFAULT 'Default',
                            active_name VARCHAR(120) NULL,
                            key_prefix VARCHAR(24) NOT NULL,
                            key_hash VARCHAR(128) NOT NULL UNIQUE,
                            last4 VARCHAR(4) NOT NULL,
                            created_at DATETIME NOT NULL,
                            last_used_at DATETIME NULL,
                            revoked_at DATETIME NULL,
                            INDEX ix_api_keys_user_id (user_id),
                            INDEX ix_api_keys_active_name (active_name),
                            INDEX ix_api_keys_key_prefix (key_prefix),
                            INDEX ix_api_keys_key_hash (key_hash),
                            UNIQUE KEY uq_api_keys_user_active_name (user_id, active_name),
                            CONSTRAINT fk_api_keys_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                        )
                        """
                    )
                )
            # migration path for existing tables without active_name
            cols = {c["name"] for c in inspect(engine).get_columns("api_keys")}
            if "active_name" not in cols:
                conn.execute(text("ALTER TABLE api_keys ADD COLUMN active_name VARCHAR(120) NULL"))
            conn.execute(
                text(
                    "UPDATE api_keys SET active_name = LOWER(name) WHERE revoked_at IS NULL AND active_name IS NULL"
                )
            )
            # resolve collisions before unique index creation
            duplicates = conn.execute(
                text(
                    """
                    SELECT user_id, active_name, COUNT(*) as cnt
                    FROM api_keys
                    WHERE revoked_at IS NULL AND active_name IS NOT NULL
                    GROUP BY user_id, active_name
                    HAVING COUNT(*) > 1
                    """
                )
            ).fetchall()
            for d in duplicates:
                rows = conn.execute(
                    text(
                        """
                        SELECT id, name FROM api_keys
                        WHERE user_id = :user_id AND active_name = :active_name AND revoked_at IS NULL
                        ORDER BY id ASC
                        """
                    ),
                    {"user_id": d[0], "active_name": d[1]},
                ).fetchall()
                for r in rows[1:]:
                    new_name = f"{r[1]} {r[0]}"
                    conn.execute(
                        text("UPDATE api_keys SET name = :name, active_name = :active_name WHERE id = :id"),
                        {"id": r[0], "name": new_name[:120], "active_name": new_name[:120].lower()},
                    )
            # unique index for existing schema
            if dialect == "sqlite":
                conn.execute(
                    text(
                        "CREATE UNIQUE INDEX IF NOT EXISTS uq_api_keys_user_active_name ON api_keys (user_id, active_name)"
                    )
                )
            else:
                try:
                    conn.execute(
                        text(
                            "ALTER TABLE api_keys ADD UNIQUE KEY uq_api_keys_user_active_name (user_id, active_name)"
                        )
                    )
                except Exception:
                    pass
        print("✅ api_keys Tabelle erstellt/geprüft.")
    except Exception as exc:
        print(f"⚠️ Konnte api_keys Tabelle nicht automatisch erstellen: {exc}")

from __future__ import annotations

from razdevator.db.database import Database


DDL = """
CREATE TABLE IF NOT EXISTS staff_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER NOT NULL UNIQUE,
    username TEXT,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL,
    referral_tag TEXT NOT NULL UNIQUE,
    commission_rate INTEGER NOT NULL DEFAULT 30,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bot_instances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bot_id INTEGER UNIQUE,
    token TEXT NOT NULL UNIQUE,
    username TEXT,
    title TEXT NOT NULL,
    kind TEXT NOT NULL,
    audience TEXT NOT NULL,
    owner_staff_id INTEGER REFERENCES staff_users(id),
    is_active INTEGER NOT NULL DEFAULT 1,
    is_archived INTEGER NOT NULL DEFAULT 0,
    welcome_text TEXT,
    farewell_text TEXT,
    hero_media TEXT,
    payment_provider TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS end_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bot_instance_id INTEGER NOT NULL REFERENCES bot_instances(id),
    telegram_id INTEGER NOT NULL,
    username TEXT,
    full_name TEXT NOT NULL,
    language_code TEXT NOT NULL DEFAULT 'ru',
    balance INTEGER NOT NULL DEFAULT 0,
    successful_generations INTEGER NOT NULL DEFAULT 0,
    failed_generations INTEGER NOT NULL DEFAULT 0,
    referred_by_staff_id INTEGER REFERENCES staff_users(id),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(bot_instance_id, telegram_id)
);

CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bot_instance_id INTEGER REFERENCES bot_instances(id),
    end_user_id INTEGER REFERENCES end_users(id),
    amount_cents INTEGER NOT NULL,
    currency TEXT NOT NULL DEFAULT 'USD',
    provider TEXT NOT NULL,
    direction TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    external_id TEXT,
    meta_json TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS payouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    staff_user_id INTEGER NOT NULL REFERENCES staff_users(id),
    amount_cents INTEGER NOT NULL,
    currency TEXT NOT NULL DEFAULT 'USD',
    status TEXT NOT NULL DEFAULT 'pending',
    note TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS generation_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bot_instance_id INTEGER NOT NULL REFERENCES bot_instances(id),
    end_user_id INTEGER NOT NULL REFERENCES end_users(id),
    feature TEXT NOT NULL,
    template_slug TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued',
    source_file_id TEXT,
    result_file_id TEXT,
    prompt TEXT,
    error_text TEXT,
    cost_credits INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS broadcast_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scope TEXT NOT NULL,
    bot_instance_id INTEGER REFERENCES bot_instances(id),
    created_by_staff_id INTEGER NOT NULL REFERENCES staff_users(id),
    text TEXT NOT NULL,
    media_path TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_end_users_bot_instance_id
ON end_users (bot_instance_id);

CREATE INDEX IF NOT EXISTS idx_payments_bot_instance_id
ON payments (bot_instance_id);

CREATE INDEX IF NOT EXISTS idx_generation_jobs_bot_instance_id
ON generation_jobs (bot_instance_id);
"""


async def init_schema(db: Database) -> None:
    for statement in DDL.strip().split(";\n\n"):
        cleaned = statement.strip()
        if cleaned:
            await db.execute(cleaned)
    await ensure_column(db, "payments", "meta_json", "TEXT")
    await db.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_payments_external_id
        ON payments (external_id)
        """
    )


async def ensure_column(db: Database, table: str, column: str, ddl: str) -> None:
    rows = await db.fetchall(f"PRAGMA table_info({table})")
    known_columns = {row["name"] for row in rows}
    if column in known_columns:
        return
    await db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")

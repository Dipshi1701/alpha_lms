"""
Alembic environment — wired to the LMS app's SQLAlchemy models and .env config.

How to use
----------
Run from the backend/ directory (where alembic.ini lives):

  # Apply all pending migrations
  alembic upgrade head

  # Roll back the last migration
  alembic downgrade -1

  # Auto-generate a new migration after you change models.py
  alembic revision --autogenerate -m "describe your change here"

  # See current migration state
  alembic current

  # See migration history
  alembic history
"""

import os
import sys
from logging.config import fileConfig

from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

from alembic import context

# ── Make sure app/ is on the path so we can import from it ───────────────────
# alembic.ini sets prepend_sys_path = . which adds backend/ to sys.path.
# We also add it explicitly here as a safety net.
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# ── Load .env so DATABASE_URL and other vars are available ───────────────────
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

# ── Import the app's Base so autogenerate can see all table definitions ───────
from app.database import Base  # noqa: E402
import app.models  # noqa: E402,F401  — registers all models on Base.metadata

# ── Alembic Config object ─────────────────────────────────────────────────────
config = context.config

# Override sqlalchemy.url from environment (do not store credentials in alembic.ini)
database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise RuntimeError("DATABASE_URL is not set. Check your .env file.")
config.set_main_option("sqlalchemy.url", database_url)

# Set up Python logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The metadata Alembic uses for autogenerate (--autogenerate compares this to the DB)
target_metadata = Base.metadata


# ═════════════════════════════════════════════════════════════════════════════
#  Offline mode  —  generates SQL without connecting to the database
# ═════════════════════════════════════════════════════════════════════════════

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Compare column types so autogenerate catches type changes too
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ═════════════════════════════════════════════════════════════════════════════
#  Online mode  —  connects to the database and runs migrations directly
# ═════════════════════════════════════════════════════════════════════════════

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Compare column types so autogenerate catches type changes
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

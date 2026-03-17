from logging.config import fileConfig
import os
import sys

from alembic import context

# Add parent directory to path so `app` package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Tell create_app() to skip demo seeding (tables may not exist yet)
os.environ["_ALEMBIC_RUNNING"] = "1"

from app import create_app
from app.db import db

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

app = create_app()
target_metadata = db.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL without connecting)."""
    url = app.config.get("SQLALCHEMY_DATABASE_URI") or config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using Flask-SQLAlchemy's engine."""
    with app.app_context():
        connectable = db.engine

        with connectable.connect() as connection:
            context.configure(
                connection=connection, target_metadata=target_metadata
            )
            with context.begin_transaction():
                context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

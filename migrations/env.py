"""Alembic migration environment - supports SQLModel and environment variables"""
from logging.config import fileConfig
import os
from sqlalchemy import engine_from_config, pool
from alembic import context

# Import database config from app.config
from app.config import settings

# Import all SQLModel models for migration generation
from app.models import (
    User, RefreshToken, Case, Snapshot, Member, Event, 
    Scenario, Delegation, AuditLog, ChartReview
)
from sqlmodel import SQLModel

# Alembic Config object
config = context.config

# Set up logger
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target_metadata (for autogenerate support)
# Use SQLModel metadata
target_metadata = SQLModel.metadata

# Get database URL from environment variable or app.config
def get_sqlalchemy_url() -> str:
    """Get database URL from environment variable or config"""
    # First try to get from environment variable
    url = os.environ.get("DATABASE_URL")
    if url:
        return url

    # Otherwise use config (fallback to SQLite)
    db_url = settings.database_url
    if db_url is None:
        db_url = f"sqlite:///{settings.db_path}"
    return db_url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode
    
    This only configures URL without actual database connection.
    Good for generating SQL scripts.
    """
    url = get_sqlalchemy_url()
    
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode
    
    Creates actual database engine and executes migrations.
    """
    url = get_sqlalchemy_url()
    
    # Configure SQLAlchemy engine
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = url
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

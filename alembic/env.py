import os
import sys
from logging.config import fileConfig
from dotenv import load_dotenv

from sqlalchemy import engine_from_config, pool
from alembic import context

# Add project root to sys.path to import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load ACTIVE_ENV and correct .env file early
ACTIVE_ENV = os.getenv("ACTIVE_ENV", "local")
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), f"../.env.{ACTIVE_ENV}"))
if not os.path.exists(dotenv_path):
    raise FileNotFoundError(f".env file not found at {dotenv_path}")
load_dotenv(dotenv_path)

print(f"ACTIVE_ENV={ACTIVE_ENV}")
print(f"Loading environment variables from: {dotenv_path}")

# Import Settings after loading .env
from app.config import Settings
from app.models import Base

config = context.config

# Setup logging once
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override sqlalchemy.url in alembic.ini with the one from Settings
print(Settings.DATABASE_URL)
config.set_main_option("sqlalchemy.url", Settings.DATABASE_URL)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

# alembic/env.py
import asyncio
import os
import sys
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# 1. СНАЧАЛА НАСТРАИВАЕМ ПУТИ И ИМПОРТЫ
# Добавляем корень проекта в пути, чтобы Python видел папку application
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

# Импортируем наш Base (теперь он точно объявится ДО того, как мы его используем)
from application.db.models import Base

# 2. НАСТРОЙКА ЛОГОВ И КОНФИГУРАЦИИ ALEMBIC
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Передаем метадату Алембику
target_metadata = Base.metadata


# 3. ФУНКЦИИ ЗАПУСКА МИГРАЦИЙ
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = os.getenv("DATABASE_URL")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Динамически подставляем URL из нашего .env
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = os.getenv("DATABASE_URL")

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
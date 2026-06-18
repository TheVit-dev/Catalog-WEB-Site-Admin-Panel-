# application/db/database.py
import os
from typing import AsyncGenerator
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# На всякий случай грузим .env (для тестов или отдельного запуска)
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL не найден в переменных окружения .env")

# 1. Создаем асинхронный движок (Engine)
# echo=True заставит SQLAlchemy писать в консоль все SQL-запросы (мега-круто для отладки)
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Поставь True, если захочешь видеть «сырой» SQL в консоли
    pool_pre_ping=True,  # Автоматически проверяет живое ли соединение, перед тем как дать его коду
)

# 2. Создаем фабрику сессий (Sessionmaker)
# expire_on_commit=False критически важен для асинхронности, чтобы объекты не «протухали» после сохранения
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# 3. Генератор сессий для FastAPI (Dependency Injection)
# Эта функция будет выдавать сессию на каждый веб-запрос и сама закрывать её в конце
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
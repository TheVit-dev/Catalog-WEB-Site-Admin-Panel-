# application/db/init_db.py
import asyncio
import sys
import os

# Прописываем пути, чтобы Docker не ругался на импорты
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from application.db.database import engine

# Импортируем твой найденный Base (подставь точное имя файла вместо base)
from application.db.models import Base

# Импортируем модель категории (и остальные модели, если есть), 
# чтобы Base "увидел" их до создания таблиц
from application.db.models import Category, Product, ProductImage

async def init_models():
    print("🔄 Проверка и создание таблиц в базе данных...")
    try:
        async with engine.begin() as conn:
            # Запускаем создание всех зарегистрированных таблиц
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Инициализация базы данных успешно завершена!")
    except Exception as e:
        print(f"❌ Ошибка при инициализации базы данных: {e}")
        import sys
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(init_models())
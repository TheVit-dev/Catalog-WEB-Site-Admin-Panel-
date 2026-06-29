import json
import logging
import redis.asyncio as redis
from typing import Any, Optional
from dotenv import load_dotenv
import redis.asyncio as redis
from application.core.config import settings
import os
load_dotenv()


# Подключение к Redis (лучше вынести хост в .env)
redis_client = redis.Redis(
    host=settings.redis_config['host'],
    port=settings.redis_config['port'],
    db=settings.redis_config['db'],
    decode_responses=True
)

async def get_cached_catalog(key: str) -> Optional[dict]:
    """
    Достает строку из Redis и безопасно превращает её обратно в Python-словарь.
    """
    try:
        data = await redis_client.get(key)
        if not data:
            return None
            
        # Если Redis возвращает байты (зависит от настроек клиента), декодируем их
        if isinstance(data, bytes):
            data = data.decode("utf-8")
            
        # ОБЯЗАТЕЛЬНО десериализуем строку обратно в dict, чтобы Pydantic не ругался
        return json.loads(data)
    except Exception as e:
        logging.error(f"Redis get failed for key '{key}': {e}")
        return None  # При ошибке кэша просто возвращаем None, чтобы пойти в БД


async def set_cached_catalog(key: str, data: dict, expire: int = 3600):
    """
    Безопасно сериализует dict в JSON и сохраняет в Redis.
    """
    try:
        # ensure_ascii=False сохраняет кириллицу в читаемом виде, экономя место
        serialized_data = json.dumps(data, ensure_ascii=False)
        await redis_client.set(key, serialized_data, ex=expire)
    except Exception as e:
        logging.error(f"Redis set failed for key '{key}': {e}")
        # Если кэш упал — не страшно, приложение продолжит работать

async def delete_cached_catalog(key: str):
    """
    Удаляет определенный ключ из кэша Redis (инвалидация).
    """
    try:
        await redis_client.delete(key)
    except Exception as e:
        logging.error(f"Redis delete failed for key '{key}': {e}")
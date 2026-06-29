from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from application.db.models import Category, Product, ProductImage
from application.services.cache import get_cached_catalog, set_cached_catalog
from application.core.config import CACHE_KEY_CATALOG
import math
from typing import Optional, Dict, Any
from sqlalchemy import func


async def get_catalog_structure(session: AsyncSession):
    # 1. Проверяем кэш (поменяем ключ на более точный)
    cached = await get_cached_catalog(CACHE_KEY_CATALOG)
    if cached:
        return cached

    # 2. Грузим ТОЛЬКО категории разом (всего 1 легкий запрос к БД вместо трех)
    res_cat = await session.execute(select(Category).order_by(Category.id))
    categories = res_cat.scalars().all()

    # 3. Формируем финальную структуру (вытягиваем все поля из твоей модели)
    catalog_data = {
        "categories": [
            {
                "id": c.id,
                "name": c.name,
                "slug": c.slug,
                "image_url": c.image_url,
                "parent_id": c.parent_id,
                "is_main": c.is_main
            } 
            for c in categories
        ]
    }

    # 4. Кэшируем на 1 час и возвращаем чистые данные
    await set_cached_catalog(CACHE_KEY_CATALOG, catalog_data, expire=3600)
    return catalog_data






class ProductService:
    @staticmethod
    async def get_paginated_products(
        db: AsyncSession,
        category_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 12
    ) -> Dict[str, Any]:
        """
        Сервис для получения товаров с пагинацией.
        Строго подстроен под модели Product и ProductImage.
        """
        # ---------------------------------------------------------------------
        # 1. Считаем общее количество товаров (COUNT)
        # ---------------------------------------------------------------------
        count_query = select(func.count()).select_from(Product)
        
        if category_id is not None:
            count_query = count_query.where(Product.category_id == category_id)
            
        total_items_result = await db.execute(count_query)
        total_items = total_items_result.scalar() or 0

        # Высчитываем страницы
        total_pages = math.ceil(total_items / page_size) if total_items > 0 else 1

        # Защита от выхода за пределы
        if page > total_pages:
            page = total_pages
        if page < 1:
            page = 1

        # ---------------------------------------------------------------------
        # 2. Получаем сами товары (LIMIT / OFFSET)
        # ---------------------------------------------------------------------
        skip = (page - 1) * page_size
        
        items_query = select(Product)
        
        if category_id is not None:
            items_query = items_query.where(Product.category_id == category_id)
            
        # Сортируем по ID (или можно по created_at, чтобы новинки были первыми)
        items_query = items_query.order_by(Product.id.desc()).offset(skip).limit(page_size)
        
        # Выполняем запрос. Благодаря lazy="selectin" в модели, 
        # SQLAlchemy сама подтянет ProductImage без проблемы N+1
        items_result = await db.execute(items_query)
        db_products = items_result.scalars().all()

        # ---------------------------------------------------------------------
        # 3. Форматируем результат для Pydantic схемы и фронтенда
        # ---------------------------------------------------------------------
        formatted_products = []
        for p in db_products:
            formatted_products.append({
                "id": p.id,
                "title": p.title,
                "description": p.description,
                # Decimal переводим в строку, чтобы JSON не сломался и копейки не поплыли
                "price": str(p.price),
                "category_id": p.category_id,
                # Берем главную картинку напрямую из поля товара
                "main_image": p.image_url,
                "views_count": p.views_count,
                "is_available": p.is_available,
                "created_at": p.created_at,
                # Пробегаемся по связи images и достаем только URL для галереи
                "gallery": [img.image_url for img in p.images]
            })

        # ---------------------------------------------------------------------
        # 4. Возвращаем готовую структуру
        # ---------------------------------------------------------------------
        return {
            "meta": {
                "total_items": total_items,
                "total_pages": total_pages,
                "current_page": page,
                "page_size": page_size,
                "has_next": page < total_pages,
                "has_prev": page > 1
            },
            "products": formatted_products
        }
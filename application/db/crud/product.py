from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from application.db.models import Product


async def has_products_in_category(session: AsyncSession, category_id: int) -> bool:
    """Проверяет, есть ли в категории товары"""
    query = select(Product.id).where(Product.category_id == category_id).limit(1)
    result = await session.execute(query)
    return result.scalar_one_or_none() is not None


# application/db/crud/product.py
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from application.db.models import Product

async def get_product_by_id(session: AsyncSession, product_id: int) -> Optional[Product]:
    """Получить один товар по его уникальному ID"""
    query = select(Product).where(Product.id == product_id)
    result = await session.execute(query)
    return result.scalar_one_or_none()

async def get_products_by_category_id(
    session: AsyncSession, 
    category_id: int, 
    limit: int = 20, 
    offset: int = 0
) -> List[Product]:
    """
    Получить список доступных товаров в конкретной категории.
    Использует LIMIT и OFFSET для постраничной навигации (пагинации).
    """
    query = (
        select(Product)
        .where(Product.category_id == category_id, Product.is_available == True)
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(query)
    return list(result.scalars().all())

async def get_popular_products(session: AsyncSession, limit: int = 10) -> List[Product]:
    """Получить топ популярных товаров по просмотрам (для блока 'Популярное')"""
    query = (
        select(Product)
        .where(Product.is_available == True)
        .order_by(Product.views_count.desc())
        .limit(limit)
    )
    result = await session.execute(query)
    return list(result.scalars().all())

async def get_new_products(session: AsyncSession, limit: int = 10) -> List[Product]:
    """Получить самые свежие товары (для блока 'Новинки')"""
    query = (
        select(Product)
        .where(Product.is_available == True)
        .order_by(Product.created_at.desc())
        .limit(limit)
    )
    result = await session.execute(query)
    return list(result.scalars().all())

async def increment_product_views(session: AsyncSession, product_id: int) -> None:
    """
    Безопасное атомарное увеличение счетчика просмотров товара на +1.
    Запрос выполняется напрямую на уровне СУБД, защищая от Race Condition.
    """
    query = (
        update(Product)
        .where(Product.id == product_id)
        .values(views_count=Product.views_count + 1)
    )
    await session.execute(query)
    await session.commit()

async def has_products_in_category(session: AsyncSession, category_id: int) -> bool:
    """
    Проверяет, привязан ли к категории хотя бы один товар.
    Используется в сервисах для безопасного удаления категорий (Вариант А).
    """
    # select(Product.id) вместо select(Product) — так базе не нужно тащить всю строку,
    # ей достаточно проверить существование хотя бы одного ID. Это работает быстрее.
    query = select(Product.id).where(Product.category_id == category_id).limit(1)
    result = await session.execute(query)
    return result.scalar_one_or_none() is not None
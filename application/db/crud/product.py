from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from application.db.models import Product
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from application.db.models import Product


async def has_products_in_category(session: AsyncSession, category_id: int) -> bool:
    """Проверяет, есть ли в категории товары"""
    query = select(Product.id).where(Product.category_id == category_id).limit(1)
    result = await session.execute(query)
    return result.scalar_one_or_none() is not None


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


async def get_products_by_search(
    db: AsyncSession, 
    slug: Optional[str] = None, 
    name: Optional[str] = None
) -> List[Product]:
    """
    Ищет товары в базе данных по title.
    """
    query = select(Product)
    
    if slug:
        # Так как поля slug в модели нет, временно ищем по частичному совпадению в title
        # Если в будущем добавишь slug в модель Product, поменяй обратно на: Product.slug == slug
        query = query.where(Product.title.ilike(f"%{slug}%"))
    elif name:
        # ИСПРАВЛЕНО: Вместо Product.name пишем Product.title
        query = query.where(Product.title.ilike(f"%{name}%"))
    else:
        return []
        
    result = await db.execute(query)
    return list(result.scalars().all())





from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select 
from application.db.models import Category, Product
from sqlalchemy import delete


async def check_category_has_relations(db: AsyncSession, category_id: int) -> bool:
    """
    Проверяет, есть ли у категории связанные товары или дочерние подкатегории.
    Возвращает True, если связи найдены (удалять нельзя), и False, если всё чисто.
    """
    # 1. Ищем хотя бы один товар в этой категории
    product_query = select(Product.id).where(Product.category_id == category_id).limit(1)
    product_result = await db.execute(product_query)
    if product_result.scalar() is not None:
        return True  # Связь есть, удалять нельзя

    # 2. Ищем хотя бы одну подкатегорию, где текущая категория указана как родительская
    subcategory_query = select(Category.id).where(Category.parent_id == category_id).limit(1)
    subcategory_result = await db.execute(subcategory_query)
    if subcategory_result.scalar() is not None:
        return True  # Связь есть, удалять нельзя

    return False  # Связей нет, категория "чистая"


async def get_category_by_name(db: AsyncSession, name: str) -> Optional[Category]:
    """
    Ищет категорию по строгому имени и возвращает её объект целиком со всеми полями.
    Если категория не найдена, возвращает None.
    """
    query = select(Category).where(Category.name == name)
    result = await db.execute(query)
    return result.scalars().first() # Возвращает объект Category или None


async def find_category_by_name(db: AsyncSession, name: str) -> int | None:
    """
    Ищет категорию по имени и возвращает её ID.
    Если категория не найдена, возвращает None.
    """
    query = select(Category.id).where(Category.name == name)
    result = await db.execute(query)
    return result.scalar_one_or_none()  # Возвращает чистый ID (int) или None


async def get_all_rows_name_c(session: AsyncSession):
    stmt = select(Category.name)
    result = await session.execute(stmt)
    
    # 2. .scalars().all() превратит результат в обычный плоский список строк: ['Хуйня', 'Владов', 'Ллллллл']
    names = result.scalars().all()
    
    # 3. Джойним список через запятую с пробелом
    # Если в базе пусто, вернется просто пустая строка ""
    return ", ".join(names)


async def get_id_by_category_name(session: AsyncSession, name: str):
    stmt = select(Category.id).where(Category.name == name)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
    

async def search_categories_by_name(session: AsyncSession, query_str: str):
    """
    Ищет категории в БД, у которых имя содержит поисковый запрос (ILIKE).
    """
    stmt = select(Category).where(Category.name.ilike(f"%{query_str}%"))
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_category_by_id(session: AsyncSession, category_id: int) -> Optional[Category]:
    """ Get Category by her ID """
    query = select(Category).where(Category.id == category_id)
    result = await session.execute(query)
    return result.scalar_one_or_none()





async def delete_category(session: AsyncSession, category_id: int) -> bool:
    """Delete category by ID. Retirn True, if approwe"""
    category = await get_category_by_id(session, category_id)
    if category:
        await session.delete(category)
        await session.commit()
        return True
    return False
 

# 2. ФУНКЦИЯ УДАЛЕНИЯ БЕЗ CASCADE
async def delete_category_by_id(db: AsyncSession, category_id: int) -> bool:
    """
    Удаляет категорию по её ID.
    """
    stmt = delete(Category).where(Category.id == category_id)
    result = await db.execute(stmt)
    await db.commit()
    
    return result.rowcount > 0  # Возвращает True, если строка была удалена
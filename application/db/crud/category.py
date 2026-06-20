from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from application.db.models import Category




async def get_category_by_id(session: AsyncSession, category_id: int) -> Optional[Category]:
    """ Get Category by her ID """
    query = select(Category).where(Category.id == category_id)
    result = await session.execute(query)
    return result.scalar_one_or_none()



async def get_category_by_slug(session: AsyncSession, slug: str)-> Optional[Category]:
    """ Get Category by slug """
    query = select(Category).where(Category.slug == slug)
    result = await session.execute(query)
    return result.scalar_one_or_none




async def get_main_categories(session: AsyncSession, name: str)-> Optional[Category]:
    """ Get Category by name (for duplicate search)"""
    query = select(Category).where(Category.name == name)
    result = await session.execute(query)
    return result.scalar_one_or_none()





async def get_main_categories(session: AsyncSession) -> List[Category]:
    """Get main  (Tree)) Category"""
    query = select(Category).where(Category.is_main == True)
    result = await session.execute(query)
    return list(result.scalars().all())


async def get_subcategories_by_parent_id(session: AsyncSession, parent_id: int) -> List[Category]:
    """Get all subcategories by parent_id"""
    query = select(Category).where(Category.parent_id == parent_id)
    result = await session.execute(query)
    return list(result.scalars().all())


async def delete_category(session: AsyncSession, category_id: int) -> bool:
    """Delete category by ID. Retirn True, if approwe"""
    category = await get_category_by_id(session, category_id)
    if category:
        await session.delete(category)
        await session.commit()
        return True
    return False
 
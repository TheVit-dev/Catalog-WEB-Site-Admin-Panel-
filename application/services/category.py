# application/services/category.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from application.db.models import Category

def generate_slug(text: str) -> str:
    """Простейший транслит для перевода русских названий в читаемые ссылки (slug)"""
    cyrillic = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя '
    latin = ['a','b','v','g','d','e','yo','zh','z','i','y','k','l','m','n','o','p','r','s','t','u','f','kh','ts','ch','sh','shch','','y','','e','yu','ya','-']
    tr = {c: l for c, l in zip(cyrillic, latin)}
    
    text = text.lower().strip()
    # Заменяем кириллицу, оставляем только буквы, цифры и дефисы
    slug = "".join(tr.get(c, c) for c in text if c.isalnum() or c == ' ' or c == '-')
    # Убираем двойные дефисы, если они появились
    while '--' in slug:
        slug = slug.replace('--', '-')
    return slug

async def create_category(session: AsyncSession, name: str, parent_id: int = None, is_main: bool = False) -> Category:
    """Бизнес-логика создания новой категории"""
    slug = generate_slug(name)
    
    # Проверяем, нет ли уже категории с таким же slug
    existing = await session.execute(select(Category).where(Category.slug == slug))
    if existing.scalar_one_or_none():
        # Если такой slug есть, добавим уникальный хвост (для тестов упростим)
        import random
        slug = f"{slug}-{random.randint(10, 99)}"

    new_category = Category(
        name=name,
        slug=slug,
        parent_id=parent_id,
        is_main=is_main
    )
    
    session.add(new_category)
    await session.commit()
    await session.refresh(new_category)
    return new_category

async def get_all_categories(session: AsyncSession):
    """Получить список всех категорий для вывода на веб-странице"""
    result = await session.execute(select(Category).order_by(Category.id.desc()))
    return result.scalars().all()
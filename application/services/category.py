import os
import uuid
import aiofiles
from sqlalchemy.ext.asyncio import AsyncSession
from slugify import slugify  
from application.infrastructure.image_set import upload_image_to_s3, delete_image_from_s3
from application.db.models import Category 
from application.services.cache import delete_cached_catalog
from fastapi import HTTPException
from application.core.config import CACHE_KEY_CATALOG
from application.db.crud.category import (
    get_category_by_name,
    check_category_has_relations,
    delete_category_by_id
)


async def create_category_in_db(
    session: AsyncSession,
    name: str,
    parent_id: int | None,
    image_bytes: bytes,
    original_filename: str
):
    """
    Сервис создания категории: генерирует slug, сохраняет обложку и делает запись в БД.
    """



    # 1. Формируем уникальное имя файла
    ext = original_filename.split(".")[-1] if "." in original_filename else "jpg"
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    
    image_data = await upload_image_to_s3(file_bytes= image_bytes, original_filename=unique_filename)


    #  3. Генерируем slug из названия категории
    category_slug = slugify(name)
    is_main = parent_id in (None, 0, "0", "")
    clean_parent_id = None if is_main else int(parent_id)

    # Создаем инстанс модели SQLAlchemy
    new_category = Category(
        name=name,
        slug=category_slug,
        parent_id=clean_parent_id, # Сюда пойдет либо чистый int (1, 2, 3), либо None
        is_main=is_main,           # Сюда пойдет True или False
        image_url=image_data
    )

    # 5. Записываем в базу
    session.add(new_category)
    await session.commit()
    await session.refresh(new_category)
    await delete_cached_catalog(CACHE_KEY_CATALOG)
    return new_category


async def delete_category_by_name_service(db: AsyncSession, category_name: str) -> dict:
    """
    Сервисная функция для безопасного удаления категории по её названию.
    """

    
    # 1. Запрашиваем объект. Переменная называется category (без _id!)
    category = await get_category_by_name(db, category_name)
    if not category:
        raise HTTPException(
            status_code=404,
            detail=f"Категория «{category_name}» не найдена."
        )


    # 2. Передаем именно ЧИСЛО (category.id)
    has_relations = await check_category_has_relations(db, category.id)
    if has_relations:
        raise HTTPException(
            status_code=400,
            detail=f"Нельзя удалить категорию «{category_name}». В ней есть товары или подкатегории!"
        )
    

    # 3. Чистим бакет (передаем ссылку из объекта)
    if hasattr(category, "image_url") and category.image_url:
        await delete_image_from_s3(category.image_url)


    # 4. Удаляем из БД тоже по числу (category.id)
    is_deleted = await delete_category_by_id(db, category.id)
    if not is_deleted:
        raise HTTPException(
            status_code=500,
            detail="Произошла непредвиденная ошибка при удалении из базы данных."
        )
    

    await delete_cached_catalog(CACHE_KEY_CATALOG)


    return {
        "status": "success", 
        "message": f"Категория «{category_name}» успешно удалена."
    }
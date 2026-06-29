from fastapi import FastAPI, Depends, HTTPException, status, Form, File, UploadFile, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from application.db.database import get_db
from application.db.models import Product
from decimal import Decimal
from typing import Optional, List
from application.services.product import search_products_service
import logging
from application.services.product import save_new_product
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from application.db.database import get_db  # Твоя зависимость для сессии БД

# Импортируем нашу функцию удаления из сервиса
from application.services.product import delete_product

product_router = APIRouter(prefix="/api/products", tags=["Products"])


@product_router.get("/search", response_model=List[dict])
async def search_product_endpoint(
    slug: Optional[str] = None,
    name: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Эндпоинт для бота. Принимает параметры, дергает сервис.
    """
    if not slug and not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Передайте slug или name для поиска"
        )
        
    # Вызываем сервис
    products = await search_products_service(db=db, slug=slug, name=name)
    
    return products


@product_router.post("", status_code=status.HTTP_201_CREATED)
async def create_product_endpoint(
    # Принимаем текстовые поля через Form
    category_id: int = Form(..., description="ID категории"),
    title: str = Form(..., description="Название товара"),
    price: Decimal = Form(..., description="Цена товара"),
    description: str | None = Form(None, description="Описание товара"),
    
    # Принимаем массив файлов через File
    files: list[UploadFile] = File(..., description="Массив фотографий"),
    
    # Сессия БД
    session: AsyncSession = Depends(get_db)
):
    """
    Эндпоинт для создания нового товара с галереей изображений.
    """
    # 1. Базовая валидация: проверяем, что прислали хотя бы один файл
    if not files or len(files) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Необходимо загрузить хотя бы одну фотографию."
        )

    try:
        # 2. Читаем бинарные данные (bytes) из объектов UploadFile
        photos_bytes = []
        for file in files:
            content = await file.read()
            photos_bytes.append(content)
            
        # 3. Передаем всё в наш сервисный слой
        product_id = await save_new_product(
            session=session,
            category_id=category_id,
            title=title,
            description=description,
            price=price,
            files_data=photos_bytes
        )

        # 4. Возвращаем успешный ответ
        return {
            "status": "success",
            "message": f"Товар успешно создан. Загружено фото: {len(photos_bytes)}",
            "product_id": product_id
        }

    except Exception as e:
        # Логируем ошибку для дебага
        logging.error(f"Ошибка при создании товара на сервере: {e}")
        
        # Возвращаем 500 ошибку клиенту (боту)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера при сохранении товара: {str(e)}"
        )
    

@product_router.delete("/{product_id}", status_code=status.HTTP_200_OK)
async def delete_product_endpoint(
    product_id: int, 
    db: AsyncSession = Depends(get_db)
):
    """
    Эндпоинт для удаления товара по его ID.
    """
    # Дергаем сервис
    deleted = await delete_product(db=db, product_id=product_id)
    
    # Если сервис вернул False (товар не найден), выплевываем 404
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Товар с ID {product_id} не найден в базе данных"
        )
        
    # Если всё ок, отдаем статус успешного удаления
    return {"status": "success", "message": f"Товар с ID {product_id} успешно удален"}

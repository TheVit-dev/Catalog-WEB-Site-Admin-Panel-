from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from application.db.database import get_db  # Импортируй свою зависимость сессии
from application.services.structure_c_p import get_catalog_structure
import math
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from application.db.models import Product, ProductImage
from application.schemas.product_web_api import PaginatedProductResponse, CatalogStructureResponse
from application.services.structure_c_p import ProductService



DEFAULT_PAGE_SIZE = 12

web_catalog_router = APIRouter(prefix="/api/catalog", tags=["Catalog"])

@web_catalog_router.get("/structure", response_model=CatalogStructureResponse)
async def get_catalog(session: AsyncSession = Depends(get_db)):
    """
    Эндпоинт для получения всего каталога.
    """
    data = await get_catalog_structure(session)
    return data



@web_catalog_router.get("", response_model=PaginatedProductResponse)
async def get_products(
    category_id: int | None = Query(
        None, 
        description="ID категории. Если не передан, бэк вернет товары из всех категорий скопом."
    ),
    page: int = Query(
        1, 
        ge=1, 
        description="Номер запрашиваемой страницы. Должен быть >= 1."
    ),
    page_size: int = Query(
        12, 
        ge=1, 
        le=100, 
        description="Количество товаров на страницу. Минимум 1, максимум 100."
    ),
    db: AsyncSession = Depends(get_db)
):
    """
    Адаптивный эндпоинт каталога товаров.
    
    Принимает параметры фильтрации и пагинации через Query-параметры (строку запроса),
    отдает мета-данные для фронтенда и массив из 12 (или page_size) товаров с галереями.
    """
    return await ProductService.get_paginated_products(
        db=db,
        category_id=category_id,
        page=page,
        page_size=page_size
    )
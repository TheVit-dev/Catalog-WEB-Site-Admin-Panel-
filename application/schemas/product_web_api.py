from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime



class ProductSchema(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    price: str  # Оставляем str для Decimal
    category_id: int
    main_image: Optional[str] = None
    views_count: int
    is_available: bool
    created_at: datetime
    gallery: List[str] = []

    class Config:
        from_attributes = True


# Схема для мета-данных пагинации
class PaginationMeta(BaseModel):
    total_items: int
    total_pages: int
    current_page: int
    page_size: int
    has_next: bool
    has_prev: bool


# Финальный ответ, который увидит фронтенд
class PaginatedProductResponse(BaseModel):
    meta: PaginationMeta
    products: List[ProductSchema]


class CategoryStructureSchema(BaseModel):
    id: int
    name: str
    slug: str
    image_url: Optional[str] = None
    parent_id: Optional[int] = None
    is_main: bool

    class Config:
        from_attributes = True


class CatalogStructureResponse(BaseModel):
    categories: List[CategoryStructureSchema]
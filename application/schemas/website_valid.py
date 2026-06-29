from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

# Схема для товара
class ProductSchema(BaseModel):
    id: int
    name: str = Field(..., min_length=2, max_length=100)
    price: float = Field(..., gt=0)  # Цена строго больше нуля
    in_stock: bool = True
    image_url: Optional[str] = None

# Схема для категории (базовая)
class CategorySchema(BaseModel):
    id: int
    name: str = Field(..., min_length=2, max_length=50)
    slug: str  # url-friendly имя, например "toys-for-couples"
    parent_id: Optional[int] = None  # Ссылка на ID родительской категории
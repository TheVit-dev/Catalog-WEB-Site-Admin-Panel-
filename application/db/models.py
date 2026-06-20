# application/db/models.py
from datetime import datetime
from typing import List, Optional
from sqlalchemy import ForeignKey, String, Text, Numeric, Boolean, DateTime, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# Базовый класс, от которого наследуются модели
class Base(DeclarativeBase):
    pass



class Category(Base):
    __tablename__ = "categories"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    # Убрали лишний index=True, unique=True достаточно
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False) 
    image_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    
    # ДОБАВИЛИ ИНДЕКС: теперь поиск подкатегорий будет летать
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), nullable=True, index=True
    )
    is_main: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # ... связи остаются прежними ...


class Product(Base):
    __tablename__ = "products"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # ДОБАВИЛИ ИНДЕКС: критически важно для выборки товаров по категории!
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    
    # ДОБАВИЛИ ИНДЕКС: чтобы быстро собирать "Топ популярных товаров"
    views_count: Mapped[int] = mapped_column(Integer, default=0, index=True)
    
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # ДОБАВИЛИ ИНДЕКС: чтобы быстро собирать "Новинки" (сортировка ORDER BY created_at DESC)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    
    # ... связи остаются прежними ...
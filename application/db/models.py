# application/db/models.py
from datetime import datetime
from decimal import Decimal
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
    
    # Индекс для быстрой фильтрации по категориям
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True) # Стиль Python 3.10+
    
    # Меняем float на Decimal, чтобы копейки не терялись
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    # Главная обложка товара (для каталога)
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    
    # Индекс для топа популярных
    views_count: Mapped[int] = mapped_column(Integer, default=0, index=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Индекс для новинок. Используем default без скобок (), чтобы время генерировалось в момент вставки
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    
    # СВЯЗЬ: Дополнительные фотки (галерея)
    # cascade="all, delete-orphan" означает: если удалить товар, его галерея в БД тоже сотрется
    images: Mapped[list["ProductImage"]] = relationship(
        "ProductImage", 
        back_populates="product", 
        cascade="all, delete-orphan",
        lazy="selectin"
    )


class ProductImage(Base):
    __tablename__ = "product_images"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    image_url: Mapped[str] = mapped_column(String(512), nullable=False)
    
    product: Mapped["Product"] = relationship("Product", back_populates="images")
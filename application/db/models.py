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
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    
    # ВОТ ОНА — НАША НОВАЯ КОЛОНКА ДЛЯ S3 ССЫЛОК КАТЕГОРИЙ
    image_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), nullable=True
    )
    is_main: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # СВЯЗИ (Relationships) остаются прежними
    subcategories: Mapped[List["Category"]] = relationship(
        "Category", back_populates="parent", remote_side=[id]
    )
    parent: Mapped[Optional["Category"]] = relationship(
        "Category", back_populates="subcategories"
    )
    products: Mapped[List["Product"]] = relationship(
        "Product", back_populates="category"
    )

class Product(Base):
    __tablename__ = "products"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Ограничиваем цену: 10 знаков всего, 2 после запятой (например, 9999999.99)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    
    image_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    views_count: Mapped[int] = mapped_column(Integer, default=0)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # СВЯЗЬ: позволяет у товара вызвать .category и узнать все о его разделе
    category: Mapped["Category"] = relationship("Category", back_populates="products")
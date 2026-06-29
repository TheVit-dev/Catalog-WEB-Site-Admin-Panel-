from decimal import Decimal
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from application.db.models import Product, ProductImage
from application.infrastructure.image_set import upload_image_to_s3, delete_image_from_s3
from typing import Optional, List, Dict, Any
from application.services.cache import delete_cached_catalog
from application.db.crud.product import get_products_by_search
import asyncio
import uuid


async def save_new_product(
    session: AsyncSession, 
    category_id: int, 
    title: str, 
    description: str | None, 
    price: Decimal, 
    files_data: list[bytes]
) -> int:
    """
    Оптимизированный сервис для создания товара в БД:
    1. Асинхронно и параллельно загружает массив картинок в S3 (Tebi.io).
    2. Инициализирует модель Product, устанавливая первую ссылку как обложку.
    3. Создает записи в таблице `ProductImage` для остальных ссылок.
    4. Сохраняет всё в базу за одну транзакцию.
    """
    
    # 1. Формируем список задач для параллельной отправки в S3
    upload_tasks = []
    for img_bytes in files_data:
        file_name = f"products/{uuid.uuid4()}.jpg"
        # Мы НЕ делаем await здесь! Мы просто создаем корутину и кладем в список
        upload_tasks.append(
            upload_image_to_s3(file_bytes=img_bytes, original_filename=file_name)
        )
        
    # 2. Выполняем все загрузки ОДНОВРЕМЕННО
    # Если хоть одна картинка упадет с ошибкой сети, gather прервет процесс 
    # и выкинет Exception. До БД дело даже не дойдет (что нам и нужно).
    # Функция вернет готовый список ссылок (строк) в том же порядке, в каком мы их закинули.
    uploaded_urls = await asyncio.gather(*upload_tasks)

    # 3. Собираем объект товара
    new_product = Product(
        category_id=category_id,
        title=title,
        description=description,
        price=price,
        # Забираем первую ссылку из полученного списка под обложку
        image_url=uploaded_urls[0] if uploaded_urls else None 
    )
    
    # 4. Если ссылок больше одной, остальные пакуем в галерею
    if len(uploaded_urls) > 1:
        # Берем срез списка начиная со второго элемента [1:]
        for url in uploaded_urls[1:]:
            product_image = ProductImage(image_url=url)
            new_product.images.append(product_image)

    # 5. Фиксируем всё в БД
    session.add(new_product)
    await session.commit()
    await session.refresh(new_product)
    await delete_cached_catalog("product_structure")
    
    return new_product.id


async def delete_product(db: AsyncSession, product_id: int) -> bool:
    """
    Удаляет товар, всю его галерею картинок из S3 и записи из БД.
    """
    try:
        # 1. Находим сам товар (для главной картинки)
        product = await db.get(Product, product_id)
        if not product:
            print(f"Товар с ID {product_id} не найден.")
            return False

        # 2. Достаем ВСЕ дополнительные картинки из галереи ProductImage
        # Делаем это ДО удаления, пока связи в БД ещё живы
        images_query = select(ProductImage).where(ProductImage.product_id == product_id)
        images_result = await db.execute(images_query)
        gallery_images = images_result.scalars().all()

        # ==========================================
        # 🔥 ЧИСТКА S3 БАКЕТА (TEBI.IO)
        # ==========================================
        
        # А. Чистим главную картинку товара
        if hasattr(product, "image_url") and product.image_url:
            await delete_image_from_s3(product.image_url)

        # Б. Циклом чистим ВСЕ картинки из галереи в S3
        for img in gallery_images:
            # Замени 'image_url' на реальное имя поля в модели ProductImage, если оно другое
            if hasattr(img, "image_url") and img.image_url:
                await delete_image_from_s3(img.image_url)

        # ==========================================
        # 🗑️ УДАЛЕНИЕ ИЗ БАЗЫ ДАННЫХ
        # ==========================================
        
        # Если на уровне базы данных (Foreign Key) у тебя настроено ON DELETE CASCADE,
        # то при удалении product строки из ProductImage удалятся автоматически.
        # На всякий случай удалим их принудительно, если каскад не настроен:
        for img in gallery_images:
            await db.delete(img)

        # Удаляем сам товар
        await db.delete(product)
        
        # Фиксируем все изменения одной транзакцией
        await db.commit()
        
        print(f"Товар {product_id} и вся его галерея успешно удалены.")
        return True

    except Exception as e:
        await db.rollback()
        print(f"Ошибка при полном удалении товара {product_id}: {e}")
        return False


async def search_products_service(
    db: AsyncSession, 
    slug: Optional[str] = None, 
    name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Бизнес-логика поиска: дергает CRUD и мапит модели в список словарей,
    который ожидает получить Телеграм-бот.
    """
    # Вызываем CRUD-функцию
    db_products = await get_products_by_search(db=db, slug=slug, name=name)

    # Формируем структуру [{"id": 1, "name": "Член"}, ...]
    return [{"id": p.id, "name": p.title} for p in db_products]
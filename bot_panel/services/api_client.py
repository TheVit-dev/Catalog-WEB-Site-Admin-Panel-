import aiohttp
import asyncio
import logging
from typing import Optional, List, Dict, Any
import os
from dotenv import load_dotenv
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from application.db.models import Category


load_dotenv()


BASE_URL = os.getenv("API_URL")


async def fetch_categories_list() -> Dict[str, Any]:
    """
    Получает структуру категорий (плоский список со связями parent_id) с бэкенда.
    Ручка FastAPI: /catalog/structure
    """
    url = f"{BASE_URL}/catalog/structure"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.json()  # Прилетит словарь {"categories": [...]}
                
                print(f"Бэкэнд вернул статус {resp.status} для {url}")
                return {"categories": []}
                
    except Exception as e:
        print(f"Ошибка в get_category_structure: {e}")
        return {"categories": []}


async def find_category_by_name(name: str):
    """
    Get category by name.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/categories/search?name={name}") as resp:
                if resp.status == 200:
                    category_id = await resp.json()  # Тут уже лежит готовое число (например, 5) или null
                    return category_id
    except Exception as e:
        print(f"Ошибка в боте при поиске категории: {e}")
    return None


async def create_category_on_backend(
    name: str, 
    parent_id: str, 
    file_bytes: bytes, 
    filename: str = "cover.jpg"
) -> tuple[bool, str]:
    """
    Form multipart/form-data and push from backend.
    """
    try:
        form = aiohttp.FormData()
        form.add_field("name", name)
        
        # Если не "0", значит есть родитель — передаем его ID
        if parent_id != "0":
            form.add_field("parent_id", parent_id)
            
        # Ключ "image" должен совпадать с тем, что ждет FastAPI (image: UploadFile = File(...))
        form.add_field("image", file_bytes, filename=filename, content_type="image/jpeg")

        async with aiohttp.ClientSession() as session:
            async with session.post(f"{BASE_URL}/categories", data=form) as resp:
                if resp.status == 200:
                    return True, "✅ Категория успешно создана!"
                
                error_text = await resp.text()
                return False, f"Ошибка бэкенда: {error_text}"
    except Exception as e:
        return False, f"Ошибка сети: {str(e)}"
    

async def create_product_in_backend(
    category_id: int, 
    title: str, 
    description: str | None, 
    price: float, 
    photos_bytes: list[bytes]
) -> dict:
    """
    Send data on backend (aiohttp).
    """
    url = f"{BASE_URL}/products"
    
    # 1. Создаем объект FormData
    form_data = aiohttp.FormData()
    
    # 2. Упаковываем текстовые поля (обязательно приводим к строке)
    form_data.add_field("category_id", str(category_id))
    form_data.add_field("title", title)
    form_data.add_field("price", str(price))
    
    # Описание добавляем только если оно есть
    if description and description != "0":
        form_data.add_field("description", description)

    # 3. Упаковываем файлы.
    # Обрати внимание: первый аргумент ("files") - это имя поля, которое ждет FastAPI.
    # Так как файлов несколько, мы просто добавляем их с одним и тем же ключом в цикле.
    for index, img_bytes in enumerate(photos_bytes):
        form_data.add_field(
            "files",                     # Имя ключа (как в ручке FastAPI)
            img_bytes,                   # Сами байты
            filename=f"photo_{index}.jpg", # Имя файла
            content_type="image/jpeg"    # MIME-тип
        )

    # 4. Настраиваем таймаут (60 секунд, чтобы успели улететь на S3)
    timeout = aiohttp.ClientTimeout(total=60.0)

    # 5. Делаем POST-запрос
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, data=form_data) as response:
                
                # Если бэк ответил 201 Created
                if response.status == 201:
                    return await response.json()
                
                # Читаем текст ошибки, если что-то пошло не так
                error_text = await response.text()
                logging.error(f"Ошибка бэкенда при создании товара: {error_text}")
                
                return {
                    "status": "error", 
                    "detail": f"Код {response.status}. Ошибка сервера."
                }
                
    except asyncio.TimeoutError:
        logging.error("Таймаут запроса: бэкенд слишком долго сохранял картинки.")
        return {"status": "error", "detail": "Превышено время ожидания сервера (Таймаут)."}
        
    except aiohttp.ClientError as e:
        logging.error(f"Сетевая ошибка при отправке товара на бэкенд: {e}")
        return {"status": "error", "detail": "Нет связи с бэкендом."}
    

async def delete_category_request(category_name: str) -> dict:
    """
    Отправляет запрос на удаление категории на бэкенд.
    Возвращает словарь со статусом и текстом сообщения.
    """
    url = f"{BASE_URL}/categories/{category_name}" # URL твоего FastAPI в докере
    
    async with aiohttp.ClientSession() as session:
        async with session.delete(url) as response:
            if response.status == 200:
                return {"success": True, "text": f"✅ Категория **«{category_name}»** успешно удалена!"}
            
            # Ловим нашу 400 ошибку (когда есть связи) или 404 (не найдено)
            elif response.status in (400, 404):
                error_data = await response.json()
                # Берем текст ошибки прямо из detail, который мы прописали в FastAPI
                error_msg = error_data.get("detail", "Ошибка при удалении.")
                return {"success": False, "text": f"⚠️ {error_msg}"}
            
            else:
                return {"success": False, "text": "❌ Внутренняя ошибка сервера. Проверь логи."}


async def get_product_info_request(value: str, search_type: str) -> Optional[Dict[str, Any]]:
    """
    Ищет товар на бэкенде по слагу (если была ссылка) или по точному названию.
    search_type может быть "link" (ищем по slug) или "text" (ищем по name).
    Возвращает словарь {"id": 123, "name": "..."} или None, если не найдено.
    """
    # Допустим, на бэке у тебя будет ручка GET /products/search
    # с query-параметрами: ?slug=... или ?name=...
    
    params = {"slug": value} if search_type == "link" else {"name": value}
    url = f"{BASE_URL}/products/search"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # Если бэк возвращает массив совпадений, берем первое точное
                    if data and isinstance(data, list):
                        return data[0]
                    return data
                return None
    except Exception as e:
        print(f"Ошибка get_product_info_request: {e}")
        return None


async def delete_product_by_id_request(product_id: int) -> Dict[str, Any]:
    """
    Отправляет запрос на бэкенд для удаления товара строго по его ID.
    Ожидает эндпоинт вида: DELETE /products/{product_id}
    """
    url = f"{BASE_URL}/products/{product_id}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.delete(url) as resp:
                if resp.status == 200:
                    # Успешное удаление
                    return {"success": True, "detail": "Товар удален"}
                elif resp.status == 404:
                    return {"success": False, "detail": "Товар с таким ID не найден"}
                else:
                    return {"success": False, "detail": f"Ошибка сервера: {resp.status}"}
    except Exception as e:
        print(f"Ошибка delete_product_by_id_request: {e}")
        return {"success": False, "detail": "Нет связи с сервером"}
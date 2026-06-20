import aiohttp
from typing import Optional, List, Dict, Any
import os
from dotenv import load_dotenv

BASE_URL = os.getenv("DATABASE_URL", "0")

async def fetch_categories_list() -> List[Dict[str, Any]]:
    """Тянет список всех категорий для подсказки."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/categories") as resp:
                if resp.status == 200:
                    return await resp.json()
                return []
    except Exception:
        return []




async def find_category_by_name(name: str) -> Optional[int]:
    """Ищет категорию по имени и возвращает её ID на бэкенде."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/categories/search", params={"name": name}) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("id")
                return None
    except Exception:
        return None




async def create_category_on_backend(
    name: str, 
    parent_id: str, 
    file_bytes: bytes, 
    filename: str = "cover.jpg"
) -> tuple[bool, str]:
    """Формирует multipart/form-data и пушит на бэкенд."""
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
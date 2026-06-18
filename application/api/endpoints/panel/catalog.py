
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

router = APIRouter(prefix="/api/categories", tags=["Categories"])


@router.post("")  # Итоговый путь: POST /api/categories
async def api_create_category_test(
    name: str = Form(...),                  
    is_main: bool = Form(False),            
    image_file: UploadFile = File(None)     
):
    """Заглушка для создания категории (допилю завтра)"""
    pass


@router.get("/search")  # Итоговый путь: GET /api/categories/search
async def search_category_by_name(name: str):
    """Заглушка для поиска категории по имени (допилю завтра)"""
    pass
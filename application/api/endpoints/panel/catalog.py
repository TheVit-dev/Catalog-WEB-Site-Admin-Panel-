from fastapi import APIRouter, Form, File, UploadFile, HTTPException, Depends, FastAPI, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from application.db.crud.category import get_all_rows_name_c, get_id_by_category_name
from application.db.database import get_db
from application.services.category import create_category_in_db
from application.services.category import delete_category_by_name_service
from application.db.models import Category
from application.schemas.category import CategoryShortResponse
from typing import List


category_router = APIRouter()


@category_router.post("/api/categories")
async def create_category_endpoint(
    name: str = Form(...),
    parent_id: Optional[int] = Form(None),
    image: UploadFile = File(...),
    session: AsyncSession = Depends(get_db) 
):
    """
    Create CATEGORY
    """

    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Разрешены только изображения.")
    

    try:
        file_bytes = await image.read()

        # Передаем работу сервису
        created_category = await create_category_in_db(
            session=session,
            name=name,
            parent_id=parent_id,
            image_bytes=file_bytes,
            original_filename=image.filename
        )

        return {
            "status": "success",
            "message": "Категория успешно создана",
            "category": {
                "id": created_category.id, # Предполагается, что БД выдаст ID
                "name": created_category.name,
                "image_url": created_category.image_url
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при сохранении: {str(e)}")
    

@category_router.get("/api/categories/search")
async def search_categories_endpoint(
    name: str = Query(..., description="Название категории для поиска её ID"),
    session: AsyncSession = Depends(get_db)
):
    """
    Search CATEGORY by her NAME
    """
    try:
        category_id = await get_id_by_category_name(session=session, name=name)
        
        return category_id
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при поиске категорий: {str(e)}")


@category_router.get("/api/categories/all")
async def get_all_category_name(session: AsyncSession = Depends(get_db)):
    """
    Get all CATEGORY NAME
    """
    return await get_all_rows_name_c(session=session)

@category_router.delete("/api/categories/{category_name}")
async def delete_category_endpoint(category_name: str, db: AsyncSession = Depends(get_db)):
    # Просто вызываем сервис одной строчкой
    return await delete_category_by_name_service(db, category_name)





from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

get_static_router = APIRouter(tags=["Фронтенд страницы"])

# 1. Говорим FastAPI, где искать CSS и картинки
get_static_router.mount("/static", StaticFiles(directory="public/static"), name="static")

# 2. Указываем папку с HTML шаблонами
templates = Jinja2Templates(directory="public/templates")

# 3. Единственная ручка для Главной страницы
@get_static_router.get("/", response_class=HTMLResponse)
async def read_main(request: Request):
    return templates.TemplateResponse(
    request=request, 
    name="pages/index.html"
)

@get_static_router.get("/about", response_class=HTMLResponse)
async def read_about(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="pages/about.html"
    )


@get_static_router.get("/location", response_class=HTMLResponse)
async def read_location(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="pages/location.html"
    )

@get_static_router.get("/socials", response_class=HTMLResponse)
async def read_socials(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="pages/socials.html"
    )


@get_static_router.get("/delivery", response_class=HTMLResponse)
async def read_delivery(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="pages/delivery.html"
    )
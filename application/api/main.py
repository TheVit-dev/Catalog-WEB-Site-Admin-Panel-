import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Импортируем наши роутеры. 
# Замени 'app.routers...' на свой реальный путь, если он отличается.
from application.api.endpoints.panel.catalog import category_router
from application.api.endpoints.panel.products import product_router
from application.api.endpoints.web.catalog_web import web_catalog_router
from application.api.endpoints.web.get_static import get_static_router

# Настраиваем базовое логирование, чтобы видеть ошибки в консоли
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

# Инициализируем приложение
app = FastAPI(
    title="Telegram Shop API",
    description="API для работы с товарами и категориями через Telegram-бота",
    version="1.0.0",
    docs_url="/docs",   # Swagger UI доступен по этому адресу
    redoc_url="/redoc"  # Альтернативная документация
)

# Настройка CORS (Cross-Origin Resource Sharing)
# Это обязательно, если к твоему API будет обращаться веб-сайт (Web App / Mini App)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В проде лучше указывать конкретные домены, но для старта пойдет "*"
    allow_credentials=True,
    allow_methods=["*"],  # Разрешаем все методы (GET, POST, PUT, DELETE)
    allow_headers=["*"],  # Разрешаем все заголовки
)

# Подключаем роутеры к основному приложению
# Обрати внимание: префиксы (типа /api/products) мы уже задали внутри самих файлов роутеров,
# поэтому здесь просто инклудим их.
app.include_router(category_router)
app.include_router(product_router)
app.include_router(web_catalog_router)
app.include_router(get_static_router)
# Базовый эндпоинт для проверки жизнеспособности сервера (Healthcheck)
@app.get("/", tags=["Healthcheck"])
async def root_healthcheck():
    return {
        "status": "ok",
        "message": "API работает в штатном режиме. Перейдите на /docs для просмотра документации."
    }
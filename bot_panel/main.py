# main.py
import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

# ИМПОРТИРУЕМ НАШ РОУТЕР
# (Укажи правильный путь, смотря как называется и где лежит файл с FSM)
from bot_panel.callback.categories_wizard import router as categories_router
from bot_panel.handlers.handlers_menu import admin_router
from bot_panel.callback.product_wizard import product_router
from bot_panel.callback.delete_categoties import delete_categories_router
from bot_panel.callback.delete_product import delete_product_router
load_dotenv()

async def main():
    # Включаем логирование, чтобы видеть ошибки в терминале
    logging.basicConfig(level=logging.INFO)
    
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise ValueError("❌ Токен бота не найден в переменных окружения (.env)!")

    bot = Bot(token=bot_token)
    dp = Dispatcher()

    # ПОДКЛЮЧАЕМ РОУТЕР К ДИСПЕТЧЕРУ
    dp.include_router(admin_router)
    dp.include_router(categories_router)
    dp.include_router(product_router)
    dp.include_router(delete_categories_router)
    dp.include_router(delete_product_router)
    

    print("🤖 Бот успешно запущен и слушает команды...")
    
    # Запускаем polling (опрос серверов Телеграма)
    await dp.start_polling(bot, drop_pending_updates=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("🤖 Бот остановлен.")
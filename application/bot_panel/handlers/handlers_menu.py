# bot/handlers.py
import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from application.bot_panel.keyboards.inline_keyboards import first_message_inline_button
from dotenv import load_dotenv

load_dotenv()

admin_router = Router()

# Подтягиваем ID друга из переменных окружения. Если его нет, по дефолту 0 (доступ закрыт)
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

@admin_router.message(CommandStart())
async def cmd_start(message: Message):
    """Ловит команду /start и проверяет права доступа."""
    
    # Железобетонная проверка «свой/чужой» прямо на месте
    if message.from_user.id != ADMIN_ID:
        await message.answer(f"❌ Доступ ограничен. Вы не являетесь администратором. {message.from_user.id}")
        return
    
    # Если это админ — вызываем функцию клавиатуры и отправляем меню
    await message.answer(
        text="Добро пожаловать в Admin-Panel. Выберите действие:",
        reply_markup=first_message_inline_button()
    )

# Пример того, как ты дальше будешь ловить нажатия на эти кнопки:
@admin_router.callback_query(F.data == "admin_help")
async def process_help_button(callback: CallbackQuery):
    """Пример обработки кнопки 'Справка'"""
    await callback.message.answer("Здесь будет инструкция по управлению магазином.")
    await callback.answer() # Обязательно гасим часики на кнопке в ТГ
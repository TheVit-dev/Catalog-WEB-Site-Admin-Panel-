from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def first_message_inline_button() -> InlineKeyboardMarkup:
    """Генерирует главное меню админки из 9 инлайн-кнопок."""
    builder = InlineKeyboardBuilder()
    
    # Список твоих 9 кнопок (Текст кнопки, callback_data для отлова нажатия)
    # Callback_data — это то, что полетит бэкенду при нажатии
    buttons = [
        ("📦 Добавить товар", "add_product"),
        ("🗑️ Удалить товар", "delete_product"),
        ("📁 Добавить категорию", "add_category"),
        ("📂 Удалить категорию", "delete_category"),
        ("📊 Статистика товаров", "view_stats"),
        ("👥 Метрика посещений", "web_metrics"),
        ("❓ Помощь / Команды", "admin_help")
    ]
    
    for text, callback_data in buttons:
        builder.add(InlineKeyboardButton(text=text, callback_data=callback_data))
    
    # Сетка: adjust(2) означает выводить по 2 кнопки в ряд. 
    # Девятая кнопка автоматически встанет одна в самый низ — будет выглядеть аккуратно.
    builder.adjust(2) 
    
    return builder.as_markup()


inline_menu_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Вернуться в меню", callback_data="back_to_main_menu")]
    ]
)
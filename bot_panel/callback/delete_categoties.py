from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from bot_panel.services.api_client import fetch_categories_list, delete_category_request
from bot_panel.keyboards.inline_keyboards import inline_menu_kb, first_message_inline_button
from bot_panel.services.validation_json import format_category_tree
from bot_panel.services.api_client import fetch_categories_list

# 1. Объявляем состояние
class DeleteCategoryFSM(StatesGroup):
    waiting_for_name = State()
delete_categories_router = Router()
# 2. Кнопка в меню: Вывод списка и запрос имени
@delete_categories_router.callback_query(F.data == "delete_category")
async def start_delete_category(call: CallbackQuery, state: FSMContext):
    await state.set_state(DeleteCategoryFSM.waiting_for_name)
    
    # Запоминаем ID сообщения, чтобы перезаписывать его
    await state.update_data(menu_message_id=call.message.message_id)
    
    # 1. Получаем структуру категорий с бэкенда через новую ручку
    json_data = await fetch_categories_list()
    
    # 2. Строим красивое дерево через наш парсер
    cats_text = format_category_tree(json_data)

    # 3. Выводим результат юзеру
    await call.message.edit_text(
        text=f"🗑 Введи точное НАЗВАНИЕ категории для удаления:\n\n🗂 **Текущая структура каталога:**\n{cats_text}",
        reply_markup=inline_menu_kb,  # Твоя кнопка отмены
        parse_mode="Markdown"         # Чтобы дерево и заголовки не поплыли
    )
    await call.answer()

# 3. Ловим введенное имя и дергаем API
@delete_categories_router.message(DeleteCategoryFSM.waiting_for_name)
async def process_delete_category_name(message: Message, state: FSMContext, bot: Bot):
    category_name = message.text.strip()
    
    # Подчищаем за юзером его сообщение с текстом
    try:
        await message.delete()
    except Exception:
        pass

    user_data = await state.get_data()
    menu_msg_id = user_data.get("menu_message_id")

    # Дергаем нашу функцию запроса к бэкенду
    result = await delete_category_request(category_name)
    
    if result["success"]:
        # Если удалилось — сбрасываем состояние
        await state.clear()
        
        # Редактируем меню, сообщаем об успехе. 
        # (Замени None на клавиатуру твоего главного админ-меню, чтобы юзер мог продолжить работу)
        final_markup = first_message_inline_button
    else:
        # Если ошибка (опечатка или в категории есть товары) — оставляем юзера в состоянии FSM, 
        # чтобы он мог попробовать ввести имя еще раз, и добавляем кнопку отмены.
        final_markup = inline_menu_kb
        result["text"] += "\n\nПопробуй ввести другое название или нажми Отмена:"

    try:
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=menu_msg_id,
            text=result["text"],
            parse_mode="Markdown",
            reply_markup=final_markup
        )
    except Exception:
        pass
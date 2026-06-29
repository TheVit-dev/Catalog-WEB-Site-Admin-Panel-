from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from bot_panel.keyboards.inline_keyboards import first_message_inline_button
from bot_panel.services.validation_json import validate_category_name, parse_parent_input
from bot_panel.services.validation_json import format_category_tree
from bot_panel.services.api_client import (
    fetch_categories_list, 
    find_category_by_name, 
    create_category_on_backend
)
from bot_panel.keyboards.inline_keyboards import inline_menu_kb
router = Router()

class CategoryFSM(StatesGroup):
    name = State()
    parent = State()
    photo = State()


# 1. СТАРТ (Редактируем старое меню)
@router.callback_query(F.data == "add_category")
async def start_category_creation(call: CallbackQuery, state: FSMContext):
    await state.set_state(CategoryFSM.name)
    
    # КРИТИЧЕСКИ ВАЖНО: Запоминаем ID сообщения, которое будем постоянно редактировать
    await state.update_data(menu_message_id=call.message.message_id)
    
    # Меняем текст самого меню вместо отправки нового сообщения
    await call.message.edit_text("📝 Введи название новой категории:", reply_markup=inline_menu_kb)
    await call.answer()


# 2. ИМЯ (ОБНОВЛЕННЫЙ ХЭНДЛЕР)
@router.message(CategoryFSM.name)
async def process_category_name(message: Message, state: FSMContext, bot: Bot):
    # Сразу чистим за юзером его ввод
    try:
        await message.delete()
    except Exception:
        pass

    user_data = await state.get_data()
    menu_msg_id = user_data.get("menu_message_id")

    is_valid, result = validate_category_name(message.text)
    if not is_valid:
        try:
            await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=menu_msg_id,
                text=f"⚠️ {result}\nПопробуй еще раз:"
            )
        except Exception:
            pass
        return

    await state.update_data(name=result)

    # ВЫЗЫВАЕМ ТВОЮ НОВУЮ РУЧКУ СТРУКТУРЫ
    json_data = await fetch_categories_list()
    
    # Прогоняем сырой JSON через парсер дерева
    cats_text = format_category_tree(json_data)

    await state.set_state(CategoryFSM.parent)
    
    try:
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=menu_msg_id,
            text=(
                f"Отлично! Теперь укажи **НАЗВАНИЕ** родительской категории (или отправь 0, если это главная).\n\n"
                f"🗂 **Текущая структура каталога:**\n{cats_text}"
            ),
            parse_mode="Markdown"
        )
    except Exception:
        pass


# 3. РОДИТЕЛЬ
@router.message(CategoryFSM.parent)
async def process_category_parent(message: Message, state: FSMContext, bot: Bot):
    # Удаляем ввод юзера
    try:
        await message.delete()
    except Exception:
        pass

    user_data = await state.get_data()
    menu_msg_id = user_data.get("menu_message_id")
    parent_input = parse_parent_input(message.text)

    if parent_input == "0":
        await state.update_data(parent_id="0")
        await state.set_state(CategoryFSM.photo)
        try:
            await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=menu_msg_id,
                text="Понял, это будет главная категория.\n📸 Теперь отправь картинку-обложку:"
            )
        except Exception:
            pass
        return

    # Запрашиваем ID у бэкенда
    parent_id = await find_category_by_name(parent_input)
    
    if parent_id:
        await state.update_data(parent_id=str(parent_id))
        await state.set_state(CategoryFSM.photo)    
        try:
            await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=menu_msg_id,
                text=f"✅ Найдена категория (ID: {parent_id})\n📸 Теперь отправь картинку-обложку:"
            )
        except Exception:
            pass
    else:
        try:
            await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=menu_msg_id,
                text=f"❌ Категория с названием «{parent_input}» не найдена.\nПроверь название или отправь 0."
            )
        except Exception:
            pass


from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton # <-- Добавь импорт кнопок

# 4. ФОТО И ОТПРАВКА
@router.message(CategoryFSM.photo, F.photo)
async def process_category_photo(message: Message, state: FSMContext, bot: Bot):
    # Удаляем сообщение с фоткой от юзера
    try:
        await message.delete()
    except Exception:
        pass

    user_data = await state.get_data()
    menu_msg_id = user_data.get("menu_message_id")
    name = user_data.get("name")
    parent_id = user_data.get("parent_id")
    
    # Меняем статус прямо в основном сообщении
    try:
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=menu_msg_id,
            text="⏳ Скачиваю фото и отправляю на бэкенд..."
        )
    except Exception:
        pass
    
    # Скачиваем байты картинки
    file_id = message.photo[-1].file_id
    file_info = await bot.get_file(file_id)
    downloaded_file = await bot.download_file(file_info.file_path)
    file_bytes = downloaded_file.read()

    # Пушим всё на сервер
    success, result_msg = await create_category_on_backend(
        name=name,  
        parent_id=parent_id,
        file_bytes=file_bytes
    )

    # Выводим финальный результат в то же самое сообщение, прикрепляя кнопку
    try:
        if success:
            await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=menu_msg_id,
                text=f"🎉 {result_msg}",
                reply_markup=inline_menu_kb # <-- Привязали кнопку к успеху
            )
        else:
            await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=menu_msg_id,
                text=f"❌ Не удалось создать:\n{result_msg}",
                reply_markup=inline_menu_kb # <-- Привязали кнопку к ошибке
            )
    except Exception:
        pass

    # Чистим стейт, чтобы юзер вышел из машины состояний
    await state.clear()



@router.callback_query(F.data == "back_to_main_menu")
async def back_to_menu_handler(call: CallbackQuery, state: FSMContext):
    # На всякий случай сбрасываем стейт, если юзер вернулся в меню посреди процесса
    await state.clear()
    
    try:
        # Редактируем сообщение с ошибкой/успехом обратно в главное меню!
        await call.message.edit_text(
            text="Добро пожаловать в Admin-Panel. Выберите действие:",
            reply_markup=first_message_inline_button()
        )
    except Exception:
        pass
        
    await call.answer()


@router.callback_query(F.data == "back_to_main_menu")
async def cancel_category_creation(call: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        # Если почему-то состояния не было, просто гасим часики на кнопке
        await call.answer()
        return

    # Очищаем состояние (выходим из FSM сценария)
    await state.clear()
    
    # Редактируем сообщение, возвращая юзера в главное меню админки
    # (Замени текст и клавиатуру на те, которые у тебя используются в главном меню)
    await call.message.edit_text(
        "Главное меню админ-панели. Действие успешно отменено.",
        reply_markup=first_message_inline_button # <-- Сюда закинь свою клавиатуру админки
    )
    await call.answer("Действие отменено ❌")
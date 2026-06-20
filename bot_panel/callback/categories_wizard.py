from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

# Чистые импорты наших новых модулей
from bot_panel.utils.validators import validate_category_name, parse_parent_input
from bot_panel.services.api_client import (
    fetch_categories_list, 
    find_category_by_name, 
    create_category_on_backend
)

router = Router()

class CategoryFSM(StatesGroup):
    name = State()
    parent = State()
    photo = State()

# 1. СТАРТ
@router.callback_query(F.data == "add_category")
async def start_category_creation(call: CallbackQuery, state: FSMContext):
    await state.set_state(CategoryFSM.name)
    await call.message.answer("📝 Введи название новой категории:")
    await call.answer()

# 2. ИМЯ
@router.message(CategoryFSM.name)
async def process_category_name(message: Message, state: FSMContext):
    # Используем утилиту валидации
    is_valid, result = validate_category_name(message.text)
    if not is_valid:
        await message.answer(f"⚠️ {result}\nПопробуй еще раз:")
        return

    await state.update_data(name=result)

    # Дергаем чистый сервис API
    categories = await fetch_categories_list()
    cats_text = "Категорий пока нет. Эта будет первой!"
    if categories:
        cats_text = "\n".join([f"- {c['name']}" for c in categories])

    await state.set_state(CategoryFSM.parent)
    await message.answer(
        f"Отлично! Теперь укажи **НАЗВАНИЕ** родительской категории (или отправь 0, если это главная).\n\n"
        f"📂 Существующие категории:\n{cats_text}",
        parse_mode="Markdown"
    )

# 3. РОДИТЕЛЬ
@router.message(CategoryFSM.parent)
async def process_category_parent(message: Message, state: FSMContext):
    parent_input = parse_parent_input(message.text)
    
    if parent_input == "0":
        await state.update_data(parent_id="0")
        await state.set_state(CategoryFSM.photo)
        await message.answer("Понял, это будет главная категория.\n📸 Теперь отправь картинку-обложку:")
        return

    # Запрашиваем ID у бэкенда через сервис
    parent_id = await find_category_by_name(parent_input)
    
    if parent_id:
        await state.update_data(parent_id=str(parent_id))
        await state.set_state(CategoryFSM.photo)
        await message.answer(
            f"✅ Найдена категория (ID: {parent_id})\n"
            f"📸 Теперь отправь картинку-обложку:"
        )
    else:
        await message.answer(
            f"❌ Категория с названием «{parent_input}» не найдена.\n"
            f"Проверь название или отправь 0."
        )

# 4. ФОТО И ОТПРАВКА
@router.message(CategoryFSM.photo, F.photo)
async def process_category_photo(message: Message, state: FSMContext, bot: Bot):
    status_msg = await message.answer("⏳ Скачиваю фото и отправляю на бэкенд...")
    
    # 1. Достаем данные из машины состояний
    user_data = await state.get_data()
    name = user_data.get("name")
    parent_id = user_data.get("parent_id")
    
    # 2. Скачиваем байты картинки силами aiogram
    file_id = message.photo[-1].file_id
    file_info = await bot.get_file(file_id)
    downloaded_file = await bot.download_file(file_info.file_path)
    file_bytes = downloaded_file.read()

    # 3. Пушим всё на сервер через наш чистый API-клиент
    success, result_msg = await create_category_on_backend(
        name=name,
        parent_id=parent_id,
        file_bytes=file_bytes
    )

    if success:
        await status_msg.edit_text(result_msg)
    else:
        await status_msg.edit_text(f"❌ Не удалось создать:\n{result_msg}")

    await state.clear()
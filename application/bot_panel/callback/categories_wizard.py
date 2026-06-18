# application/bot_panel/categories_wizard.py
import aiohttp
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

router = Router()

class CategoryFSM(StatesGroup):
    name = State()
    parent = State()
    photo = State()

# 1. ЛОВИМ КЛИК ПО ИНЛАЙН-КНОПКЕ "Добавить категорию"
@router.callback_query(F.data == "add_category")
async def start_category_creation(call: CallbackQuery, state: FSMContext):
    await state.set_state(CategoryFSM.name)
    await call.message.answer("📝 Введи название новой категории:")
    await call.answer()

# 2. ПОЛУЧАЕМ ИМЯ -> запрашиваем НАЗВАНИЕ родителя
@router.message(CategoryFSM.name)
async def process_category_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)

    # Тянем список существующих категорий для подсказки
    cats_text = "Категорий пока нет. Эта будет первой!"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://127.0.0.1:8000/api/categories") as resp:
                if resp.status == 200:
                    categories = await resp.json()
                    if categories:
                        cats_text = "\n".join([f"- {c['name']}" for c in categories]) # ID юзеру больше видеть не нужно!
    except Exception as e:
        cats_text = "⚠️ Не удалось загрузить список существующих категорий с сервера."

    await state.set_state(CategoryFSM.parent)
    # Поправили текст: теперь просим именно НАЗВАНИЕ, а не ID
    await message.answer(
        f"Отлично! Теперь укажи **НАЗВАНИЕ** родительской категории (или отправь 0, если это главная категория).\n\n"
        f"📂 Существующие категории:\n{cats_text}",
        parse_mode="Markdown"
    )

# 3. ПОЛУЧАЕМ НАЗВАНИЕ РОДИТЕЛЯ -> Ищем ID на бэкенде -> просим фото
@router.message(CategoryFSM.parent)
async def process_category_parent(message: Message, state: FSMContext):
    parent_name = message.text.strip()
    
    # Если ввели "0", значит это главная категория
    if parent_name == "0":
        await state.update_data(parent_id="0")
        await state.set_state(CategoryFSM.photo)
        await message.answer("Понял, это будет главная категория.\n📸 Теперь отправь картинку-обложку:")
        return

    # Стучимся во FastAPI искать ID по имени
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "http://127.0.0.1:8000/api/categories/search", 
                params={"name": parent_name}
            ) as resp:
                
                if resp.status == 200:
                    category_data = await resp.json()
                    parent_id = category_data.get("id")
                    
                    # Сохраняем найденный ID под капотом FSM
                    await state.update_data(parent_id=str(parent_id))
                    
                    await state.set_state(CategoryFSM.photo)
                    await message.answer(
                        f"✅ Найдена категория: *{category_data['name']}* (ID: {parent_id})\n"
                        f"📸 Теперь отправь картинку-обложку:",
                        parse_mode="Markdown"
                    )
                elif resp.status == 404:
                    await message.answer(
                        f"❌ Категория с названием «{parent_name}» не найдена.\n"
                        f"Попробуй ввести еще раз точное название или отправь 0."
                    )
                else:
                    await message.answer("⚠️ Ошибка бэкенда при поиске. Попробуй ещё раз.")
                    
    except Exception as e:
        await message.answer(f"❌ Не удалось связаться с сервером для проверки имени: {e}")

# 4. ЛОВИМ КАРТИНКУ -> качаем в RAM и пушим в FastAPI
@router.message(CategoryFSM.photo, F.photo)
async def process_category_photo(message: Message, state: FSMContext, bot: Bot):
    file_id = message.photo[-1].file_id
    status_msg = await message.answer("⏳ Обрабатываю изображение и отправляю на бэкенд...")

    user_data = await state.get_data()
    name = user_data.get("name")
    parent_id = user_data.get("parent_id")

    try:
        file_info = await bot.get_file(file_id)
        downloaded_file = await bot.download_file(file_info.file_path)
        file_bytes = downloaded_file.read()

        is_main = "true" if parent_id == "0" else "false"

        form = aiohttp.FormData()
        form.add_field("name", name)
        form.add_field("is_main", is_main)
        form.add_field("image_file", file_bytes, filename="category_cover.jpg", content_type="image/jpeg")

        async with aiohttp.ClientSession() as session:
            async with session.post("http://127.0.0.1:8000/api/categories", data=form) as resp:
                if resp.status == 200:
                    await status_msg.edit_text("✅ Категория успешно создана! Картинка загружена в Tebi.io.")
                else:
                    error_text = await resp.text()
                    await status_msg.edit_text(f"❌ Бэкенд вернул ошибку: {error_text}")

    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка при отправке данных: {e}")

    await state.clear()
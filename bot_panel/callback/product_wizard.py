from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from bot_panel.services.api_client import fetch_categories_list, create_product_in_backend, find_category_by_name
from bot_panel.keyboards.inline_keyboards import inline_menu_kb, first_message_inline_button
from bot_panel.services.validation_json import format_category_tree

product_router = Router()

class ProductFSM(StatesGroup):
    title = State()
    description = State()
    price = State()
    photos = State()
    category = State()


# 1. СТАРТ ВИЗАРДА
@product_router.callback_query(F.data == "add_product")
async def start_product_creation(call: CallbackQuery, state: FSMContext):
    await state.set_state(ProductFSM.title)
    
    # Запоминаем ID сообщения-меню для последующего редактирования
    await state.update_data(menu_message_id=call.message.message_id)
    
    await call.message.edit_text("📝 Укажите название товара:", reply_markup=inline_menu_kb)
    await call.answer()


# 2. НАЗВАНИЕ
@product_router.message(ProductFSM.title, F.text)
async def process_product_title(message: Message, state: FSMContext, bot: Bot):
    try: await message.delete()
    except Exception: pass

    user_data = await state.get_data()
    menu_msg_id = user_data.get("menu_message_id")

    await state.update_data(title=message.text)
    await state.set_state(ProductFSM.description)
    
    try:
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=menu_msg_id,
            text="Укажите описание товара (или отправьте 0, если описания нет):"
        )
    except Exception: pass


# 3. ОПИСАНИЕ
@product_router.message(ProductFSM.description, F.text)
async def process_product_description(message: Message, state: FSMContext, bot: Bot):
    try: await message.delete()
    except Exception: pass

    user_data = await state.get_data()
    menu_msg_id = user_data.get("menu_message_id")

    description = None if message.text == "0" else message.text
    await state.update_data(description=description)
    await state.set_state(ProductFSM.price)
    
    try:
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=menu_msg_id,
            text="💰 Укажите цену товара (только число, например: 1500 или 99.90):"
        )
    except Exception: pass


# 4. ЦЕНА
@product_router.message(ProductFSM.price, F.text)
async def process_product_price(message: Message, state: FSMContext, bot: Bot):
    try: await message.delete()
    except Exception: pass

    user_data = await state.get_data()
    menu_msg_id = user_data.get("menu_message_id")

    try:
        price = float(message.text.replace(",", "."))
    except ValueError:
        try:
            await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=menu_msg_id,
                text="⚠️ Ошибка! Цена должна быть числом.\n💰 Укажите цену товара:"
            )
        except Exception: pass
        return

    await state.update_data(price=price, photos=[]) # Создаем пустой список для фото
    await state.set_state(ProductFSM.photos)
    
    try:
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=menu_msg_id,
            text=(
                "📸 Прикрепите фотографии товара (максимум 5 шт.).\n"
                "Можно отправлять по одной или сразу альбомом.\n\n"
                "👉 **Если это все (или если фото больше нет), отправьте 0.**"
            ),
            parse_mode="Markdown"
        )
    except Exception: pass


# 5. ФОТОГРАФИИ (Ловим сами картинки)
@product_router.message(ProductFSM.photos, F.photo)
async def process_product_photos(message: Message, state: FSMContext, bot: Bot):
    try: await message.delete()
    except Exception: pass

    user_data = await state.get_data()
    menu_msg_id = user_data.get("menu_message_id")
    photos_list = user_data.get("photos", [])

    # Берем самое высокое качество фото (последний элемент массива)
    file_id = message.photo[-1].file_id
    
    if len(photos_list) < 5:
        photos_list.append(file_id)
        await state.update_data(photos=photos_list)
        
        # Обновляем текст, показывая сколько фото уже загружено
        try:
            await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=menu_msg_id,
                text=(
                    f"✅ Фото добавлено ({len(photos_list)}/5).\n"
                    "Отправьте еще фото или отправьте **0**, чтобы перейти к категории."
                ),
                parse_mode="Markdown"
            )
        except Exception: pass
        
        # Если достигли лимита в 5 фото, сразу перекидываем на следующий шаг
        if len(photos_list) == 5:
            await jump_to_category_step(message.chat.id, state, bot, menu_msg_id)
    else:
        # Если юзер пытается прислать 6-е фото
        try:
            await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=menu_msg_id,
                text="⚠️ Достигнут лимит (5/5). Отправьте **0**, чтобы продолжить.",
                parse_mode="Markdown"
            )
        except Exception: pass


# 5.1. ФОТОГРАФИИ (Команда завершения "0")
@product_router.message(ProductFSM.photos, F.text == "0")
async def process_photos_done(message: Message, state: FSMContext, bot: Bot):
    try: await message.delete()
    except Exception: pass

    user_data = await state.get_data()
    menu_msg_id = user_data.get("menu_message_id")
    photos_list = user_data.get("photos", [])

    if not photos_list:
        try:
            await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=menu_msg_id,
                text="⚠️ Нужно прикрепить хотя бы одно фото!\nПрикрепите фотографию:"
            )
        except Exception: pass
        return

    await jump_to_category_step(message.chat.id, state, bot, menu_msg_id)


# ОДНА функция, которая заменит оба твоих куска кода
async def jump_to_category_step(chat_id: int, state: FSMContext, bot: Bot, menu_msg_id: int):
    """
    Вспомогательная функция для перевода пользователя на шаг выбора категории товара.
    Выводит красивое дерево категорий и ожидает ввод названия.
    """
    # Переводим FSM в состояние ожидания категории для товара
    await state.set_state(ProductFSM.category)
    
    # 1. Запрашиваем структуру категорий через нашу новую ручку API
    json_data = await fetch_categories_list()
    
    # 2. Собираем красивое дерево (функция format_category_tree должна быть доступна/импортирована)
    cats_text = format_category_tree(json_data)

    try:
        # 3. Редактируем сообщение, выводя красивую иерархию
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=menu_msg_id,
            text=(
                f"📂 **Укажите НАЗВАНИЕ категории для товара из списка:**\n\n"
                f"🗂 **Текущая структура каталога:**\n{cats_text}\n\n"
                f"⚠️ *Пишите название точно так же, как в списке выше (учитывая регистр).*"
            ),
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Ошибка при редактировании сообщения в jump_to_category_step: {e}")


# 6. КАТЕГОРИЯ И ФИНАЛЬНАЯ ОТПРАВКА НА БЭК
@product_router.message(ProductFSM.category, F.text)
async def process_product_category(message: Message, state: FSMContext, bot: Bot):
    try: await message.delete()
    except Exception: pass

    user_data = await state.get_data()
    menu_msg_id = user_data.get("menu_message_id")
    
    # Забираем текст, который ввел юзер
    category_name = message.text.strip()

    # Сразу показываем, что процесс пошел
    try:
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=menu_msg_id,
            text=f"🔍 Ищу категорию «{category_name}»..."
        )
    except Exception: pass

    # Отправляем запрос на бэк, чтобы получить ID по названию
    category_id = await find_category_by_name(category_name)

    # Защита от опечаток (если бэкенд не нашел категорию и вернул None/False)
    if not category_id:
        try:
            await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=menu_msg_id,
                text=f"⚠️ Категория «{category_name}» не найдена.\nПожалуйста, проверьте правильность названия и отправьте его снова:"
            )
        except Exception: pass
        return

    # Меняем статус на скачивание, если категория найдена
    try:
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=menu_msg_id,
            text="⏳ Категория найдена! Скачиваю файлы и отправляю товар на бэкенд..."
        )
    except Exception: pass

    # --- Подготовка данных ---
    title = user_data.get("title")
    description = user_data.get("description")
    price = user_data.get("price")
    photos_file_ids = user_data.get("photos", [])

    # Скачиваем все фото в память (bytes)
    photos_bytes_list = []
    for f_id in photos_file_ids:
        file_info = await bot.get_file(f_id)
        downloaded_file = await bot.download_file(file_info.file_path)
        photos_bytes_list.append(downloaded_file.read())

    # Пушим на бэкенд (используем имя функции, как ты указал: creacte_product_in_backend)
    response = await create_product_in_backend(
        category_id=category_id,
        title=title,
        description=description,
        price=price,
        photos_bytes=photos_bytes_list
    )

    # Клавиатура для возврата
    inline_menu_kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="📱 Главное меню", callback_data="back_to_main_menu")]]
    )

    # Финальный ответ
    try:
        if response.get("status") == "success":
            await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=menu_msg_id,
                text="🎉 Товар успешно создан и добавлен в каталог!",
                reply_markup=inline_menu_kb
            )
        else:
            await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=menu_msg_id,
                text=f"❌ Ошибка бэкенда:\n{response.get('detail', 'Неизвестная ошибка')}",
                reply_markup=inline_menu_kb
            )
    except Exception: pass

    # Очищаем состояние
    await state.clear()


@product_router.callback_query(F.data == "back_to_main_menu")
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
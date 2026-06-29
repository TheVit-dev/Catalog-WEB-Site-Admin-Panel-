from aiogram import F, Router, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from bot_panel.keyboards.inline_keyboards import inline_menu_kb, first_message_inline_button
from bot_panel.services.api_client import delete_product_by_id_request, get_product_info_request
from bot_panel.services.validation_json import parse_product_input
from bot_panel.keyboards.inline_keyboards import inline_menu_kb, first_message_inline_button

delete_product_router =Router()


class DeleteProductFSM(StatesGroup):
    waiting_for_input = State()



@delete_product_router.callback_query(F.data == "delete_product")
async def start_delete_product(call: CallbackQuery, state: FSMContext):
    # Переходим в состояние ожидания текста или ссылки
    await state.set_state(DeleteProductFSM.waiting_for_input)
    
    # Запоминаем ID сообщения, чтобы не плодить новые, а редактировать старое
    await state.update_data(menu_message_id=call.message.message_id)
    
    await call.message.edit_text(
        text=(
            "🗑 **Удаление товара**\n\n"
            "Отправь мне **ссылку на товар** с сайта\n"
            "или введи его **ТОЧНОЕ НАЗВАНИЕ**:"
        ),
        reply_markup=inline_menu_kb, # Твоя кнопка "Отмена / Назад"
        parse_mode="Markdown"
    )
    await call.answer()


@delete_product_router.message(DeleteProductFSM.waiting_for_input)
async def process_product_delete(message: Message, state: FSMContext, bot: Bot):
    # 1. Сразу чистим чат от сообщения админа
    try:
        await message.delete()
    except Exception:
        pass

    user_data = await state.get_data()
    menu_msg_id = user_data.get("menu_message_id")

    # 2. Прогоняем ввод через наш валидатор (ссылка это или текст?)
    parsed_data = parse_product_input(message.text)
    
    if parsed_data["type"] == "error":
        try:
            await bot.edit_message_text(
                chat_id=message.chat.id, message_id=menu_msg_id,
                text=f"⚠️ {parsed_data['value']}\nПопробуй прислать корректную ссылку или точное название:",
                reply_markup=inline_menu_kb # Кнопка отмены
            )
            print(parsed_data)
        except Exception: pass
        return

    # 3. Ищем ID товара на бэкенде
    product_info = await get_product_info_request(
        value=parsed_data["value"], 
        search_type=parsed_data["type"]
    )

    if not product_info or "id" not in product_info:
        try:
            await bot.edit_message_text(
                chat_id=message.chat.id, message_id=menu_msg_id,
                text=(
                    f"🤷‍♂️ Товар по запросу **'{parsed_data['value']}'** не найден.\n"
                    f"Проверь правильность ввода или скопируй точную ссылку с сайта и попробуй еще раз:"
                ),
                reply_markup=inline_menu_kb,
                parse_mode="Markdown"
            )
        except Exception: pass
        return

    # 4. Товар найден! Достаем ID и удаляем
    product_id = product_info["id"]
    product_name = product_info.get("name", "Без названия")
    
    delete_result = await delete_product_by_id_request(product_id)

    # 5. Выводим финальный результат
    if delete_result["success"]:
        await state.clear()
        try:
            await bot.edit_message_text(
                chat_id=message.chat.id, message_id=menu_msg_id,
                text=f"✅ Товар **{product_name}** (ID: {product_id}) успешно удален из базы!",
                parse_mode="Markdown",
                reply_markup=inline_menu_kb
                # Тут можно прикрутить кнопку "Вернуться в главное меню"
            )
        except Exception: pass
    else:
        try:
            await bot.edit_message_text(
                chat_id=message.chat.id, message_id=menu_msg_id,
                text=f"❌ Ошибка при удалении: {delete_result['detail']}\nПопробуй еще раз:",
                reply_markup=inline_menu_kb
            )
        except Exception: pass


@delete_product_router.callback_query(F.data == "back_to_main_menu")
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
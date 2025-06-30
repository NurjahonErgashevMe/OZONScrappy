import logging
from aiogram import Dispatcher, F, Bot
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from src.bot.handlers.base import (
    start_command,
    parse_seller_products,
    parse_inn_command,
    parse_products_inn_command,
    parse_category_inn_command  # Новый импорт
)
from src.bot.handlers.seller_handling import handle_seller_url
from src.bot.handlers.inn_handling import handle_inn_urls
from src.bot.handlers.category_handling import handle_category_url  # Новый импорт
from src.bot.states import ParserStates
from src.utils import load_config

logger = logging.getLogger('bot.register_handlers')

# Загрузка конфигурации
config = load_config("config.txt")

# Устанавливаем ALLOWED_CHAT_ID, если TELEGRAM_CHAT_ID задан
ALLOWED_CHAT_ID = None
chat_id = config.get("TELEGRAM_CHAT_ID", "")
if chat_id:
    try:
        ALLOWED_CHAT_ID = int(chat_id)
        logger.info(f"ALLOWED_CHAT_ID установлен: {ALLOWED_CHAT_ID}")
    except ValueError:
        logger.warning(f"Некорректный TELEGRAM_CHAT_ID: {chat_id}, бот будет работать без ограничения chat_id")
else:
    logger.info("TELEGRAM_CHAT_ID не задан или пустой в config.txt, бот будет работать без ограничения chat_id")

async def check_chat_id(message: Message) -> bool:
    """Промежуточная проверка chat_id"""
    if ALLOWED_CHAT_ID is None:
        return True  # Пропускаем проверку, если chat_id не задан
    if message.chat.id != ALLOWED_CHAT_ID:
        await message.reply("Вам доступ запрещен.")
        return False
    return True

def create_handler(handler):
    """Фабрика для создания обработчиков с проверкой chat_id"""
    async def wrapped_handler(message: Message, state: FSMContext = None):
        if not await check_chat_id(message):
            return
        if state:
            await handler(message, state)
        else:
            await handler(message)
    return wrapped_handler

def register_handlers(dp: Dispatcher, bot: Bot):
    """Регистрация всех обработчиков с проверкой chat_id"""
    # Регистрация базовых команд
    dp.message.register(
        create_handler(start_command), 
        Command("start")
    )
    dp.message.register(
        create_handler(parse_seller_products), 
        F.text == "🔍 Парсинг продавца и товары"
    )
    dp.message.register(
        create_handler(parse_inn_command), 
        F.text == "🆔 Парсинг ИНН продавцов"
    )
    dp.message.register(
        create_handler(parse_products_inn_command), 
        F.text == "📦 Парсинг ИНН из товаров"
    )
    # Новый обработчик для парсинга категорий
    dp.message.register(
        create_handler(parse_category_inn_command), 
        F.text == "🏷️ Парсинг ИНН по категориям"
    )

    # Регистрация обработчиков состояний
    dp.message.register(
        create_handler(lambda m, s: handle_seller_url(m, s, bot)),
        ParserStates.waiting_seller_url
    )
    dp.message.register(
        create_handler(lambda m, s: handle_inn_urls(m, s, bot, mode='sellers')),
        ParserStates.waiting_seller_urls_for_inn
    )
    dp.message.register(
        create_handler(lambda m, s: handle_inn_urls(m, s, bot, mode='products')),
        ParserStates.waiting_product_urls_for_inn
    )
    # Новый обработчик состояния для категорий
    dp.message.register(
        create_handler(lambda m, s: handle_category_url(m, s, bot)),
        ParserStates.waiting_category_url
    )

    logger.info("Все обработчики успешно зарегистрированы")
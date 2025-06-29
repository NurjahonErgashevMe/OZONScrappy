import logging
from aiogram import Dispatcher, F, Bot
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from bot.handlers.base import (
    start_command,
    parse_seller_products,
    parse_inn_command,
    parse_products_inn_command
)
from bot.handlers.seller_handling import handle_seller_url
from bot.handlers.inn_handling import handle_inn_urls
from bot.states import ParserStates

logger = logging.getLogger('bot.register_handlers')

def register_handlers(dp: Dispatcher, bot: Bot):
    """Регистрация всех обработчиков с передачей бота"""
    # Базовые команды
    dp.message.register(start_command, Command("start"))
    dp.message.register(parse_seller_products, F.text == "🔍 Парсинг продавца и товары")
    dp.message.register(parse_inn_command, F.text == "🆔 Парсинг ИНН продавцов")
    dp.message.register(parse_products_inn_command, F.text == "📦 Парсинг ИНН из товаров")
    
    # Создаем обертки для обработчиков
    async def seller_wrapper(message: Message, state: FSMContext):
        await handle_seller_url(message, state, bot)
    
    async def inn_sellers_wrapper(message: Message, state: FSMContext):
        await handle_inn_urls(message, state, bot, mode='sellers')
    
    async def inn_products_wrapper(message: Message, state: FSMContext):
        await handle_inn_urls(message, state, bot, mode='products')
    
    # Регистрируем обработчики состояний
    dp.message.register(
        seller_wrapper,
        ParserStates.waiting_seller_url
    )
    
    dp.message.register(
        inn_sellers_wrapper,
        ParserStates.waiting_seller_urls_for_inn
    )
    
    dp.message.register(
        inn_products_wrapper,
        ParserStates.waiting_product_urls_for_inn
    )
    
    logger.info("Все обработчики успешно зарегистрированы")
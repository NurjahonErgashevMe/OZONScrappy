import logging
from aiogram import types
from aiogram.fsm.context import FSMContext
from src.bot.keyboards import main_keyboard, cancel_keyboard
from src.bot.states import ParserStates

logger = logging.getLogger('bot.base_handlers')

async def start_command(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🤖 Привет! Я бот для парсинга данных с Ozon.\n"
        "Выберите действие из меню ниже:",
        reply_markup=main_keyboard()
    )

async def parse_seller_products(message: types.Message, state: FSMContext):
    await state.set_state(ParserStates.waiting_seller_url)
    await message.answer(
        "🔍 Пожалуйста, отправьте ссылку на продавца Ozon.\n"
        "Пример: https://www.ozon.ru/seller/trade-electronics-183434/",
        reply_markup=cancel_keyboard()
    )

async def parse_inn_command(message: types.Message, state: FSMContext):
    await state.set_state(ParserStates.waiting_seller_urls_for_inn)
    await message.answer(
        "🆔 Отправьте ссылки на продавцов (каждая с новой строки):\n\n"
        "Пример:\n"
        "https://www.ozon.ru/seller/prodavec-1/\n"
        "https://www.ozon.ru/seller/prodavec-2/",
        reply_markup=cancel_keyboard()
    )

async def parse_products_inn_command(message: types.Message, state: FSMContext):
    await state.set_state(ParserStates.waiting_product_urls_for_inn)
    await message.answer(
        "📦 Отправьте ссылки на товары (каждая с новой строки):\n\n"
        "Пример:\n"
        "https://www.ozon.ru/product/tovar-1/\n"
        "https://www.ozon.ru/product/tovar-2/",
        reply_markup=cancel_keyboard()
    )
    
async def parse_category_inn_command(message: types.Message, state: FSMContext):
    """Команда для запуска парсинга ИНН по категориям"""
    await state.set_state(ParserStates.waiting_category_url)
    await message.reply(
        "🏷️ **Парсинг ИНН по категориям**\n\n"
        "Отправьте ссылку на категорию товаров Ozon для парсинга ИНН продавцов\n\n"
        "📝 **Формат ссылки:**\n"
        "`https://www.ozon.ru/category/название-категории-ID/`\n\n"
        "📄 **Примеры:**\n"
        "• `https://www.ozon.ru/category/kruizery-11080/`\n"
        "• `https://www.ozon.ru/category/elektronnye-knigi-15458/`\n"
        "• `https://www.ozon.ru/category/smartfony-15502/`\n\n"
        "⚙️ **Настройки парсинга:**\n"
        "• Максимум страниц: настраивается в config.txt (MAX_CATEGORY_PAGES)\n"
        "• Товаров на странице: настраивается в config.txt (MAX_PRODUCTS_PER_PAGE)\n\n"
        "⏳ Парсинг может занять от 5 до 20 минут в зависимости от размера категории",
        reply_markup=cancel_keyboard()
    )
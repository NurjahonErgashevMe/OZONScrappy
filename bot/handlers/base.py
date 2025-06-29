import logging
from aiogram import types
from aiogram.fsm.context import FSMContext
from bot.keyboards import main_keyboard, cancel_keyboard
from bot.states import ParserStates

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
import logging
import asyncio
from aiogram import F, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from bot.keyboards import main_keyboard
from bot.states import ParserStates
from parse_seller_and_products import parse_seller_and_products
from parse_inn import run_inn_parser
from parse_products_inn import run_product_inn_parser

logger = logging.getLogger(__name__)

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
        "Пример: https://www.ozon.ru/seller/trade-electronics-183434/"
    )

async def handle_seller_url(message: types.Message, state: FSMContext):
    url = message.text
    # Простая валидация URL
    if not url.startswith('https://www.ozon.ru/seller/'):
        await message.answer("❌ Неверная ссылка на продавца. Попробуйте еще раз.")
        return
    
    await message.answer(f"⏳ Начинаю парсинг продавца: {url}...")
    
    try:
        # Запускаем парсинг в отдельном потоке
        result = await asyncio.to_thread(parse_seller_and_products, url, True)
        
        if result:
            # Форматируем результат
            response = (
                f"🏪 *Информация о продавце:*\n"
                f"• Название: {result['seller'].get('seller_name', 'N/A')}\n"
                f"• Премиум: {'✅ Да' if result['seller'].get('is_premium') else '❌ Нет'}\n"
                f"• Заказов: {result['seller'].get('orders_count', 'N/A')}\n"
                f"• Работает с: {result['seller'].get('working_since', 'N/A')}\n"
                f"• Рейтинг: {result['seller'].get('average_rating', 'N/A')} "
                f"(отзывов: {result['seller'].get('reviews_count', 'N/A')})\n"
                f"• Компания: {result['seller'].get('company_name', 'N/A')}\n"
                f"• ИНН: {result['seller'].get('inn', 'N/A')}\n\n"
                f"📦 *Товары:* {len(result['products']) if result['products'] else 0} спарсено"
            )
            await message.answer(response, parse_mode="Markdown")
        else:
            await message.answer("❌ Не удалось получить данные о продавце.")
            
    except Exception as e:
        logger.error(f"Ошибка парсинга: {e}")
        await message.answer(f"⚠️ Произошла ошибка при парсинге: {str(e)}")
    
    await state.clear()

async def parse_inn_command(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🆔 Начинаю парсинг ИНН продавцов...")
    
    try:
        # Запускаем парсинг в отдельном потоке
        result = await asyncio.to_thread(run_inn_parser)
        await message.answer(result[:4000])  # Ограничение Telegram на длину сообщения
    except Exception as e:
        logger.error(f"Ошибка парсинга ИНН: {e}")
        await message.answer(f"⚠️ Произошла ошибка: {str(e)}")

async def parse_products_inn_command(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("📦 Начинаю парсинг ИНН из товаров...")
    
    try:
        # Запускаем парсинг в отдельном потоке
        result = await asyncio.to_thread(run_product_inn_parser)
        await message.answer(result[:4000])  # Ограничение Telegram на длину сообщения
    except Exception as e:
        logger.error(f"Ошибка парсинга ИНН из товаров: {e}")
        await message.answer(f"⚠️ Произошла ошибка: {str(e)}")
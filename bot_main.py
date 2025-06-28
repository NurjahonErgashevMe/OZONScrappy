import logging
from aiogram import Bot, Dispatcher
from aiogram import types, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from bot.handlers import (
    start_command,
    parse_seller_products,
    handle_seller_url,
    parse_inn_command,
    parse_products_inn_command
)
from bot.states import ParserStates
from dotenv import load_dotenv
import os

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def main():
    bot = Bot(token=TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Регистрация обработчиков
    dp.message.register(start_command, Command("start"))
    dp.message.register(parse_seller_products, F.text == "🔍 Парсинг продавца и товары")
    dp.message.register(parse_inn_command, F.text == "🆔 Парсинг ИНН продавцов")
    dp.message.register(parse_products_inn_command, F.text == "📦 Парсинг ИНН из товаров")
    dp.message.register(handle_seller_url, ParserStates.waiting_seller_url)

    # Запуск бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
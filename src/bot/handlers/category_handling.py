import asyncio
from src.parser.category_inn_parser.main import CategoryParser
from aiogram import Bot
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext
from src.bot.keyboards import main_keyboard
import logging
import os

logger = logging.getLogger('bot.category_handler')


async def send_typing_action(bot: Bot, chat_id: int):
    """Отправляет действие 'typing' каждые 30 секунд, чтобы поддерживать соединение"""
    try:
        while True:
            await bot.send_chat_action(chat_id=chat_id, action="typing")
            await asyncio.sleep(30)
    except asyncio.CancelledError:
        # Когда задача отменена, просто выходим
        pass


async def handle_category_url(message: Message, state: FSMContext, bot: Bot):
    """Обработчик URL категории"""
    category_url = message.text.strip()

    # Проверяем, что это ссылка на категорию Ozon
    if not category_url.startswith('https://www.ozon.ru/category/'):
        await message.reply(
            "❌ Неверный формат ссылки!\n\n"
            "Пожалуйста, отправьте ссылку на категорию Ozon в формате:\n"
            "`https://www.ozon.ru/category/название-категории-ID/`\n\n"
            "Например: `https://www.ozon.ru/category/kruizery-11080/`"
        )
        return

    await state.clear()

    # Уведомляем пользователя о начале парсинга
    await message.reply(
        "🔄 **Начинаем парсинг категории...**\n\n"
        "⏳ Это может занять несколько минут (5–20 минут).\n"
        "📊 Мы уведомим вас, как только парсинг завершится."
    )

    # Создаем задачу для отправки "typing" уведомлений
    typing_task = asyncio.create_task(send_typing_action(bot, message.chat.id))

    try:
        # Асинхронный парсинг
        parser = CategoryParser()
        sellers_data = await asyncio.get_event_loop().run_in_executor(
            None, parser.parse_category, category_url
        )

        # Отменяем задачу "typing"
        typing_task.cancel()

        # Проверяем результат
        if not sellers_data or '_files' not in sellers_data:
            raise ValueError("Парсинг завершен, но данные не были получены.")

        # Получаем пути к файлам
        excel_filepath = sellers_data['_files']['excel']
        txt_filepath = sellers_data['_files']['txt']
        
        logger.info(f"Excel файл: {excel_filepath}")
        logger.info(f"TXT файл: {txt_filepath}")

        # Проверяем существование файлов
        if not os.path.exists(excel_filepath):
            raise FileNotFoundError(f"Excel файл не найден: {excel_filepath}")
        if not os.path.exists(txt_filepath):
            raise FileNotFoundError(f"TXT файл не найден: {txt_filepath}")

        # Отправка Excel файла с использованием FSInputFile
        excel_file = FSInputFile(excel_filepath)
        await bot.send_document(
            chat_id=message.chat.id,
            document=excel_file,
            caption=f"📄 Данные продавцов из категории {sellers_data['_files']['category_name']} (Excel)"
        )

        # Отправка TXT файла с использованием FSInputFile
        txt_file = FSInputFile(txt_filepath)
        await bot.send_document(
            chat_id=message.chat.id,
            document=txt_file,
            caption="📄 TXT файл с ИНН продавцов"
        )

        # Подсчитываем количество продавцов (исключая служебные ключи)
        sellers_count = len([k for k in sellers_data.keys() if not k.startswith('_')])

        await message.reply(
            "✅ **Парсинг завершен!**\n\n"
            f"📊 Найдено продавцов: {sellers_count}\n\n"
            "Спасибо за использование нашего бота!",
            reply_markup=main_keyboard()
        )

    except FileNotFoundError as e:
        # Обработка отсутствия файлов
        typing_task.cancel()
        logger.error(f"Файл не найден: {str(e)}")
        await message.reply(
            "❌ Не удалось найти файл для отправки.\n"
            "Возможно, парсинг завершился с ошибкой.",
            reply_markup=main_keyboard()
        )
    except Exception as e:
        # Общая обработка ошибок
        typing_task.cancel()
        logger.error(f"Ошибка при отправке файлов: {str(e)}")
        await message.reply(
            f"❌ Произошла ошибка: {str(e)}",
            reply_markup=main_keyboard()
        )
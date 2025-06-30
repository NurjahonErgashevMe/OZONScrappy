from src.parser.category_inn_parser import CategoryParser
from aiogram import Dispatcher, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from src.bot.keyboards import main_keyboard, cancel_keyboard
import logging


logger = logging.getLogger('bot.category_handler')


async def handle_category_url(message: Message, state: FSMContext, bot):
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
    
    # Отправляем сообщение о начале парсинга
    status_message = await message.reply(
        "🔄 **Начинаем парсинг категории...**\n\n"
        "⏳ Это может занять несколько минут\n"
        "📊 Будем собирать информацию о продавцах и их товарах"
    )
    
    try:
        # Создаем парсер и запускаем парсинг
        parser = CategoryParser()
        sellers_data = parser.parse_category(category_url)
        
        # Форматируем и отправляем результаты
        results_text = parser.format_results(sellers_data)
        
        # Удаляем статус сообщение
        await bot.delete_message(message.chat.id, status_message.message_id)
        
        # Разбиваем длинный текст на части если нужно
        if len(results_text) > 4000:
            parts = [results_text[i:i+4000] for i in range(0, len(results_text), 4000)]
            for i, part in enumerate(parts):
                if i == 0:
                    await message.reply(part, reply_markup=main_keyboard())
                else:
                    await message.reply(part)
        else:
            await message.reply(results_text, reply_markup=main_keyboard())
            
    except Exception as e:
        logger.error(f"Ошибка при парсинге категории: {str(e)}")
        
        # Удаляем статус сообщение
        try:
            await bot.delete_message(message.chat.id, status_message.message_id)
        except:
            pass
            
        await message.reply(
            f"❌ **Ошибка при парсинге категории**\n\n"
            f"Описание ошибки: {str(e)}\n\n"
            "Попробуйте позже или с другой категорией",
            reply_markup=main_keyboard()
        )
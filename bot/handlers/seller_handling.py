import logging
import asyncio
import os
from aiogram import types
from aiogram.fsm.context import FSMContext
from parse_seller_and_products import parse_seller_and_products
from bot.keyboards import main_keyboard
from bot.telegram_logger import TelegramLogsHandler

logger = logging.getLogger('bot.seller_handlers')

async def handle_seller_url(message: types.Message, state: FSMContext, bot):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Действие отменено", reply_markup=main_keyboard())
        return
    
    url = message.text
    if not url.startswith('https://www.ozon.ru/seller/'):
        await message.answer("❌ Неверная ссылка на продавца. Попробуйте еще раз.")
        return
    
    # Инициализируем систему логов
    telegram_logger = TelegramLogsHandler(bot, message.chat.id)
    
    try:
        await telegram_logger.add_log(f"⏳ Начинаем парсинг продавца: {url}")
        
        # Запускаем парсинг без callback
        result = await asyncio.to_thread(
            parse_seller_and_products, 
            url, 
            True,
        )
        
        # Отправляем информацию о продавце после получения результата
        if result and result.get('seller'):
            seller_info = result['seller_info']
            await telegram_logger.send_result_message(seller_info)
        
        if result and result.get('excel_path'):
            await telegram_logger.add_log("✅ Парсинг завершен! Отправляю файл...")
            
            # Отправляем файл
            with open(result['excel_path'], 'rb') as file:
                await message.answer_document(
                    types.BufferedInputFile(
                        file.read(),
                        filename=os.path.basename(result['excel_path'])
                    )
                )
            
            # Удаляем файл через 10 секунд
            async def delete_file():
                await asyncio.sleep(10)
                try:
                    os.remove(result['excel_path'])
                    logger.info(f"Файл {result['excel_path']} удален")
                except Exception as e:
                    logger.error(f"Ошибка удаления файла: {str(e)}")
            asyncio.create_task(delete_file())
            
            await telegram_logger.final_message("✅ Готово! Файл отправлен.")
        else:
            error_msg = result.get('error', 'Неизвестная ошибка')
            await telegram_logger.add_log(f"❌ Ошибка: {error_msg}")
            await telegram_logger.final_message(f"❌ Парсинг завершен с ошибкой: {error_msg}")
            
        # Показываем меню после завершения
        await message.answer("Выберите следующее действие:", reply_markup=main_keyboard())
            
    except Exception as e:
        logger.error(f"Критическая ошибка: {str(e)}")
        await telegram_logger.add_log(f"💥 Критическая ошибка: {str(e)}")
        await telegram_logger.final_message(f"💥 Произошла критическая ошибка: {str(e)}")
        await message.answer("❌ Произошла ошибка при обработке", reply_markup=main_keyboard())
    finally:
        await telegram_logger.stop()
        await state.clear()
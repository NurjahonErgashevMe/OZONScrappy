import logging
import asyncio
import os
import queue
from aiogram import types
from aiogram.fsm.context import FSMContext
from bot.keyboards import main_keyboard
from bot.telegram_logger import TelegramLogsHandler
from parse_inn import run_inn_parser_from_list
from parse_products_inn import run_product_inn_parser_from_list

logger = logging.getLogger('bot.inn_handlers')

async def handle_inn_urls(message: types.Message, state: FSMContext, bot, mode='sellers'):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Действие отменено", reply_markup=main_keyboard())
        return
    
    urls = [url.strip() for url in message.text.split('\n') if url.strip()]
    
    # Инициализируем систему логов
    telegram_logger = TelegramLogsHandler(bot, message.chat.id)
    
    try:
        # Отправляем начальное сообщение
        if mode == 'sellers':
            await telegram_logger.add_log(f"🆔 Начинаем парсинг ИНН для {len(urls)} продавцов")
        else:
            await telegram_logger.add_log(f"📦 Начинаем парсинг ИНН для {len(urls)} товаров")
        
        # Для парсинга товаров: будем отправлять результаты по каждому товару
        results = []
        
        if mode == 'sellers':
            result_message, _, filepath = await asyncio.to_thread(
                run_inn_parser_from_list, 
                urls
            )
        else:  # mode == 'products'
            # Запускаем парсинг и собираем результаты
            result_message, _, filepath, results = await asyncio.to_thread(
                run_product_inn_parser_from_list, 
                urls
            )
            
            # Отправляем результаты по каждому товару
            for i, result in enumerate(results, 1):
                seller_name = result.get('seller_name', 'Не найдено')
                company_name = result.get('company_name', 'Не найдено')
                inn = result.get('inn', 'Не найдено')
                product_url = result.get('product_url', '')
                
                # Формируем сообщение
                result_msg = (
                    f"✓ Товар {i} обработан:\n"
                    f"Продавец: {seller_name}\n"
                    f"Компания: {company_name}\n"
                    f"ИНН: {inn}\n"
                    f"Ссылка: {product_url}"
                )
                
                # Отправляем через логгер (будет очищено от HTML)
                await telegram_logger.send_result_message(result_msg)
        
        # Даем время на обработку оставшихся логов
        await asyncio.sleep(1)
        await telegram_logger.add_log(result_message)
        
        if filepath and os.path.exists(filepath):
            # Отправляем файл
            with open(filepath, 'rb') as file:
                await message.answer_document(
                    types.BufferedInputFile(
                        file.read(),
                        filename=os.path.basename(filepath)
                    )
                )
            
            # Удаляем файл через 10 секунд
            async def delete_file():
                await asyncio.sleep(10)
                try:
                    os.remove(filepath)
                    logger.info(f"Файл {filepath} удален")
                except Exception as e:
                    logger.error(f"Ошибка удаления файла: {str(e)}")
            asyncio.create_task(delete_file())
            
            await telegram_logger.final_message("✅ Успешно завершено! Файл отправлен.")
        else:
            await telegram_logger.final_message(result_message)
            
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
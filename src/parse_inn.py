import logging
import os
import time
import queue
from datetime import datetime
from src.parser.inn_parser import INNParser
from src.parser.excel_writer import ExcelWriter

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

def run_inn_parser_from_list(urls, log_queue=None):
    """Запуск парсера ИНН с передачей логов через очередь"""
    parser = None
    try:
        if log_queue:
            log_queue.put(f"🔄 Начинаем парсинг ИНН для {len(urls)} продавцов")
        
        # Создаем парсер
        parser = INNParser(headless=True)
        
        # Парсим URL
        parser.parse_url_list(urls)
        
        # Сохраняем результаты
        filepath = parser.save_to_excel()
        
        if filepath:
            if log_queue:
                log_queue.put(f"✅ Результаты сохранены в файл: {os.path.basename(filepath)}")
            return f"✅ Парсинг завершен! Результаты сохранены в:\n{os.path.basename(filepath)}", "", filepath
        return "❌ Ошибка при сохранении результатов", "", None
    except Exception as e:
        error_msg = f"❌ Ошибка при парсинге: {str(e)}"
        if log_queue:
            log_queue.put(error_msg)
        return error_msg, error_msg, None
    finally:
        if parser:
            parser.close()
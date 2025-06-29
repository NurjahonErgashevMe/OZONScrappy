import logging
import os
import time
from parser.product_inn_parser import ProductINNParser
from parser.excel_writer import ExcelWriter

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

def run_product_inn_parser_from_list(urls):
    """Запуск парсера ИНН для товаров с возвратом результатов"""
    parser = None
    results = []  # Будем собирать результаты
    
    try:
        parser = ProductINNParser(headless=True)
        # Парсим URL
        parser.parse_url_list(urls)
        results = parser.results  # Сохраняем результаты
        
        # Сохраняем результаты в Excel
        filepath = parser.save_to_excel()
        
        if filepath:
            return f"✅ Парсинг завершен! Результаты сохранены в файле: {os.path.basename(filepath)}", "", filepath, results
        return "❌ Ошибка при сохранении результатов", "", None, results
    except Exception as e:
        error_msg = f"❌ Ошибка при парсинге: {str(e)}"
        return error_msg, error_msg, None, results
    finally:
        if parser:
            parser.close()
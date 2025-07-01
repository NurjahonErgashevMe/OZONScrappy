import logging
import asyncio
import os
from datetime import datetime

from .driver_manager import DriverManager
from .link_collector import LinkCollector
from .seller_parser import SellerParser
from .excel_saver import ExcelSaver
from .file_manager import FileManager
from .url_utils import UrlUtils
from src.utils import load_config

logger = logging.getLogger('parser.category_inn_parser')

class CategoryParser:
    def __init__(self):
        self.config = load_config("config.txt")
        self.total_links = int(self.config.get("TOTAL_LINKS", "150"))
        self.workers_count = 3  # Количество воркеров для парсинга ИНН
        self.output_dir = "output"
        
        # Создаем папку output если её нет
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        # Инициализируем компоненты
        self.driver_manager = DriverManager()
        self.link_collector = LinkCollector(self.config, self.driver_manager)
        self.seller_parser = SellerParser(self.driver_manager)
        self.excel_saver = ExcelSaver(self.output_dir)
        self.file_manager = FileManager(self.output_dir)
        self.url_utils = UrlUtils()

    def parse_category(self, category_url):
        """Основной метод парсинга категории"""
        logger.info(f"Начинаем полный парсинг категории: {category_url}")
        
        try:
            # Валидация URL
            is_valid, validation_message = self.url_utils.validate_ozon_url(category_url)
            if not is_valid:
                logger.error(f"Некорректный URL: {validation_message}")
                return {}
            
            # Нормализация URL
            normalized_url = self.url_utils.normalize_url(category_url)
            if normalized_url:
                category_url = normalized_url
            
            # Этап 1: Сбор ссылок на товары
            logger.info("=== ЭТАП 1: Сбор ссылок на товары ===")
            product_links = self.link_collector.collect_product_links(category_url)
            
            if not product_links:
                logger.error("Не удалось собрать ссылки на товары")
                return {}
            
            logger.info(f"Собрано {len(product_links)} ссылок на товары")
            
            # Этап 2: Парсинг ИНН продавцов
            logger.info("=== ЭТАП 2: Парсинг ИНН продавцов ===")
            sellers_data = self.seller_parser.parse_sellers_from_links(product_links, self.workers_count)
            
            if sellers_data:
                category_name = self.url_utils.get_category_name(category_url)
                
                # Этап 3: Создание Excel файла
                logger.info("=== ЭТАП 3: Создание Excel файла ===")
                excel_filepath = self.excel_saver.save_to_excel(sellers_data, category_name)
                
                # Этап 4: Создание TXT файла с ИНН
                logger.info("=== ЭТАП 4: Создание файла с ИНН ===")
                txt_filepath = self.file_manager.save_inn_to_txt(sellers_data, category_name)
                
                # Сохраняем пути к файлам для последующей отправки
                sellers_data['_files'] = {
                    'excel': excel_filepath,
                    'txt': txt_filepath,
                    'category_name': category_name
                }
            
            return sellers_data
            
        except Exception as e:
            logger.error(f"Критическая ошибка при парсинге категории: {str(e)}")
            return {}

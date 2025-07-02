import logging
import os

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
        self.output_dir = "output"
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        self.driver_manager = DriverManager()
        # Исправлено: передаем только config и driver_manager
        self.link_collector = LinkCollector(
            self.config, 
            self.driver_manager
        )
        self.seller_parser = SellerParser(self.driver_manager)
        self.excel_saver = ExcelSaver(self.output_dir)
        self.file_manager = FileManager(self.output_dir)
        self.url_utils = UrlUtils()

    def parse_category(self, category_url):
        logger.info(f"Начинаем полный парсинг категории: {category_url}")
        
        try:
            is_valid, validation_message = self.url_utils.validate_ozon_url(category_url)
            if not is_valid:
                logger.error(f"Некорректный URL: {validation_message}")
                return {}
            
            normalized_url = self.url_utils.normalize_url(category_url)
            if normalized_url:
                category_url = normalized_url
            
            logger.info("=== ЭТАП 1: Сбор ссылок и парсинг продавцов ===")
            sellers_data = self.link_collector.collect_product_links(
                category_url,
                self.seller_parser  # Передаем парсер как аргумент
            )
            
            if not sellers_data:
                logger.error("Не удалось собрать данные продавцов")
                return {}
            
            logger.info(f"Собраны данные от {len(sellers_data)} продавцов")
            
            if sellers_data:
                category_name = self.url_utils.get_category_name(category_url)
                
                logger.info("=== ЭТАП 2: Создание Excel файла ===")
                excel_filepath = self.excel_saver.save_to_excel(sellers_data, category_name)
                
                logger.info("=== ЭТАП 3: Создание файла с ИНН ===")
                txt_filepath = self.file_manager.save_inn_to_txt(sellers_data, category_name)
                
                sellers_data['_files'] = {
                    'excel': excel_filepath,
                    'txt': txt_filepath,
                    'category_name': category_name
                }
            
            return sellers_data
            
        except Exception as e:
            logger.error(f"Критическая ошибка при парсинге категории: {str(e)}")
            return {}
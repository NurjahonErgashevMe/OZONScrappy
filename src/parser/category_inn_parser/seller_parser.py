import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.parser.seller_info_parser import SellerInfoParser

logger = logging.getLogger('parser.category_inn_parser.seller_parser')

class SellerParser:
    def __init__(self, driver_manager):
        self.driver_manager = driver_manager
        self.seller_info_parser = SellerInfoParser()

    def parse_single_seller(self, driver, seller_name, product_link):
        try:
            parsed_name = self.seller_info_parser.get_seller_name(driver)
            seller_info = self.seller_info_parser.get_seller_details(driver)
            product_title = self._get_product_title(driver)
            
            return {
                'seller_name': seller_info.get('seller_name', 'Не найдено'),
                'company_name': seller_info.get('company_name', seller_name),
                'inn': seller_info.get('inn', 'Не найдено'),
                'products_count': 1,
                'sample_products': [{
                    'title': product_title,
                    'url': product_link,
                    'seller_link': seller_info.get('seller_link', 'Не найдена ссылка на продавца')
                }],
                'filter_name': seller_name,
                'parsed_company_name': seller_info.get('company_name', 'Не найдено')
            }
        except Exception as e:
            logger.error(f"Ошибка парсинга: {str(e)}")
            return {
                'seller_name': seller_name,
                'company_name': seller_name,
                'inn': 'Ошибка парсинга',
                'products_count': 1,
                'sample_products': [{
                    'title': 'Ошибка получения данных',
                    'url': product_link
                }],
                'filter_name': seller_name,
                'parsed_company_name': 'Ошибка парсинга'
            }

    def _get_product_title(self, driver):
        try:
            title_element = WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, 'h1'))
            )
            return title_element.text[:100]
        except:
            return "Название не найдено"
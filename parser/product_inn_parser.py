# pproduct_inn_parser.py
import logging
import os
import time
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from parser.ozon_parser import OzonSellerParser
from parser.excel_writer import ExcelWriter

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

class ProductINNParser:
    def __init__(self, headless=True):
        """Инициализация парсера ИНН для товаров"""
        self.seller_parser = OzonSellerParser(headless=headless)
        self.driver = self.seller_parser.driver
        self.excel_writer = ExcelWriter()
        self.results = []
        
    def load_product_urls(self, file_path="products.txt"):
        """Загрузка ссылок на товары из файла"""
        try:
            if not os.path.exists(file_path):
                logger.error(f"Файл {file_path} не найден!")
                return []
            
            with open(file_path, 'r', encoding='utf-8') as file:
                urls = [line.strip() for line in file if line.strip() and not line.strip().startswith('#')]
            
            logger.info(f"Загружено {len(urls)} ссылок на товары")
            return urls
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке файла {file_path}: {str(e)}")
            return []
    
    def parse_url_list(self, urls):
        """Парсинг списка URL товаров"""
        self.results = []  # очищаем предыдущие результаты
        
        if not urls:
            logger.error("Нет ссылок для парсинга!")
            return False
        
        logger.info(f"Начинаем парсинг {len(urls)} товаров")
        
        for i, product_url in enumerate(urls, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"Парсинг товара {i}/{len(urls)}: {product_url}")
            logger.info(f"{'='*60}")
            
            try:
                product_data = self.parse_single_product(product_url)
                
                # Добавляем результат в список (только нужные поля)
                result = {
                    'seller_name': product_data.get('seller_name', 'Не найдено'),
                    'company_name': product_data.get('company_name', 'Не найдено'),
                    'inn': product_data.get('inn', 'Не найдено'),
                    'product_url': product_url
                }
                
                self.results.append(result)
                logger.info(f"✓ Товар {i} обработан:")
                logger.info(f"  Продавец: {result['seller_name']}")
                logger.info(f"  Компания: {result['company_name']}")
                logger.info(f"  ИНН: {result['inn']}")
                
                # Пауза между товарами
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"✗ Ошибка при парсинге товара {i}: {str(e)}")
                
                # Добавляем результат с ошибкой
                error_result = {
                    'seller_name': 'Ошибка',
                    'company_name': 'Ошибка',
                    'inn': 'Ошибка',
                    'product_url': product_url
                }
                self.results.append(error_result)
                
                # Восстановление драйвера при ошибке
                try:
                    self.driver.get("about:blank")
                    time.sleep(1)
                except:
                    logger.warning("Проблемы с драйвером, продолжаем...")
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Парсинг завершен! Обработано {len(self.results)} товаров")
        logger.info(f"{'='*60}")
        
        return True
    
    def parse_all_products(self):
        """Парсинг всех товаров из файла products.txt"""
        product_urls = self.load_product_urls()
        
        if not product_urls:
            logger.error("Нет ссылок для парсинга!")
            return False
        
        logger.info(f"Начинаем парсинг {len(product_urls)} товаров")
        
        for i, product_url in enumerate(product_urls, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"Парсинг товара {i}/{len(product_urls)}: {product_url}")
            logger.info(f"{'='*60}")
            
            try:
                product_data = self.parse_single_product(product_url)
                
                # Добавляем результат в список (только нужные поля)
                result = {
                    'seller_name': product_data.get('seller_name', 'Не найдено'),
                    'company_name': product_data.get('company_name', 'Не найдено'),
                    'inn': product_data.get('inn', 'Не найдено'),
                    'product_url': product_url
                }
                
                self.results.append(result)
                logger.info(f"✓ Товар {i} обработан:")
                logger.info(f"  Продавец: {result['seller_name']}")
                logger.info(f"  Компания: {result['company_name']}")
                logger.info(f"  ИНН: {result['inn']}")
                
                # Пауза между товарами
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"✗ Ошибка при парсинге товара {i}: {str(e)}")
                
                # Добавляем результат с ошибкой
                error_result = {
                    'seller_name': 'Ошибка',
                    'company_name': 'Ошибка',
                    'inn': 'Ошибка',
                    'product_url': product_url
                }
                self.results.append(error_result)
                
                # Восстановление драйвера при ошибке
                try:
                    self.driver.get("about:blank")
                    time.sleep(1)
                except:
                    logger.warning("Проблемы с драйвером, продолжаем...")
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Парсинг завершен! Обработано {len(self.results)} товаров")
        logger.info(f"{'='*60}")
        
        return True
    
    def parse_single_product(self, product_url):
        """Парсинг одного товара - только данные продавца"""
        product_data = {
            'seller_name': 'Не найдено',
            'company_name': 'Не найдено', 
            'inn': 'Не найдено'
        }
        
        try:
            # Переходим на страницу товара
            logger.info(f"Открываем страницу товара...")
            self.driver.get(product_url)
            time.sleep(3)
            
            # Получаем название продавца
            product_data['seller_name'] = self._get_seller_name_from_product()
            
            # Получаем данные продавца (ИНН и название компании)
            seller_data = self._extract_seller_data_from_product()
            product_data.update(seller_data)
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге товара: {str(e)}")
            
        return product_data
    
    def _get_seller_name_from_product(self):
        """Получение названия продавца со страницы товара"""
        try:
            # Различные селекторы для названия продавца
            seller_selectors = [
                '[data-widget="webProductSeller"] a',
                '[data-widget="webSeller"] a',
                'a[href*="/seller/"]',
                '[data-widget="webProductCardSeller"] a',
                '.product-seller a',
                '.seller-info a'
            ]
            
            for selector in seller_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text and text not in ['', 'Продавец', 'Seller']:
                            logger.info(f"Найден продавец: {text}")
                            return text
                except NoSuchElementException:
                    continue
            
            # Поиск через XPath
            try:
                xpath_selectors = [
                    "//span[contains(text(), 'Продавец')]/following-sibling::*/text()",
                    "//span[contains(text(), 'Продавец')]/parent::*/following-sibling::*//text()",
                    "//div[contains(@class, 'seller')]//a/text()"
                ]
                
                for xpath in xpath_selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, xpath)
                        for element in elements:
                            text = element.strip() if hasattr(element, 'strip') else str(element).strip()
                            if text and len(text) > 2:
                                logger.info(f"Найден продавец через XPath: {text}")
                                return text
                    except:
                        continue
            except:
                pass
            
            logger.warning("Название продавца не найдено")
            return 'Не найдено'
            
        except Exception as e:
            logger.warning(f"Ошибка при получении названия продавца: {str(e)}")
            return 'Не найдено'
    
    def _extract_seller_data_from_product(self):
        """Извлечение данных продавца (ИНН и название компании) со страницы товара"""
        seller_data = {
            'company_name': 'Не найдено',
            'inn': 'Не найдено'
        }
        
        try:
            # Используем существующий парсер деталей продавца
            seller_details = self.seller_parser.seller_details_parser.parse_seller_details(self.driver)
            
            if seller_details:
                # Обновляем данные продавца
                if 'company_name' in seller_details and seller_details['company_name']:
                    seller_data['company_name'] = seller_details['company_name']
                    
                if 'inn' in seller_details and seller_details['inn']:
                    seller_data['inn'] = seller_details['inn']
                
                logger.info(f"Данные продавца получены: ИНН={seller_data['inn']}, Компания={seller_data['company_name']}")
            else:
                logger.warning("Данные продавца не найдены в информации о товаре")
            
            return seller_data
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении данных продавца: {str(e)}")
            return seller_data
    
    def save_to_excel(self):
        """Сохранение результатов в Excel с использованием ExcelWriter"""
        try:
            if not self.results:
                logger.warning("Нет данных для сохранения")
                return None
            
            # Используем ExcelWriter для сохранения
            filepath = self.excel_writer.save_sellers_from_products(
                self.results,
                filename_prefix="sellers_from_products"
            )
            
            if filepath:
                logger.info(f"✓ Результаты сохранены: {filepath}")
                return filepath
            return None
            
        except Exception as e:
            logger.error(f"Ошибка сохранения: {str(e)}")
            return None
    
    def close(self):
        """Закрытие парсера"""
        try:
            if hasattr(self.seller_parser, 'driver') and self.seller_parser.driver:
                self.seller_parser.close()
        except Exception as e:
            logger.warning(f"Ошибка при закрытии драйвера: {str(e)}")

def main():
    """Основная функция"""
    logger.info("Запуск парсера продавцов из товаров Ozon")
    
    parser = None
    try:
        # Создаем парсер
        parser = ProductINNParser(headless=False)  # Изменить на True для работы в фоне
        
        # Парсим все товары
        success = parser.parse_all_products()
        
        if success:
            # Сохраняем результаты
            parser.save_to_excel()
            logger.info("✓ Парсинг завершен успешно!")
        else:
            logger.error("✗ Ошибка при парсинге товаров")
            
    except KeyboardInterrupt:
        logger.info("Парсинг прерван пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {str(e)}")
    finally:
        if parser:
            parser.close()

if __name__ == "__main__":
    main()
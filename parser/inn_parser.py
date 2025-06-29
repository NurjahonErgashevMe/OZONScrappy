# parser_inn.py
import logging
import os
import time
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from parser.ozon_parser import OzonSellerParser
from parser.product_parser import ProductParser
from parser.excel_writer import ExcelWriter

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

class INNParser:
    def __init__(self, headless=False):
        """Инициализация парсера ИНН"""
        self.seller_parser = OzonSellerParser(headless=headless)
        self.driver = self.seller_parser.driver
        self.product_parser = ProductParser()
        self.excel_writer = ExcelWriter()
        self.results = []
        
    def load_seller_urls(self, file_path="sellers.txt"):
        """Загрузка ссылок продавцов из файла"""
        try:
            if not os.path.exists(file_path):
                logger.error(f"Файл {file_path} не найден!")
                return []
            
            with open(file_path, 'r', encoding='utf-8') as file:
                urls = [line.strip() for line in file if line.strip()]
            
            logger.info(f"Загружено {len(urls)} ссылок продавцов")
            return urls
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке файла {file_path}: {str(e)}")
            return []
        
    def parse_url_list(self, urls):
        """Парсинг списка URL продавцов"""
        self.results = []  # очищаем предыдущие результаты
        
        if not urls:
            logger.error("Нет ссылок для парсинга!")
            return False
        
        logger.info(f"Начинаем парсинг {len(urls)} продавцов")
        
        for i, seller_url in enumerate(urls, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"Парсинг продавца {i}/{len(urls)}: {seller_url}")
            logger.info(f"{'='*60}")
            
            try:
                seller_data = self.parse_single_seller(seller_url)
                
                # Добавляем результат в список
                result = {
                    'seller_url': seller_url,
                    'seller_name': seller_data.get('seller_name', 'Не найдено'),
                    'company_name': seller_data.get('company_name', 'Не найдено'),
                    'inn': seller_data.get('inn', 'Не найдено')
                }
                
                self.results.append(result)
                logger.info(f"✓ Продавец {i} обработан. ИНН: {result['inn']}")
                
                # Небольшая пауза между продавцами
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"✗ Ошибка при парсинге продавца {i}: {str(e)}")
                
                # Добавляем результат с ошибкой
                error_result = {
                    'seller_url': seller_url,
                    'seller_name': 'Ошибка',
                    'company_name': 'Ошибка',
                    'inn': 'Ошибка'
                }
                self.results.append(error_result)
                
                # Пытаемся восстановить драйвер при критической ошибке
                try:
                    self.driver.get("about:blank")
                    time.sleep(1)
                except:
                    logger.warning("Проблемы с драйвером, продолжаем...")
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Парсинг завершен! Обработано {len(self.results)} продавцов")
        logger.info(f"{'='*60}")
        
        return True
    
    def parse_all_sellers(self):
        """Парсинг всех продавцов из файла sellers.txt"""
        seller_urls = self.load_seller_urls()
        
        if not seller_urls:
            logger.error("Нет ссылок для парсинга!")
            return False
        
        logger.info(f"Начинаем парсинг {len(seller_urls)} продавцов")
        
        for i, seller_url in enumerate(seller_urls, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"Парсинг продавца {i}/{len(seller_urls)}: {seller_url}")
            logger.info(f"{'='*60}")
            
            try:
                seller_data = self.parse_single_seller(seller_url)
                
                # Добавляем результат в список
                result = {
                    'seller_url': seller_url,
                    'seller_name': seller_data.get('seller_name', 'Не найдено'),
                    'company_name': seller_data.get('company_name', 'Не найдено'),
                    'inn': seller_data.get('inn', 'Не найдено')
                }
                
                self.results.append(result)
                logger.info(f"✓ Продавец {i} обработан. ИНН: {result['inn']}")
                
                # Небольшая пауза между продавцами
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"✗ Ошибка при парсинге продавца {i}: {str(e)}")
                
                # Добавляем результат с ошибкой
                error_result = {
                    'seller_url': seller_url,
                    'seller_name': 'Ошибка',
                    'company_name': 'Ошибка',
                    'inn': 'Ошибка'
                }
                self.results.append(error_result)
                
                # Пытаемся восстановить драйвер при критической ошибке
                try:
                    self.driver.get("about:blank")
                    time.sleep(1)
                except:
                    logger.warning("Проблемы с драйвером, продолжаем...")
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Парсинг завершен! Обработано {len(self.results)} продавцов")
        logger.info(f"{'='*60}")
        
        return True
    
    def parse_single_seller(self, seller_url):
        """Парсинг одного продавца"""
        seller_data = {
            'seller_name': 'Не найдено',
            'company_name': 'Не найдено', 
            'inn': 'Не найдено'
        }
        
        try:
            # Переходим на страницу продавца
            logger.info(f"Открываем страницу продавца: {seller_url}")
            self.driver.get(seller_url)
            time.sleep(3)
            
            # Получаем название продавца используя ProductParser
            seller_data['seller_name'] = self._get_seller_name()
            
            # Ищем товары продавца на его странице
            product_links = self._get_product_links()
            
            if not product_links:
                logger.warning("Товары продавца не найдены")
                return seller_data
            
            logger.info(f"Найдено {len(product_links)} товаров продавца")
            
            # Пробуем получить ИНН с каждого товара (максимум 10 попыток)
            max_attempts = min(len(product_links), 10)
            
            for i, product_url in enumerate(product_links[:max_attempts], 1):
                logger.info(f"Попытка {i}/{max_attempts}: переходим к товару {product_url}")
                
                try:
                    # Переходим к товару
                    self.driver.get(product_url)
                    time.sleep(2)
                    
                    # Если не получили название продавца на странице магазина,
                    # пытаемся получить его со страницы товара
                    if seller_data['seller_name'] == 'Не найдено':
                        result = {}
                        self.product_parser.parse_product_name(self.driver, result)
                        if result.get('product'):
                            seller_data['seller_name'] = result['product']
                    
                    # Пытаемся получить ИНН
                    inn_data = self._extract_inn_from_product_page()
                    
                    if inn_data and inn_data.get('inn') and inn_data['inn'] != 'Не найдено':
                        # Обновляем данные продавца
                        seller_data.update(inn_data)
                        logger.info(f"✓ ИНН найден: {inn_data['inn']}")
                        break
                    else:
                        logger.info(f"ИНН не найден на товаре {i}, пробуем следующий...")
                        
                except Exception as e:
                    logger.warning(f"Ошибка при обработке товара {i}: {str(e)}")
                    continue
            
            if seller_data['inn'] == 'Не найдено':
                logger.warning("ИНН не найден ни на одном товаре продавца")
            
        except Exception as e:
            logger.error(f"Критическая ошибка при парсинге продавца: {str(e)}")
            
        return seller_data
    
    def _get_seller_name(self):
        """Получение названия продавца со страницы магазина"""
        try:
            # Различные селекторы для названия продавца
            name_selectors = [
                'h1[data-widget="webShopTitle"]',
                '.shop-header h1',
                '[data-widget="webShopTitle"] h1',
                '.seller-name',
                'h1'
            ]
            
            for selector in name_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element and element.text.strip():
                        return element.text.strip()
                except NoSuchElementException:
                    continue
            
            # Попытка получить из заголовка страницы
            title = self.driver.title
            if title and '|' in title:
                return title.split('|')[0].strip()
            
            return 'Не найдено'
            
        except Exception as e:
            logger.warning(f"Ошибка при получении названия продавца: {str(e)}")
            return 'Не найдено'
    
    def _get_product_links(self):
        """Получение ссылок на товары продавца"""
        product_links = []
        
        try:
            # Ждем загрузки товаров
            time.sleep(2)
            
            # Различные селекторы для ссылок на товары
            product_selectors = [
                'a[href*="/product/"]',
                '.tile-hover-target',
                '[data-widget="searchResultsV2"] a[href*="/product/"]',
                '.product-card a',
                'a[href*="/detail/"]'
            ]
            
            for selector in product_selectors:
                try:
                    elements = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                    )
                    
                    for element in elements:
                        href = element.get_attribute('href')
                        if href and ('/product/' in href or '/detail/' in href):
                            # Очищаем URL от лишних параметров
                            clean_url = href.split('?')[0].split('#')[0]
                            if clean_url not in product_links:
                                product_links.append(clean_url)
                    
                    if product_links:
                        break
                        
                except TimeoutException:
                    continue
            
            # Удаляем дубликаты и ограничиваем количество
            unique_links = list(dict.fromkeys(product_links))[:20]  # максимум 20 товаров
            
            logger.info(f"Найдено {len(unique_links)} уникальных ссылок на товары")
            return unique_links
            
        except Exception as e:
            logger.error(f"Ошибка при поиске товаров: {str(e)}")
            return []
    
    def _extract_inn_from_product_page(self):
        """Извлечение ИНН со страницы товара"""
        inn_data = {
            'company_name': 'Не найдено',
            'inn': 'Не найдено'
        }
        
        try:
            # Используем существующий парсер деталей продавца
            seller_details = self.seller_parser.seller_details_parser.parse_seller_details(self.driver)
            
            if seller_details:
                # Оставляем только нужные поля
                if 'company_name' in seller_details:
                    inn_data['company_name'] = seller_details['company_name']
                if 'inn' in seller_details:
                    inn_data['inn'] = seller_details['inn']
                
                logger.info(f"Получены данные продавца: {inn_data}")
            
            return inn_data
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении ИНН: {str(e)}")
            return inn_data
    
    def save_to_excel(self):
        """Сохранение результатов в Excel используя ExcelWriter"""
        try:
            if not self.results:
                logger.warning("Нет данных для сохранения")
                return None
            
            # Преобразуем данные в формат для ExcelWriter
            products_data = []
            for result in self.results:
                product_data = {
                    'name': result['seller_name'],
                    'price_with_discount': result['company_name'],
                    'price_without_discount': result['inn'],
                    'discount_percent': '',
                    'rating': '',
                    'reviews_count': '',
                    'url': result['seller_url']
                }
                products_data.append(product_data)
            
            # Используем ExcelWriter для сохранения
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = self.excel_writer.save_sellers_to_excel(products_data, f"sellers_inn_{timestamp}")
            
            if filepath:
                logger.info(f"✓ Результаты сохранены в файл: {filepath}")
                logger.info(f"✓ Всего записей: {len(self.results)}")
                
                # Выводим статистику
                inn_found_count = len([r for r in self.results if r['inn'] not in ['Не найдено', 'Ошибка']])
                logger.info(f"✓ ИНН найден у: {inn_found_count} продавцов")
                
                return filepath
            else:
                logger.error("Ошибка при сохранении файла")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при сохранении в Excel: {str(e)}")
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
    logger.info("Запуск парсера ИНН продавцов Ozon")
    
    parser = None
    try:
        # Создаем парсер
        parser = INNParser(headless=False)  # Изменить на True для работы в фоне
        
        # Парсим всех продавцов
        success = parser.parse_all_sellers()
        
        if success:
            # Сохраняем результаты
            parser.save_to_excel()
            logger.info("✓ Парсинг завершен успешно!")
        else:
            logger.error("✗ Ошибка при парсинге продавцов")
            
    except KeyboardInterrupt:
        logger.info("Парсинг прерван пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {str(e)}")
    finally:
        if parser:
            parser.close()

if __name__ == "__main__":
    main()
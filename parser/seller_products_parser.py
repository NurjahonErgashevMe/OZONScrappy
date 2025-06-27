import logging
import time
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
from parser.product_extractor import ProductExtractor
from .excel_writer import ExcelWriter

class OzonProductParser:
    def __init__(self, headless=False):
        self.driver = None
        self.headless = headless
        self.products = []
        self.unique_product_urls = set()
        self.target_count = 150
        self.max_retry_attempts = 3
        self.logger = logging.getLogger('product_parser')
        self.extractor = ProductExtractor()
        
    def init_driver(self):
        """Инициализация драйвера"""
        options = uc.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        if self.headless:
            options.add_argument("--headless")
        
        try:
            # Способ 1: Указываем путь к вашему ChromeDriver
            self.driver = uc.Chrome(
                driver_executable_path=r"C:\chromedriver-win64\chromedriver.exe",
                options=options, 
                headless=self.headless
            )
        except Exception as e:
            self.logger.error(f"Ошибка с указанным путем к ChromeDriver: {e}")
            try:
                # Способ 2: Автоматическое управление версией
                self.driver = uc.Chrome(
                    options=options, 
                    headless=self.headless,
                    version_main=137  # Указываем версию Chrome
                )
            except Exception as e2:
                self.logger.error(f"Ошибка с автоматическим управлением версией: {e2}")
                try:
                    # Способ 3: Без указания версии (последняя попытка)
                    self.driver = uc.Chrome(options=options, headless=self.headless)
                except Exception as e3:
                    self.logger.error(f"Все попытки инициализации драйвера не удались: {e3}")
                    raise e3
                    
        self.logger.info("Браузер инициализирован для парсинга товаров")

    def load_seller_page(self, seller_url):
        """Загрузка страницы продавца"""
        try:
            self.logger.info(f"Загрузка страницы продавца: {seller_url}")
            self.driver.get(seller_url)
            
            # Ожидаем появления виджета товаров
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[id="contentScrollPaginator"]'))
            )
            
            self.logger.info("Страница продавца загружена, товары найдены")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки страницы продавца: {str(e)}")
            return False

    def extract_products_from_page(self):
        """Извлечение товаров с текущей страницы"""
        try:
            # Находим все карточки товаров
            product_cards = self.driver.find_elements(By.CSS_SELECTOR, '.tile-root')
            new_products_count = 0
            
            for card in product_cards:
                try:
                    product_data = self.extractor.extract_product_data(card)
                    if product_data and product_data['url'] not in self.unique_product_urls:
                        self.products.append(product_data)
                        self.unique_product_urls.add(product_data['url'])
                        new_products_count += 1
                        
                except Exception as e:
                    self.logger.debug(f"Ошибка извлечения данных товара: {str(e)}")
                    continue
                    
            return new_products_count
            
        except Exception as e:
            self.logger.error(f"Ошибка извлечения товаров: {str(e)}")
            return 0

    def scroll_down_and_wait(self):
        """Плавный скролл вниз и ожидание новых товаров"""
        try:
            # Получаем текущую высоту страницы
            current_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # Плавный скролл
            for i in range(0, current_height, 300):
                self.driver.execute_script(f"window.scrollTo(0, {i});")
                time.sleep(0.05)
            
            # Скролл до самого низа
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            self.logger.info("Скролл вниз выполнен, ожидаем появление новых товаров...")
            
            # Ждем загрузки новых товаров
            time.sleep(3)
            
            # Проверяем, изменилась ли высота страницы
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            return new_height > current_height
            
        except Exception as e:
            self.logger.error(f"Ошибка при скролле: {str(e)}")
            return False

    def check_for_new_products(self):
        """Проверка появления новых товаров после скролла"""
        try:
            # Ждем несколько секунд для загрузки
            time.sleep(2)
            
            # Проверяем наличие новых карточек товаров
            product_cards = self.driver.find_elements(By.CSS_SELECTOR, '.tile-root')
            return len(product_cards) > len(self.unique_product_urls)
            
        except Exception as e:
            self.logger.error(f"Ошибка проверки новых товаров: {str(e)}")
            return False

    def get_seller_name(self):
        """Извлечение названия магазина"""
        try:
            # Пытаемся найти название в различных возможных селекторах
            selectors = [
                'h1',
                '[data-widget="webSellerInfo"] h1',
                '.seller-info h1',
                '.seller-name',
                'title'
            ]
            
            for selector in selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    text = element.text.strip()
                    if text and not text.lower().startswith('ozon'):
                        return text
                except:
                    continue
            
            # Если ничего не найдено, извлекаем из URL
            url = self.driver.current_url
            if '/seller/' in url:
                seller_part = url.split('/seller/')[1].split('/')[0]
                return seller_part.replace('-', ' ').title()
            
            return "Неизвестный_магазин"
            
        except Exception as e:
            self.logger.error(f"Ошибка получения названия магазина: {str(e)}")
            return "Неизвестный_магазин"

    def parse_products(self, seller_url):
        """Основной метод парсинга товаров"""
        try:
            self.init_driver()
            
            if not self.load_seller_page(seller_url):
                return False
            
            # Получаем название магазина
            seller_name = self.get_seller_name()
            self.logger.info(f"Парсим товары магазина: {seller_name}")
            
            # Первоначальное извлечение товаров
            initial_count = self.extract_products_from_page()
            self.logger.info(f"Спарсили {len(self.products)}/{self.target_count} товаров")
            
            retry_count = 0
            
            # Основной цикл парсинга
            while len(self.products) < self.target_count and retry_count < self.max_retry_attempts:
                self.logger.info("Скролим вниз, ждем появление новых товаров...")
                
                # Скролл и ожидание
                scroll_success = self.scroll_down_and_wait()
                
                if scroll_success:
                    # Извлекаем новые товары
                    new_products = self.extract_products_from_page()
                    
                    if new_products > 0:
                        self.logger.info(f"Новые товары появились! Спарсили {len(self.products)}/{self.target_count} товаров")
                        retry_count = 0  # Сбрасываем счетчик попыток
                    else:
                        retry_count += 1
                        self.logger.warning(f"Новые товары не найдены. Попытка {retry_count}/{self.max_retry_attempts}")
                else:
                    retry_count += 1
                    self.logger.warning(f"Скролл не привел к изменениям. Попытка {retry_count}/{self.max_retry_attempts}")
            
            # Финальная обработка
            final_count = len(self.products)
            
            if retry_count >= self.max_retry_attempts:
                self.logger.info(f"Товары закончились. Все 3 попытки загрузки новых товаров не увенчались успехом.")
            
            if final_count == 0:
                self.logger.error("Не удалось спарсить ни одного товара")
                return False
            
            self.logger.info(f"Парсинг завершен. Итого товаров: {final_count}")
            
            # Сохраняем в Excel
            excel_writer = ExcelWriter()
            filename = excel_writer.save_to_excel(self.products, seller_name)
            
            if filename:
                self.logger.info(f"Данные сохранены в файл: {filename}")
                return True
            else:
                self.logger.error("Ошибка сохранения в Excel")
                return False
                
        except Exception as e:
            self.logger.error(f"Критическая ошибка парсинга товаров: {str(e)}")
            return False
            
        finally:
            if self.driver:
                self.driver.quit()
                self.logger.info("Браузер закрыт")

    def get_products(self):
        """Получить список спарсенных товаров"""
        return self.products
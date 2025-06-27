# parser/ozon_parser.py
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from .utils import wait_for_element
from .product_parser import ProductParser
from .seller_info_parser import SellerInfoParser
from .seller_details_parser import SellerDetailsParser
from .modal_parser import ModalParser
from undetected_chromedriver import Chrome, ChromeOptions
import logging
import os
import time

logger = logging.getLogger(__name__)

class OzonSellerParser:
    def __init__(self, headless=False, driver_path=None):
        self.options = ChromeOptions()
        
        # Настройки для обхода детекта
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_argument("--window-size=1200,800")
        self.options.add_argument("--log-level=3")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--no-sandbox")
        
        # Используем явный путь к драйверу
        self.driver_path = driver_path or self._find_default_driver()
        
        # Инициализация драйвера
        self.driver = Chrome(
            options=self.options,
            driver_executable_path=self.driver_path,
            headless=headless,
            use_subprocess=True
        )
        
        # Инициализация парсеров
        self.product_parser = ProductParser()
        self.seller_info_parser = SellerInfoParser()
        self.seller_details_parser = SellerDetailsParser()
        self.modal_parser = ModalParser()

    def _find_default_driver(self):
        """Поиск драйвера по умолчанию"""
        paths = [
            r"C:\chromedriver-win64\chromedriver.exe",
            r"C:\Program Files\chromedriver\chromedriver.exe",
            "/usr/local/bin/chromedriver"
        ]
        for path in paths:
            if os.path.exists(path):
                return path
        return None

    def parse_page(self, driver, url):
        """Парсинг страницы товара"""
        result = {
            'product': 'Not Found', 
            'seller': 'Not Found', 
            'status': 'success',
            'seller_details': {}
        }
        
        try:
            driver.get(url)
            
            # Проверка наличия товара
            if self._check_out_of_stock(driver, result):
                return result
            
            # Поиск названия товара
            self.product_parser.parse_product_name(driver, result)
            
            # Скролл к секции с информацией о продавце
            driver.execute_script("window.scrollTo(0, 800);")
            time.sleep(1)
            
            # Поиск и парсинг основной информации о продавце
            self.seller_info_parser.parse_seller_info(driver, result)
            
            # Парсинг дополнительной информации (ИНН и т.д.)
            seller_details = self.seller_details_parser.parse_seller_details(driver)
            if seller_details:
                result['seller_details'] = seller_details
                
        except Exception as e:
            result['status'] = "error"
            result['seller'] = f"Ошибка: {str(e)}"
            logger.error(f"Ошибка при парсинге страницы: {str(e)}")
            
        return result

    def _check_out_of_stock(self, driver, result):
        """Проверка наличия товара"""
        try:
            WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.XPATH, '//div[@data-widget="webOutOfStock"]'))
            )
            result['status'] = "out_of_stock"
            
            # Парсинг для отсутствующего товара
            try:
                product_element = driver.find_element(
                    By.XPATH, 
                    '//div[@data-widget="webOutOfStock"]//p[contains(@class, "yl6_27")]'
                )
                result['product'] = product_element.text.strip()
            except:
                try:
                    product_element = driver.find_element(
                        By.XPATH, 
                        '//div[@data-widget="webOutOfStock"]//p[contains(text(), "Intel") or contains(text(), "Системный")]'
                    )
                    result['product'] = product_element.text.strip()
                except:
                    result['product'] = "Название не найдено"
            
            try:
                seller_element = driver.find_element(
                    By.XPATH, 
                    '//div[@data-widget="webOutOfStock"]//a[contains(@href, "/seller/")]'
                )
                result['seller'] = seller_element.text.strip()
            except:
                result['seller'] = "Продавец не найден"
                
            return True
        except TimeoutException:
            return False

    def parse_seller(self, url):
        """Парсинг информации о продавце с переходом на первый товар"""
        try:
            logger.info(f"Открываем URL продавца: {url}")
            self.driver.get(url)
            time.sleep(3)
            
            # Парсинг основной информации из модального окна
            self.modal_parser.open_shop_modal(self.driver)
            seller_data = self.modal_parser.parse_modal_data(self.driver)
            self.modal_parser.close_modal(self.driver)
            
            # Переходим на первый товар для парсинга доп. информации
            first_product_link = self._get_first_product_link()
            if first_product_link:
                logger.info(f"Переходим на первый товар: {first_product_link}")
                self.driver.get(first_product_link)
                time.sleep(3)
                
                # Парсинг дополнительной информации о продавце
                additional_details = self.seller_details_parser.parse_seller_details(self.driver)
                seller_data.update(additional_details)
            
            return seller_data
        except Exception as e:
            logger.error(f"Ошибка при парсинге: {str(e)}")
            self.driver.save_screenshot("error_screenshot.png")
            logger.error("Скриншот ошибки сохранён как error_screenshot.png")
            raise
        finally:
            self.driver.quit()

    def _get_first_product_link(self):
        """Получение ссылки на первый товар продавца"""
        try:
            # Ищем первую ссылку на товар
            product_links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/product/"]')
            if product_links:
                first_link = product_links[0].get_attribute('href')
                return first_link
            return None
        except Exception as e:
            logger.error(f"Ошибка при поиске ссылки на товар: {str(e)}")
            return None

    def close(self):
        """Закрытие драйвера"""
        if hasattr(self, 'driver') and self.driver:
            self.driver.quit()
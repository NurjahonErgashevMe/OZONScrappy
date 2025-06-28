# parser/ozon_parser.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import selenium_stealth
from .utils import wait_for_element
from .product_parser import ProductParser
from .seller_info_parser import SellerInfoParser
from .seller_details_parser import SellerDetailsParser
from .modal_parser import ModalParser
import logging
import os
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

class OzonSellerParser:
    def __init__(self, headless=True, driver_path=None):
        """Инициализация парсера с stealth режимом"""
        self.options = Options()
        
        # Базовые настройки Chrome
        if headless:
            self.options.add_argument("--headless")
            
        self.options.add_argument("--window-size=1920,1080")
        # self.options.add_argument("--headless")
        self.options.add_argument("--start-maximized")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--disable-features=VizDisplayCompositor")
        
        # Дополнительные настройки для обхода детекции
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option('useAutomationExtension', False)
        
        # Настройки User-Agent
        self.options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Поиск пути к драйверу
        self.driver_path = driver_path or self._find_default_driver()
        
        # Создание сервиса
        if self.driver_path:
            service = Service(self.driver_path)
            self.driver = webdriver.Chrome(service=service, options=self.options)
        else:
            # Попытка использовать системный ChromeDriver
            self.driver = webdriver.Chrome(options=self.options)
        
        # Применение stealth настроек
        selenium_stealth.stealth(
            self.driver,
            languages=["ru-RU", "ru"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )
        
        # Дополнительные скрипты для маскировки
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
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
            r"C:\chromedriver\chromedriver.exe",
            "/usr/local/bin/chromedriver",
            "/usr/bin/chromedriver"
        ]
        for path in paths:
            if os.path.exists(path):
                logger.info(f"Найден драйвер: {path}")
                return path
        logger.warning("ChromeDriver не найден в стандартных путях")
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
            # Проверяем, что URL является строкой
            if not isinstance(url, str) or not url.strip():
                logger.error(f"Некорректный URL: {url}")
                result['status'] = "error"
                result['seller'] = f"Некорректный URL: {url}"
                return result
            
            logger.info(f"Парсинг страницы: {url}")
            driver.get(url)
            time.sleep(3)  # Дополнительная пауза для stealth
            
            # Проверка наличия товара
            if self._check_out_of_stock(driver, result):
                return result
            
            # Поиск названия товара
            self.product_parser.parse_product_name(driver, result)
            
            # Скролл к секции с информацией о продавце
            driver.execute_script("window.scrollTo(0, 800);")
            time.sleep(2)
            
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
            # Проверяем, что URL является строкой
            if not isinstance(url, str) or not url.strip():
                logger.error(f"Некорректный URL продавца: {url}")
                raise ValueError(f"URL должен быть непустой строкой, получен: {type(url)} - {url}")
            
            logger.info(f"Открываем URL продавца: {url}")
            self.driver.get(url)
            time.sleep(5)  # Увеличенная пауза для stealth
            
            # Имитируем человеческое поведение
            self._simulate_human_behavior()
            
            # Парсинг основной информации из модального окна
            self.modal_parser.open_shop_modal(self.driver)
            seller_data = self.modal_parser.parse_modal_data(self.driver)
            self.modal_parser.close_modal(self.driver)
            
            # Переходим на первый товар для парсинга доп. информации
            first_product_link = self._get_first_product_link()
            if first_product_link and isinstance(first_product_link, str) and first_product_link.strip():
                logger.info(f"Переходим на первый товар: {first_product_link}")
                self.driver.get(first_product_link)
                time.sleep(4)
                
                # Дополнительная имитация поведения
                self._simulate_human_behavior()
                
                # Парсинг дополнительной информации о продавце
                additional_details = self.seller_details_parser.parse_seller_details(self.driver)
                if additional_details:
                    seller_data.update(additional_details)
            else:
                logger.warning("Не удалось найти ссылку на первый товар или ссылка некорректна")
            
            return seller_data
        except Exception as e:
            logger.error(f"Ошибка при парсинге: {str(e)}")
            try:
                self.driver.save_screenshot("error_screenshot.png")
                logger.error("Скриншот ошибки сохранён как error_screenshot.png")
            except:
                logger.error("Не удалось сохранить скриншот")
            raise
        finally:
            self.close()

    def _simulate_human_behavior(self):
        """Имитация человеческого поведения для обхода детекции"""
        try:
            # Случайный скролл
            self.driver.execute_script("window.scrollTo(0, Math.floor(Math.random() * 500));")
            time.sleep(1)
            
            # Движение мыши (имитация через JavaScript)
            self.driver.execute_script("""
                var event = new MouseEvent('mousemove', {
                    'view': window,
                    'bubbles': true,
                    'cancelable': true,
                    'clientX': Math.random() * window.innerWidth,
                    'clientY': Math.random() * window.innerHeight
                });
                document.dispatchEvent(event);
            """)
            time.sleep(0.5)
            
        except Exception as e:
            logger.debug(f"Ошибка при имитации поведения: {str(e)}")

    def _get_first_product_link(self):
        """Получение ссылки на первый товар продавца"""
        try:
            # Ждем загрузки товаров
            time.sleep(3)
            
            # Ищем первую ссылку на товар
            product_links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/product/"]')
            if product_links:
                first_link = product_links[0].get_attribute('href')
                # Проверяем, что ссылка является строкой
                if isinstance(first_link, str) and first_link.strip():
                    return first_link
                else:
                    logger.warning(f"Найденная ссылка не является строкой: {type(first_link)} - {first_link}")
                    return None
            else:
                logger.warning("Не найдено ссылок на товары")
                return None
        except Exception as e:
            logger.error(f"Ошибка при поиске ссылки на товар: {str(e)}")
            return None

    def close(self):
        """Закрытие драйвера"""
        try:
            if hasattr(self, 'driver') and self.driver:
                self.driver.quit()
                logger.info("Драйвер успешно закрыт")
        except Exception as e:
            logger.warning(f"Ошибка при закрытии драйвера: {str(e)}")
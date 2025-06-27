from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from .utils import wait_for_element
from undetected_chromedriver import Chrome, ChromeOptions
import logging
import re
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

    def parse_seller(self, url):
        try:
            logger.info(f"Открываем URL: {url}")
            self.driver.get(url)
            
            # Добавляем задержку для полной загрузки страницы
            time.sleep(3)
            
            self._open_shop_modal()
            seller_data = self._parse_modal_data()
            logger.info(f"Данные успешно получены: {seller_data}")
            return seller_data
        except Exception as e:
            logger.error(f"Ошибка при парсинге: {str(e)}")
            # Делаем скриншот для диагностики
            self.driver.save_screenshot("error_screenshot.png")
            logger.error("Скриншот ошибки сохранён как error_screenshot.png")
            raise
        finally:
            self.driver.quit()

    def _open_shop_modal(self):
        # Ожидаем появления виджета sellerTransparency
        transparency_widget = wait_for_element(
            self.driver,
            (By.CSS_SELECTOR, 'div[data-widget="sellerTransparency"]'),
            timeout=20
        )
        
        # Ищем кнопку "Магазин" по точному тексту
        shop_button = transparency_widget.find_element(
            By.XPATH, 
            './/div[contains(@class, "b20-b") and .//div[text()="Магазин"]]'
        )
        
        # Используем JavaScript для клика, чтобы обойти проблему с перекрытием
        self.driver.execute_script("arguments[0].click();", shop_button)
        logger.info("Клик по кнопке 'Магазин' выполнен с помощью JavaScript")
        
        # Добавляем небольшую задержку для появления модального окна
        time.sleep(1)
        
        # Ожидаем появления модального окна
        wait_for_element(
            self.driver,
            (By.CSS_SELECTOR, 'div[data-widget="modalLayout"]'),
            timeout=15
        )

    def _parse_modal_data(self):
        data = {
            "is_premium": False,
            "orders_count": None,
            "working_since": None,
            "average_rating": None,
            "reviews_count": None
        }
        
        # Находим контейнер с данными
        container = wait_for_element(
            self.driver,
            (By.CSS_SELECTOR, 'div[data-widget="cellList"]')
        )
        
        # Извлекаем все строки с информацией
        rows = container.find_elements(By.CSS_SELECTOR, 'div.b320-a')
        
        for row in rows:
            try:
                # Пытаемся найти элемент с текстом
                label_elem = row.find_element(By.CSS_SELECTOR, '.b320-a9')
                label = label_elem.text.strip()
                
                # Проверка Premium статуса
                if "Premium" in label:
                    data["is_premium"] = True
                    continue
                
                # Извлекаем значение если есть
                value_elem = row.find_element(By.CSS_SELECTOR, '.b20-b0')
                value = value_elem.text.strip()
                
                # Обработка данных в зависимости от типа
                if "Заказов" in label:
                    data["orders_count"] = self._parse_number(value)
                elif "Работает" in label:
                    data["working_since"] = value
                elif "Средняя оценка" in label:
                    data["average_rating"] = self._parse_rating(value)
                elif "Количество отзывов" in label:
                    data["reviews_count"] = self._parse_number(value)
                    
            except Exception as e:
                logger.warning(f"Ошибка обработки строки: {str(e)}")
                continue  # Пропускаем строки без данных
        
        return data

    def _parse_number(self, value):
        """Преобразует строку с числами в целое число"""
        return int(re.sub(r"[^\d]", "", value)) if value else None

    def _parse_rating(self, value):
        """Извлекает числовое значение рейтинга"""
        match = re.search(r"[\d,]+", value)
        if match:
            return float(match.group().replace(",", "."))
        return None
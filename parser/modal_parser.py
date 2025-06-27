# parser/modal_parser.py
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from .utils import wait_for_element
import logging
import re
import time

logger = logging.getLogger(__name__)

class ModalParser:
    def open_shop_modal(self, driver):
        """Открытие модального окна магазина"""
        # Ожидаем появления виджета sellerTransparency
        transparency_widget = wait_for_element(
            driver,
            (By.CSS_SELECTOR, 'div[data-widget="sellerTransparency"]'),
            timeout=20
        )
        
        # Ищем кнопку "Магазин" по точному тексту
        shop_button = transparency_widget.find_element(
            By.XPATH, 
            './/div[contains(@class, "b20-b") and .//div[text()="Магазин"]]'
        )
        
        # Используем JavaScript для клика, чтобы обойти проблему с перекрытием
        driver.execute_script("arguments[0].click();", shop_button)
        logger.info("Клик по кнопке 'Магазин' выполнен с помощью JavaScript")
        
        # Добавляем небольшую задержку для появления модального окна
        time.sleep(1)
        
        # Ожидаем появления модального окна
        wait_for_element(
            driver,
            (By.CSS_SELECTOR, 'div[data-widget="modalLayout"]'),
            timeout=15
        )

    def parse_modal_data(self, driver):
        """Парсинг данных из модального окна"""
        data = {
            "is_premium": False,
            "orders_count": None,
            "working_since": None,
            "average_rating": None,
            "reviews_count": None
        }
        
        # Находим контейнер с данными
        container = wait_for_element(
            driver,
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

    def close_modal(self, driver):
        """Закрытие модального окна"""
        try:
            # Ищем кнопку закрытия модального окна
            close_button = driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Закрыть"]')
            close_button.click()
            time.sleep(1)
        except:
            # Если кнопка не найдена, кликаем по overlay для закрытия
            try:
                overlay = driver.find_element(By.CSS_SELECTOR, 'div[data-widget="modalLayout"]')
                driver.execute_script("arguments[0].click();", overlay)
                time.sleep(1)
            except:
                # Если ничего не получилось, нажимаем Escape
                driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                time.sleep(1)

    def _parse_number(self, value):
        """Преобразует строку с числами в целое число"""
        return int(re.sub(r"[^\d]", "", value)) if value else None

    def _parse_rating(self, value):
        """Извлекает числовое значение рейтинга"""
        match = re.search(r"[\d,]+", value)
        if match:
            return float(match.group().replace(",", "."))
        return None
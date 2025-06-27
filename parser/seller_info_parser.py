# parser/seller_info_parser.py
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import logging

logger = logging.getLogger(__name__)

class SellerInfoParser:
    def parse_seller_info(self, driver, result):
        """Парсинг основной информации о продавце"""
        try:
            seller_element = WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((
                    By.XPATH, 
                    '//div[@data-widget="webCurrentSeller"]//a[contains(@class, "j7n_27") and @title] | '
                    '//div[@data-widget="webCurrentSeller"]//a[@title]'
                ))
            )
            result['seller'] = seller_element.text.strip()
        except TimeoutException:
            seller_locators = [
                (By.XPATH, '//div[@data-widget="webCurrentSeller"]//a[@title]'),
                (By.CSS_SELECTOR, 'div[data-widget="webCurrentSeller"] a.j7n_27'),
                (By.XPATH, '//a[contains(@href, "/seller/")]')
            ]
            
            for locator in seller_locators:
                try:
                    element = WebDriverWait(driver, 2).until(
                        EC.visibility_of_element_located(locator)
                    )
                    result['seller'] = element.text.strip()
                    break
                except TimeoutException:
                    continue
            else:
                result['seller'] = "Продавец не найден"
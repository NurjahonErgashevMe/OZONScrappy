# parser/product_parser.py
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import logging

logger = logging.getLogger(__name__)

class ProductParser:
    def parse_product_name(self, driver, result):
        """Парсинг названия товара"""
        try:
            product_element = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((
                    By.XPATH, 
                    '//div[@data-widget="webProductHeading"]//h1 | '
                    '//div[@data-widget="webProductHeading"]//*[contains(@class, "m9p_27")] | '
                    '//h1[@data-widget="webProductHeading"]'
                ))
            )
            result['product'] = product_element.text.strip()
            
        except TimeoutException:
            try:
                product_container = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((
                        By.XPATH, 
                        '//div[contains(@class, "p9m_27")]'
                    ))
                )
                product_element = product_container.find_element(By.TAG_NAME, 'h1')
                result['product'] = product_element.text.strip()
                
            except:
                try:
                    product_js = driver.execute_script(
                        """
                        const widget = document.querySelector('div[data-widget="webProductHeading"]');
                        if (widget) {
                            const h1 = widget.querySelector('h1');
                            if (h1) return h1.innerText.trim();
                            return widget.innerText.trim();
                        }
                        
                        const classElement = document.querySelector('.m9p_27, .tsHeadline');
                        if (classElement) return classElement.innerText.trim();
                        
                        return document.title.split('|')[0].trim();
                        """
                    )
                    if product_js:
                        result['product'] = product_js
                    else:
                        result['product'] = "Название не найдено"
                except:
                    result['product'] = "Название не найдено"
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
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

    def parse_page(self, driver, url):
        result = {
            'product': 'Not Found', 
            'seller': 'Not Found', 
            'status': 'success',
            'seller_details': {}  # Добавляем поле для дополнительных данных
        }
        
        try:
            driver.get(url)
            
            # Проверка наличия товара
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
                    
                return result
            except TimeoutException:
                pass
            
            # Поиск названия товара
            self._parse_product_name(driver, result)
            
            # Скролл к секции с информацией о продавце
            driver.execute_script("window.scrollTo(0, 800);")
            time.sleep(1)
            
            # Поиск и парсинг основной информации о продавце
            self._parse_seller_info(driver, result)
            
            # Парсинг дополнительной информации (ИНН и т.д.)
            self._parse_seller_details(driver, result)
                
        except Exception as e:
            result['status'] = "error"
            result['seller'] = f"Ошибка: {str(e)}"
            logger.error(f"Ошибка при парсинге страницы: {str(e)}")
            
        return result

    def _parse_product_name(self, driver, result):
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

    def _parse_seller_info(self, driver, result):
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

    def _parse_seller_details(self, driver, result):
        """Парсинг дополнительной информации о продавце из тултипа"""
        try:
            # Ждем загрузки секции с продавцом
            seller_section = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-widget="webCurrentSeller"]'))
            )
            
            # Скроллим к секции с продавцом
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", seller_section)
            time.sleep(1)
            
            # Ищем кнопку с информацией о продавце (иконка "i")
            info_button = None
            button_selectors = [
                'div.ea20-a.k9j_27.n7j_27 button.ga20-a',
                'button.ga20-a[aria-label=""]',
                'div[data-widget="webCurrentSeller"] button[aria-label=""]'
            ]
            
            for selector in button_selectors:
                try:
                    info_button = seller_section.find_element(By.CSS_SELECTOR, selector)
                    if info_button:
                        break
                except NoSuchElementException:
                    continue
            
            if not info_button:
                logger.warning("Кнопка с информацией о продавце не найдена")
                return
            
            # Наводим курсор на кнопку для появления тултипа
            actions = ActionChains(driver)
            actions.move_to_element(info_button).perform()
            time.sleep(0.5)
            
            # Кликаем по кнопке для открытия тултипа
            driver.execute_script("arguments[0].click();", info_button)
            time.sleep(1)
            
            # Ждем появления тултипа
            try:
                tooltip = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.vue-portal-target'))
                )
                
                # Парсим содержимое тултипа
                self._extract_tooltip_data(tooltip, result)
                
            except TimeoutException:
                # Пробуем альтернативные селекторы для тултипа
                tooltip_selectors = [
                    '.ea20-a1.ea20-a5.ea20-b3',
                    'div[data-popper-placement]',
                    '.ea20-a2.ea20-b2'
                ]
                
                for selector in tooltip_selectors:
                    try:
                        tooltip = driver.find_element(By.CSS_SELECTOR, selector)
                        if tooltip.is_displayed():
                            self._extract_tooltip_data(tooltip, result)
                            break
                    except NoSuchElementException:
                        continue
                else:
                    logger.warning("Тултип с дополнительной информацией не найден")
                    
        except Exception as e:
            logger.error(f"Ошибка при парсинге дополнительной информации о продавце: {str(e)}")

    def _extract_tooltip_data(self, tooltip, result):
        """Извлечение данных из тултипа"""
        try:
            # Получаем все параграфы с информацией
            info_paragraphs = tooltip.find_elements(By.CSS_SELECTOR, 'p.jn8_27')
            
            seller_details = {}
            
            for paragraph in info_paragraphs:
                text = paragraph.text.strip()
                
                if not text:
                    continue
                
                # Определяем тип информации
                if self._is_company_name(text):
                    seller_details['company_name'] = text
                elif self._is_inn_or_registration(text):
                    seller_details['registration_number'] = text
                elif 'режим работы' in text.lower() or 'работ' in text.lower():
                    seller_details['working_hours'] = text
                elif self._is_address(text):
                    seller_details['address'] = text
                else:
                    # Добавляем прочую информацию
                    if 'other_info' not in seller_details:
                        seller_details['other_info'] = []
                    seller_details['other_info'].append(text)
            
            result['seller_details'] = seller_details
            logger.info(f"Дополнительная информация о продавце получена: {seller_details}")
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении данных из тултипа: {str(e)}")

    def _is_company_name(self, text):
        """Проверяет, является ли текст названием компании"""
        company_indicators = ['ИП', 'ООО', 'АО', 'ЗАО', 'ПАО', 'Ltd', 'LLC', 'Inc']
        return any(indicator in text for indicator in company_indicators)

    def _is_inn_or_registration(self, text):
        """Проверяет, является ли текст ИНН или регистрационным номером"""
        # Проверяем на наличие только цифр и определенную длину
        digits_only = ''.join(filter(str.isdigit, text))
        return len(digits_only) >= 10 and len(digits_only) <= 15 and len(text) == len(digits_only)

    def _is_address(self, text):
        """Проверяет, является ли текст адресом"""
        address_indicators = ['г.', 'город', 'ул.', 'улица', 'пр.', 'проспект', 'д.', 'дом']
        return any(indicator in text.lower() for indicator in address_indicators)

    def parse_seller(self, url):
        """Метод для совместимости с оригинальным кодом"""
        try:
            logger.info(f"Открываем URL: {url}")
            self.driver.get(url)
            
            # Добавляем задержку для полной загрузки страницы
            time.sleep(3)
            
            self._open_shop_modal()
            seller_data = self._parse_modal_data()
            
            # Закрываем модальное окно перед парсингом дополнительной информации
            self._close_modal()
            
            # Парсим дополнительную информацию о продавце
            seller_details = self._parse_seller_details_from_page()
            seller_data['seller_details'] = seller_details
            
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

    def _close_modal(self):
        """Закрытие модального окна"""
        try:
            # Ищем кнопку закрытия модального окна
            close_button = self.driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Закрыть"]')
            close_button.click()
            time.sleep(1)
        except:
            # Если кнопка не найдена, кликаем по overlay для закрытия
            try:
                overlay = self.driver.find_element(By.CSS_SELECTOR, 'div[data-widget="modalLayout"]')
                self.driver.execute_script("arguments[0].click();", overlay)
                time.sleep(1)
            except:
                # Если ничего не получилось, нажимаем Escape
                from selenium.webdriver.common.keys import Keys
                self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                time.sleep(1)

    def _parse_seller_details_from_page(self):
        """Парсинг дополнительной информации о продавце со страницы товара"""
        seller_details = {}
        
        try:
            # Переходим на первый товар продавца
            first_product_link = self._get_first_product_link()
            if not first_product_link:
                logger.warning("Не найден первый товар продавца")
                return seller_details
            
            logger.info(f"Переходим на первый товар: {first_product_link}")
            self.driver.get(first_product_link)
            time.sleep(3)
            
            # Скроллим к секции с информацией о продавце
            self.driver.execute_script("window.scrollTo(0, 800);")
            time.sleep(1)
            
            # Парсим дополнительную информацию
            seller_details = self._parse_seller_tooltip()
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге дополнительной информации: {str(e)}")
            
        return seller_details

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

    def _parse_seller_tooltip(self):
        """Парсинг тултипа с дополнительной информацией о продавце"""
        seller_details = {}
        
        try:
            # Ждем загрузки секции с продавцом
            seller_section = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-widget="webCurrentSeller"]'))
            )
            
            # Скроллим к секции с продавцом
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", seller_section)
            time.sleep(1)
            
            # Ищем кнопку с информацией о продавце (иконка "i")
            info_button = None
            button_selectors = [
                'div.ea20-a.k9j_27.n7j_27 button.ga20-a',
                'button.ga20-a[aria-label=""]',
                'div[data-widget="webCurrentSeller"] button[aria-label=""]'
            ]
            
            for selector in button_selectors:
                try:
                    info_button = seller_section.find_element(By.CSS_SELECTOR, selector)
                    if info_button:
                        break
                except NoSuchElementException:
                    continue
            
            if not info_button:
                logger.warning("Кнопка с информацией о продавце не найдена")
                return seller_details
            
            # Наводим курсор на кнопку для появления тултипа
            actions = ActionChains(self.driver)
            actions.move_to_element(info_button).perform()
            time.sleep(0.5)
            
            # Кликаем по кнопке для открытия тултипа
            self.driver.execute_script("arguments[0].click();", info_button)
            time.sleep(1)
            
            # Ждем появления тултипа
            try:
                tooltip = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.vue-portal-target'))
                )
                
                # Парсим содержимое тултипа
                seller_details = self._extract_tooltip_data(tooltip)
                
            except TimeoutException:
                # Пробуем альтернативные селекторы для тултипа
                tooltip_selectors = [
                    '.ea20-a1.ea20-a5.ea20-b3',
                    'div[data-popper-placement]',
                    '.ea20-a2.ea20-b2'
                ]
                
                for selector in tooltip_selectors:
                    try:
                        tooltip = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if tooltip.is_displayed():
                            seller_details = self._extract_tooltip_data(tooltip)
                            break
                    except NoSuchElementException:
                        continue
                else:
                    logger.warning("Тултип с дополнительной информацией не найден")
                    
        except Exception as e:
            logger.error(f"Ошибка при парсинге тултипа: {str(e)}")
            
        return seller_details

    def _extract_tooltip_data(self, tooltip):
        """Извлечение данных из тултипа"""
        seller_details = {}
        
        try:
            # Получаем все параграфы с информацией
            info_paragraphs = tooltip.find_elements(By.CSS_SELECTOR, 'p.jn8_27')
            
            for paragraph in info_paragraphs:
                text = paragraph.text.strip()
                
                if not text:
                    continue
                
                # Определяем тип информации
                if self._is_company_name(text):
                    seller_details['company_name'] = text
                elif self._is_inn_or_registration(text):
                    seller_details['registration_number'] = text
                elif 'режим работы' in text.lower() or 'работ' in text.lower():
                    seller_details['working_hours'] = text
                elif self._is_address(text):
                    seller_details['address'] = text
                else:
                    # Добавляем прочую информацию
                    if 'other_info' not in seller_details:
                        seller_details['other_info'] = []
                    seller_details['other_info'].append(text)
            
            logger.info(f"Дополнительная информация о продавце получена: {seller_details}")
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении данных из тултипа: {str(e)}")
            
        return seller_details

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

    def close(self):
        """Закрытие драйвера"""
        if hasattr(self, 'driver') and self.driver:
            self.driver.quit()
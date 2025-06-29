from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from src.bot.central_logger import central_logger as logger 
import time

class SellerDetailsParser:
    def __init__(self):
        self.max_attempts = 10
        self.current_attempt = 0
        self.visited_products = set()
    
    def parse_seller_details(self, driver, seller_url=None):
        """Парсинг дополнительной информации о продавце со страницы товара с повторными попытками"""
        seller_details = {}
        self.current_attempt = 0
        
        while self.current_attempt < self.max_attempts:
            self.current_attempt += 1
            logger.info(f"Попытка {self.current_attempt} из {self.max_attempts} получить данные продавца")
            
            try:
                # Пытаемся получить данные с текущей страницы
                seller_details = self._try_parse_current_page(driver)
                
                if seller_details and self._is_valid_seller_data(seller_details):
                    logger.info(f"Успешно получены данные продавца с попытки {self.current_attempt}")
                    return seller_details
                
                # Если данные не получены, пробуем другой товар того же продавца
                if self.current_attempt < self.max_attempts:
                    if not self._try_another_product(driver, seller_url):
                        logger.warning("Не удалось найти другие товары продавца")
                        break
                        
            except Exception as e:
                logger.error(f"Ошибка в попытке {self.current_attempt}: {str(e)}")
                if self.current_attempt < self.max_attempts:
                    self._try_another_product(driver, seller_url)
        
        logger.warning(f"Не удалось получить данные продавца за {self.max_attempts} попыток")
        return seller_details
    
    def _try_parse_current_page(self, driver):
        """Попытка парсинга текущей страницы"""
        seller_details = {}
        
        try:
            # Добавляем текущий URL в посещенные
            current_url = driver.current_url
            self.visited_products.add(current_url)
            logger.info(f"Парсим страницу: {current_url}")
            
            # УЛУЧШЕННАЯ ЛОГИКА СКРОЛЛА (из рабочего примера)
            # Сначала скроллим вниз для активации контента
            driver.execute_script("window.scrollTo(0, 600);")
            time.sleep(0.5)
            
            # Ждем загрузки секции с продавцом
            seller_section = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-widget="webCurrentSeller"]'))
            )
            
            # Дополнительный скролл к секции с продавцом (как в рабочем примере)
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", seller_section)
            time.sleep(1)
            
            # Еще один скролл для уверенности (из рабочего кода)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.4);")
            time.sleep(0.5)
            
            # Ищем кнопку с информацией о продавце
            info_button = self._find_info_button(seller_section)
            if not info_button:
                logger.warning("Кнопка с информацией о продавце не найдена")
                return seller_details
            
            # Скроллим к кнопке перед кликом
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", info_button)
            time.sleep(0.5)
            
            # Наводим курсор и кликаем на кнопку, отслеживаем появление тултипа
            tooltip = self._click_info_button(driver, info_button)
            
            if tooltip:
                # Парсим найденный тултип
                text_content = tooltip.text.strip()
                html_content = tooltip.get_attribute('outerHTML')
                seller_details = self._parse_text_content(text_content, html_content)
            else:
                # Если не получилось отследить появление, пробуем старый способ
                logger.info("Не удалось отследить появление тултипа, пробуем найти существующие")
                seller_details = self._parse_all_tooltips(driver)
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге текущей страницы: {str(e)}")
            
        return seller_details
    
    def _try_another_product(self, driver, seller_url):
        """Попытка перейти к другому товару того же продавца"""
        try:
            # Если есть URL продавца, переходим к его магазину
            if seller_url and seller_url not in self.visited_products:
                logger.info(f"Переходим в магазин продавца: {seller_url}")
                driver.get(seller_url)
                time.sleep(3)
                
                # Ищем товары в магазине
                product_links = self._find_seller_products(driver)
                if product_links:
                    for link in product_links[:5]:  # Берем первые 5 товаров
                        if link not in self.visited_products:
                            logger.info(f"Переходим к товару: {link}")
                            driver.get(link)
                            time.sleep(2)
                            return True
            
            # Альтернативный способ: ищем ссылку на продавца на текущей странице
            seller_link = self._find_seller_link_on_page(driver)
            if seller_link and seller_link not in self.visited_products:
                logger.info(f"Найдена ссылка на продавца: {seller_link}")
                driver.get(seller_link)
                time.sleep(3)
                
                # Ищем товары в магазине
                product_links = self._find_seller_products(driver)
                if product_links:
                    for link in product_links[:3]:
                        if link not in self.visited_products:
                            driver.get(link)
                            time.sleep(2)
                            return True
            
            # Если не получилось найти другие товары через магазин, 
            # пробуем найти похожие товары на текущей странице
            return self._try_related_products(driver)
            
        except Exception as e:
            logger.error(f"Ошибка при поиске другого товара: {str(e)}")
            return False
    
    def _find_seller_link_on_page(self, driver):
        """Поиск ссылки на магазин продавца на странице товара"""
        selectors = [
            'div[data-widget="webCurrentSeller"] a[href*="/seller/"]',
            'a[href*="/seller/"]',
            'div[data-widget="webCurrentSeller"] a',
            '.seller-link',
            '[data-testid="seller-link"]'
        ]
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    href = element.get_attribute('href')
                    if href and ('/seller/' in href or '/shop/' in href):
                        return href
            except Exception:
                continue
        return None
    
    def _find_seller_products(self, driver):
        """Поиск товаров в магазине продавца"""
        product_links = []
        
        try:
            # Ждем загрузки страницы магазина
            time.sleep(2)
            
            # Различные селекторы для ссылок на товары
            product_selectors = [
                'a[href*="/product/"]',
                '.tile-hover-target',
                '[data-widget="searchResultsV2"] a',
                '.product-card a',
                'a[href*="/detail/"]'
            ]
            
            for selector in product_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        href = element.get_attribute('href')
                        if href and ('/product/' in href or '/detail/' in href):
                            if href not in self.visited_products:
                                product_links.append(href)
                    
                    if product_links:
                        break
                except Exception:
                    continue
            
            logger.info(f"Найдено {len(product_links)} товаров продавца")
            return product_links[:10]  # Возвращаем максимум 10 товаров
            
        except Exception as e:
            logger.error(f"Ошибка при поиске товаров продавца: {str(e)}")
            return []
    
    def _try_related_products(self, driver):
        """Попытка найти связанные товары на текущей странице"""
        try:
            # Ищем блоки с похожими или рекомендуемыми товарами
            related_selectors = [
                'div[data-widget="similarProducts"] a[href*="/product/"]',
                'div[data-widget="recommendations"] a[href*="/product/"]',
                '.recommendations a[href*="/product/"]',
                '[data-testid="similar-products"] a'
            ]
            
            for selector in related_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements[:3]:  # Пробуем первые 3
                        href = element.get_attribute('href')
                        if href and href not in self.visited_products:
                            logger.info(f"Переходим к похожему товару: {href}")
                            driver.get(href)
                            time.sleep(2)
                            return True
                except Exception:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Ошибка при поиске похожих товаров: {str(e)}")
            return False
    
    def _is_valid_seller_data(self, seller_details):
        """Проверка, что данные продавца валидны и полны"""
        if not seller_details:
            return False
        
        # Проверяем наличие ключевых данных
        required_fields = ['company_name', 'inn']
        has_required = any(field in seller_details for field in required_fields)
        
        # Проверяем, что данные не пустые
        has_content = any(
            value and str(value).strip() 
            for value in seller_details.values() 
            if not isinstance(value, list)
        )
        
        # Проверяем списки
        has_list_content = any(
            value and len(value) > 0 
            for value in seller_details.values() 
            if isinstance(value, list)
        )
        
        return has_required and (has_content or has_list_content)

    def _find_info_button(self, seller_section):
        """Поиск кнопки с информацией о продавце с улучшенной логикой"""
        button_selectors = [
            'div.ea20-a.k9j_27.n7j_27 button.ga20-a',
            'button.ga20-a[aria-label=""]',
            'div[data-widget="webCurrentSeller"] button[aria-label=""]',
            'button.ga20-a',
            'button[class*="ga20"]',
            'button[aria-label=""]',  # Добавляем более общий селектор
            'button svg',  # Кнопка с иконкой
            'button'  # Самый общий
        ]
        
        for selector in button_selectors:
            try:
                buttons = seller_section.find_elements(By.CSS_SELECTOR, selector)
                logger.info(f"Найдено {len(buttons)} кнопок по селектору: {selector}")
                
                for i, button in enumerate(buttons):
                    try:
                        if button and button.is_displayed() and button.is_enabled():
                            # Дополнительная проверка видимости
                            location = button.location
                            size = button.size
                            
                            if location['y'] > 0 and size['height'] > 0:
                                # Проверяем, что это именно кнопка информации
                                if self._is_info_button(button):
                                    logger.info(f"Найдена кнопка информации #{i} с селектором: {selector}")
                                    return button
                                else:
                                    logger.info(f"Кнопка #{i} не является кнопкой информации")
                    except Exception as e:
                        logger.warning(f"Ошибка при проверке кнопки #{i}: {str(e)}")
                        continue
                        
            except NoSuchElementException:
                continue
            except Exception as e:
                logger.warning(f"Ошибка при поиске по селектору {selector}: {str(e)}")
                continue
                
        return None

    def _is_info_button(self, button):
        """Улучшенная проверка, является ли кнопка кнопкой информации"""
        try:
            # Проверяем наличие иконки информации
            try:
                icon = button.find_element(By.TAG_NAME, 'svg')
                if icon:
                    # Проверяем атрибуты SVG для определения типа иконки
                    svg_html = icon.get_attribute('outerHTML')
                    if any(keyword in svg_html.lower() for keyword in ['info', 'question', 'help']):
                        return True
                    # Если есть SVG, скорее всего это кнопка информации
                    return True
            except NoSuchElementException:
                pass
            
            # Проверяем атрибуты и классы
            class_name = button.get_attribute('class') or ''
            aria_label = button.get_attribute('aria-label') or ''
            data_testid = button.get_attribute('data-testid') or ''
            
            # Кнопка информации обычно имеет определенные признаки
            info_indicators = [
                'ga20-a' in class_name and (not aria_label or aria_label.strip() == ''),
                'info' in class_name.lower(),
                'info' in aria_label.lower(),
                'info' in data_testid.lower(),
                button.get_attribute('title') and 'info' in button.get_attribute('title').lower()
            ]
            
            if any(info_indicators):
                return True
            
            # Проверяем размер кнопки (кнопки информации обычно маленькие)
            try:
                size = button.size
                if size['width'] <= 40 and size['height'] <= 40:
                    return True
            except:
                pass
                
            return False
            
        except Exception as e:
            logger.warning(f"Ошибка при проверке кнопки информации: {str(e)}")
            return False

    def _click_info_button(self, driver, info_button):
        """Наведение и клик на кнопку информации с отслеживанием появления тултипа"""
        try:
            # Убеждаемся, что кнопка видима (дополнительный скролл)
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", info_button)
            time.sleep(0.5)
            
            # Еще один скролл для активации элементов (из рабочего примера)
            driver.execute_script("window.scrollTo(0, window.pageYOffset + 100);")
            time.sleep(0.3)
            
            # Запоминаем количество vue-portal-target до клика
            portals_before = len(driver.find_elements(By.CSS_SELECTOR, 'body .vue-portal-target'))
            logger.info(f"Количество vue-portal-target до клика: {portals_before}")
            
            actions = ActionChains(driver)
            actions.move_to_element(info_button).perform()
            time.sleep(0.5)
            
            # Пробуем разные способы клика
            try:
                info_button.click()
            except:
                try:
                    driver.execute_script("arguments[0].click();", info_button)
                except:
                    # Последняя попытка - клик через координаты
                    actions.move_to_element(info_button).click().perform()
            
            logger.info("Клик по кнопке информации выполнен, ожидаем появления тултипа...")
            return self._wait_for_tooltip_appearance(driver, portals_before)
            
        except Exception as e:
            logger.error(f"Ошибка при клике на кнопку: {str(e)}")
            return None

    def _wait_for_tooltip_appearance(self, driver, initial_count):
        """Ожидание появления нового vue-portal-target"""
        max_wait_time = 5  # максимум 5 секунд ожидания
        check_interval = 0.2  # проверяем каждые 200мс
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            try:
                current_portals = driver.find_elements(By.CSS_SELECTOR, 'body .vue-portal-target')
                
                # Если появился новый портал
                if len(current_portals) > initial_count:
                    # Ищем последний добавленный портал (обычно это наш тултип)
                    for portal in current_portals:
                        if portal.is_displayed():
                            html_content = portal.get_attribute('outerHTML')
                            text_content = portal.text.strip()
                            
                            logger.info(f"Найден новый тултип:")
                            logger.info(f"HTML: {html_content[:300]}...")
                            logger.info(f"Текст: {text_content}")
                            
                            # Проверяем, содержит ли тултип данные продавца
                            if self._looks_like_seller_info(text_content):
                                logger.info("Тултип содержит данные продавца")
                                return portal
                
                time.sleep(check_interval)
                elapsed_time += check_interval
                
            except Exception as e:
                logger.warning(f"Ошибка при проверке тултипов: {str(e)}")
                time.sleep(check_interval)
                elapsed_time += check_interval
        
        logger.warning("Тултип с данными продавца не появился в течение ожидаемого времени")
        return None

    def _parse_all_tooltips(self, driver):
        """Упрощенный парсинг тултипа"""
        seller_details = {}
        
        try:
            # Находим все видимые vue-portal-target в body
            all_portals = driver.find_elements(By.CSS_SELECTOR, 'body .vue-portal-target')
            logger.info(f"Найдено {len(all_portals)} vue-portal-target элементов")
            
            # Проверяем каждый портал
            for i, portal in enumerate(all_portals):
                try:
                    if not portal.is_displayed():
                        continue
                    
                    # Получаем весь текст из тултипа
                    text_content = portal.text.strip()
                    html_content = portal.get_attribute('outerHTML')
                    
                    logger.info(f"Портал {i+1} - текст: {text_content}")
                    
                    # Проверяем, похож ли на данные продавца
                    if self._looks_like_seller_info(text_content):
                        logger.info(f"Найдены данные продавца в портале {i+1}")
                        seller_details = self._parse_text_content(text_content, html_content)
                        if seller_details:
                            break
                        
                except Exception as e:
                    logger.warning(f"Ошибка при обработке портала {i+1}: {str(e)}")
                    continue
            
            if not seller_details:
                logger.warning("Данные продавца не найдены ни в одном тултипе")
                
        except Exception as e:
            logger.error(f"Ошибка при парсинге тултипов: {str(e)}")
            
        return seller_details

    def _parse_text_content(self, text_content, html_content):
        """Парсинг текстового содержимого тултипа"""
        seller_details = {}
        
        try:
            logger.info(f"Парсим текст: {text_content}")
            logger.info(f"HTML: {html_content[:500]}...")
            
            # Разбиваем текст на строки и обрабатываем каждую
            lines = [line.strip() for line in text_content.split('\n') if line.strip()]
            
            logger.info(f"Найдено {len(lines)} строк для обработки")
            
            for i, line in enumerate(lines):
                logger.info(f"Обрабатываем строку {i+1}: '{line}'")
                
                # Определяем тип информации и сохраняем
                if self._is_company_name(line):
                    seller_details['company_name'] = line
                    logger.info(f"✓ Название компании: {line}")
                    
                elif self._is_inn(line):
                    seller_details['inn'] = line
                    logger.info(f"✓ ИНН/ОГРН: {line}")
                    
                elif self._is_working_hours(line):
                    seller_details['working_hours'] = line
                    logger.info(f"✓ Режим работы: {line}")
                    
                elif self._is_address(line):
                    seller_details['address'] = line
                    logger.info(f"✓ Адрес: {line}")
                    
                else:
                    # Любая другая информация
                    if 'other_info' not in seller_details:
                        seller_details['other_info'] = []
                    seller_details['other_info'].append(line)
                    logger.info(f"• Прочая информация: {line}")
            
            # Дополнительно пытаемся извлечь данные из HTML, если текста недостаточно
            if len(seller_details) < 2:  # Если получили мало данных
                html_data = self._parse_html_content(html_content)
                seller_details.update(html_data)
            
            logger.info(f"Итоговые данные: {seller_details}")
            return seller_details
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге текстового содержимого: {str(e)}")
            return {}

    def _parse_html_content(self, html_content):
        """Дополнительный парсинг HTML содержимого"""
        seller_details = {}
        
        try:
            # Ищем все теги <p> в HTML
            import re
            p_tags = re.findall(r'<p[^>]*>(.*?)</p>', html_content, re.DOTALL)
            
            logger.info(f"Найдено {len(p_tags)} параграфов в HTML")
            
            for i, p_content in enumerate(p_tags):
                # Очищаем от HTML тегов
                clean_text = re.sub(r'<[^>]+>', '', p_content).strip()
                
                if not clean_text:
                    continue
                    
                logger.info(f"HTML параграф {i+1}: '{clean_text}'")
                
                # Применяем те же правила классификации
                if self._is_company_name(clean_text) and 'company_name' not in seller_details:
                    seller_details['company_name'] = clean_text
                elif self._is_inn(clean_text) and 'inn' not in seller_details:
                    seller_details['inn'] = clean_text
                elif self._is_working_hours(clean_text) and 'working_hours' not in seller_details:
                    seller_details['working_hours'] = clean_text
                elif self._is_address(clean_text) and 'address' not in seller_details:
                    seller_details['address'] = clean_text
            
            return seller_details
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге HTML: {str(e)}")
            return {}

    def _extract_tooltip_data(self, tooltip):
        """Извлечение данных из тултипа"""
        seller_details = {}
        
        try:
            # Получаем весь текст из тултипа для анализа
            full_text = tooltip.text.strip()
            logger.info(f"Полный текст тултипа: {full_text}")
            
            # Если тултип пустой или не содержит релевантной информации, пропускаем
            if not full_text or not self._looks_like_seller_info(full_text):
                return seller_details
            
            # Получаем все параграфы с информацией
            info_paragraphs = tooltip.find_elements(By.CSS_SELECTOR, 'p.jn8_27')
            
            if not info_paragraphs:
                # Пробуем альтернативные селекторы
                info_paragraphs = tooltip.find_elements(By.TAG_NAME, 'p')
            
            if not info_paragraphs:
                # Если параграфов нет, разбиваем текст по строкам
                lines = full_text.split('\n')
                info_paragraphs = [type('MockElement', (), {'text': line.strip()}) for line in lines if line.strip()]
            
            logger.info(f"Найдено {len(info_paragraphs)} элементов с информацией")
            
            for i, paragraph in enumerate(info_paragraphs):
                text = paragraph.text.strip() if hasattr(paragraph, 'text') else str(paragraph.text).strip()
                if not text:
                    continue
                
                logger.info(f"Обрабатываем элемент {i}: {text}")
                
                # Определяем тип информации более точно
                if self._is_company_name(text):
                    seller_details['company_name'] = text
                    logger.info(f"Найдено название компании: {text}")
                elif self._is_inn(text):
                    seller_details['inn'] = text
                    logger.info(f"Найден ИНН: {text}")
                elif self._is_working_hours(text):
                    seller_details['working_hours'] = text
                    logger.info(f"Найден режим работы: {text}")
                elif self._is_address(text):
                    seller_details['address'] = text
                    logger.info(f"Найден адрес: {text}")
                else:
                    # Сохраняем прочую информацию
                    if 'other_info' not in seller_details:
                        seller_details['other_info'] = []
                    seller_details['other_info'].append(text)
                    logger.info(f"Добавлена прочая информация: {text}")
                    
        except Exception as e:
            logger.error(f"Ошибка при извлечении данных из тултипа: {str(e)}")
            
        logger.info(f"Итоговые данные продавца: {seller_details}")
        return seller_details

    def _looks_like_seller_info(self, text):
        """Проверяет, похож ли текст на информацию о продавце"""
        seller_keywords = [
            'ИП', 'ООО', 'АО', 'ЗАО', 'ПАО', 'Ltd', 'LLC', 'Inc',
            'режим работы', 'working hours', 'график работы',
            'адрес', 'address', 'г.', 'город', 'ул.', 'улица'
        ]
        
        # Проверяем наличие цифр (для ИНН/ОГРН)
        has_long_number = any(len(''.join(filter(str.isdigit, word))) >= 10 for word in text.split())
        
        # Проверяем ключевые слова
        has_keywords = any(keyword.lower() in text.lower() for keyword in seller_keywords)
        
        return has_long_number or has_keywords

    def _is_company_name(self, text):
        """Проверяет, является ли текст названием компании"""
        company_indicators = ['ИП', 'ООО', 'АО', 'ЗАО', 'ПАО', 'Ltd', 'LLC', 'Inc', 'ОАО']
        return any(indicator in text for indicator in company_indicators)

    def _is_inn(self, text):
        """Проверяет, является ли текст ИНН или ОГРН"""
        # Убираем все нецифровые символы
        digits_only = ''.join(filter(str.isdigit, text))
        
        # ИНН физлица - 12 цифр, ИНН юрлица - 10 цифр, ОГРН - 13 или 15 цифр
        valid_lengths = [10, 12, 13, 15]
        
        # Дополнительная проверка: если строка состоит преимущественно из цифр
        if len(digits_only) in valid_lengths and len(digits_only) / len(text) > 0.8:
            return True
            
        return False

    def _is_working_hours(self, text):
        """Проверяет, является ли текст режимом работы"""
        working_hours_indicators = [
            'режим работы', 'график работы', 'working hours', 'работаем',
            'часы работы', 'время работы', 'schedule', 'график'
        ]
        return any(indicator in text.lower() for indicator in working_hours_indicators)

    def _is_address(self, text):
        """Проверяет, является ли текст адресом"""
        address_indicators = [
            'г.', 'город', 'ул.', 'улица', 'пр.', 'проспект', 'д.', 'дом', 
            'обл.', 'область', 'кв.', 'квартира', 'офис', 'помещение',
            'наб.', 'набережная', 'пер.', 'переулок', 'бул.', 'бульвар'
        ]
    def reset_for_new_seller(self):
        """Сброс состояния для нового продавца"""
        self.current_attempt = 0
        self.visited_products.clear()
        logger.info("Состояние парсера сброшено для нового продавца")
    
    def get_attempts_info(self):
        """Получение информации о попытках"""
        return {
            'current_attempt': self.current_attempt,
            'max_attempts': self.max_attempts,
            'visited_products_count': len(self.visited_products)
        }
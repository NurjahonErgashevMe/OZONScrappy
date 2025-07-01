import logging
import time
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains

logger = logging.getLogger('parser.category_inn_parser.link_collector')

class LinkCollector:
    """Класс для сбора ссылок на товары по продавцам из категории"""
    
    def __init__(self, config, driver_manager):
        self.config = config
        self.driver_manager = driver_manager
        self.max_sellers = int(config.get("MAX_SELLERS", "10"))
        self.scroll_delay = float(config.get("SCROLL_DELAY", "2.0"))
        self.load_timeout = int(config.get("LOAD_TIMEOUT", "30"))
        self.response_wait_time = int(config.get("RESPONSE_WAIT_TIME", "5"))

    def collect_product_links(self, category_url):
        """Оптимизированный метод сбора ссылок с улучшенным сбросом"""
        logger.info(f"Начинаем сбор ссылок по продавцам из категории: {category_url}")
        
        driver = None
        seller_links = {}
        
        try:
            driver = self.driver_manager.setup_driver()
            driver.get(category_url)
            
            # Ожидание загрузки
            try:
                WebDriverWait(driver, self.load_timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".tile-root")))
            except TimeoutException:
                logger.error("Не удалось дождаться загрузки товаров")
                return {}
            
            # Получение продавцов
            sellers = self._initialize_sellers_filter(driver)
            if not sellers:
                logger.error("Не удалось получить список продавцов")
                return {}
            
            category_name = self._get_category_name_from_url(category_url)
            self._save_sellers_to_file(sellers, category_name)
            sellers_to_process = sellers[:self.max_sellers]
            
            # Обработка продавцов
            for i, seller in enumerate(sellers_to_process, 1):
                logger.info(f"Обработка продавца {i}/{len(sellers_to_process)}: {seller['name']}")
                
                # Обработка продавца с повторными попытками
                if self._process_single_seller(driver, seller, category_url):
                    product_link = self._get_first_product_link(driver)
                    if product_link:
                        seller_links[seller['name']] = product_link
                        logger.info(f"Ссылка получена: {product_link}")
                    else:
                        logger.warning("Не удалось получить ссылку на товар")
                else:
                    logger.warning(f"Не удалось обработать продавца {seller['name']}")
                
                # Сброс фильтра
                self._reset_filters_and_prepare_next(driver, category_url)
            
            self._save_seller_links_to_file(seller_links, category_name)
            return seller_links
            
        except Exception as e:
            logger.error(f"Критическая ошибка: {str(e)}")
            return {}
        finally:
            self.driver_manager.close_driver(driver)

    def _initialize_sellers_filter(self, driver):
        """Инициализация фильтра продавцов и получение полного списка"""
        try:
            # Скролл к фильтру
            if not self._scroll_to_seller_filter(driver):
                logger.error("Не удалось найти фильтр 'Продавец'")
                return []
            
            # Получение продавцов
            sellers = self._get_all_sellers(driver)
            if not sellers:
                logger.error("Не удалось получить список продавцов")
                return []
                
            return sellers
            
        except Exception as e:
            logger.error(f"Ошибка инициализации фильтра продавцов: {str(e)}")
            return []

    def _process_single_seller(self, driver, seller, category_url):
        """Обработка одного продавца с повторными попытками"""
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                # Находим актуальный элемент продавца
                current_seller = self._find_seller_by_name(driver, seller['name'])
                if not current_seller:
                    logger.warning(f"Попытка {attempt + 1}: Продавец '{seller['name']}' не найден в DOM")
                    if attempt < max_attempts - 1:
                        # Пробуем переинициализировать фильтр
                        self._reinitialize_seller_filter(driver)
                        continue
                    else:
                        return False
                
                # Выбираем продавца
                if self._select_seller(driver, current_seller):
                    # Ожидаем обновления товаров
                    if self._wait_for_products_update(driver):
                        return True
                    else:
                        logger.warning(f"Попытка {attempt + 1}: Товары не обновились")
                else:
                    logger.warning(f"Попытка {attempt + 1}: Не удалось выбрать продавца")
                
                # Если не удалось, сбрасываем и пробуем снова
                if attempt < max_attempts - 1:
                    self._reset_filters_and_prepare_next(driver, category_url)
                    
            except Exception as e:
                logger.error(f"Попытка {attempt + 1} - Ошибка обработки продавца: {str(e)}")
                if attempt < max_attempts - 1:
                    self._reset_filters_and_prepare_next(driver, category_url)
                    
        return False

    def _reinitialize_seller_filter(self, driver):
        """Переинициализация фильтра продавцов"""
        try:
            logger.info("Переинициализация фильтра продавцов...")
            
            # Скролл к фильтру
            if self._scroll_to_seller_filter(driver):
                # Открываем полный список продавцов
                self._expand_seller_filter(driver)
                time.sleep(2)
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Ошибка переинициализации: {str(e)}")
            return False

    def _expand_seller_filter(self, driver):
        """Раскрытие полного списка продавцов"""
        try:
            # Находим контейнер фильтра продавцов
            seller_container = driver.find_element(
                By.XPATH, 
                "//span[contains(@class, 'tsCompactControl500Medium') and contains(text(), 'Продавец')]/ancestor::div[contains(@class, 'ef9_11')]"
            )
            
            # Ищем и нажимаем кнопку "Посмотреть все"
            show_all_xpaths = [
                ".//button[contains(@class, 'ud6_11') and contains(@class, 'ga20-a')]",
                ".//button[.//div[contains(text(), 'Посмотреть все')]]",
                ".//button[.//div[contains(text(), 'Показать все')]]",
                ".//button[.//div[contains(text(), 'Ещё')]]"
            ]
            
            for xpath in show_all_xpaths:
                try:
                    show_all_button = seller_container.find_element(By.XPATH, xpath)
                    if show_all_button.is_displayed() and show_all_button.is_enabled():
                        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", show_all_button)
                        time.sleep(1)
                        driver.execute_script("arguments[0].click();", show_all_button)
                        logger.info("Кнопка 'Посмотреть все' нажата")
                        time.sleep(3)
                        return True
                except Exception:
                    continue
                    
            logger.debug("Кнопка 'Посмотреть все' не найдена или уже нажата")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка раскрытия списка продавцов: {str(e)}")
            return False

    def _reset_filters_and_prepare_next(self, driver, category_url):
        """Сброс фильтров и подготовка к следующему продавцу"""
        try:
            # Пробуем мягкий сброс
            if self._soft_reset_filters(driver):
                logger.info("Мягкий сброс фильтров выполнен")
                # После мягкого сброса переинициализируем фильтр
                self._reinitialize_seller_filter(driver)
            else:
                # Жесткий сброс через перезагрузку
                logger.info("Выполняем жесткий сброс через перезагрузку страницы")
                driver.get(category_url)
                time.sleep(3)
                
                # Ждем загрузки товаров
                WebDriverWait(driver, self.load_timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".tile-root")))
                
                # Переинициализируем фильтр продавцов
                self._reinitialize_seller_filter(driver)
                
        except Exception as e:
            logger.error(f"Ошибка сброса фильтров: {str(e)}")

    def _soft_reset_filters(self, driver):
        """Мягкий сброс фильтров без перезагрузки страницы"""
        try:
            # Попробуем найти и нажать кнопку закрытия активного фильтра
            reset_methods = [
                # Кнопка закрытия в активных фильтрах
                "//div[contains(@class, 'filters-active')]//button[contains(@class, 'remove-button')]",
                "//div[contains(@class, 'active-filters')]//button[contains(@class, 'close')]",
                # Кнопка "Сбросить"
                "//button[contains(., 'Сбросить') or contains(., 'Очистить')]",
                # Кнопка "X" рядом с фильтром
                "//div[contains(@class, 'filter')]//button[contains(@class, 'close')]"
            ]
            
            for xpath in reset_methods:
                try:
                    reset_button = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, xpath))
                    )
                    driver.execute_script("arguments[0].click();", reset_button)
                    time.sleep(2)
                    logger.info(f"Фильтр сброшен методом: {xpath}")
                    return True
                except:
                    continue
            
            # Попробуем снять выделение с выбранного чекбокса
            try:
                selected_checkbox = driver.find_element(
                    By.XPATH, "//input[@type='checkbox' and @checked]/parent::label"
                )
                driver.execute_script("arguments[0].click();", selected_checkbox)
                time.sleep(2)
                logger.info("Фильтр сброшен через чекбокс")
                return True
            except:
                pass
                
            return False
            
        except Exception as e:
            logger.debug(f"Мягкий сброс не удался: {str(e)}")
            return False

    def _find_seller_by_name(self, driver, seller_name):
        """Поиск продавца по имени в текущем DOM с нормализацией строк"""
        try:
            # Нормализация имени продавца для сравнения
            normalized_seller_name = seller_name.strip().lower()
            
            # Сначала убеждаемся, что фильтр продавцов доступен
            try:
                seller_container = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, 
                        "//span[contains(@class, 'tsCompactControl500Medium') and contains(text(), 'Продавец')]/ancestor::div[contains(@class, 'ef9_11')]"))
                )
            except TimeoutException:
                logger.warning("Контейнер фильтра 'Продавец' не найден")
                return None
            
            # Ищем элементы продавцов
            seller_items = seller_container.find_elements(
                By.XPATH, ".//div[contains(@class, 'u5d_11') or contains(@class, 'w6d_11')]")
            
            for item in seller_items:
                try:
                    # Проверяем видимость элемента
                    if not item.is_displayed():
                        continue
                        
                    name_element = item.find_element(
                        By.XPATH, ".//span[contains(@class, 'tsBody500Medium')]")
                    name_text = name_element.text.strip()
                    
                    # Сравнение с нормализацией
                    if name_text.lower() == normalized_seller_name:
                        try:
                            checkbox = item.find_element(
                                By.XPATH, ".//label[contains(@class, 'b420-a')]")
                            checkbox_input = checkbox.find_element(
                                By.XPATH, ".//input[@type='checkbox']")
                            return {
                                'name': name_text,
                                'element': checkbox,
                                'input': checkbox_input
                            }
                        except:
                            return {
                                'name': name_text,
                                'element': item
                            }
                except Exception:
                    continue
                    
            logger.debug(f"Продавец '{seller_name}' не найден в текущем DOM")
            return None
                
        except Exception as e:
            logger.error(f"Ошибка поиска продавца по имени: {str(e)}")
            return None

    def _select_seller(self, driver, seller):
        """Улучшенный выбор продавца с проверкой состояния"""
        try:
            # Прокрутка и ожидание
            driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", 
                seller['element'])
            time.sleep(1.5)
            
            # Проверка состояния
            is_checked = False
            if 'input' in seller:
                try:
                    is_checked = driver.execute_script(
                        "return arguments[0].checked;", seller['input'])
                except StaleElementReferenceException:
                    logger.debug("Элемент устарел, обновляем состояние")
                    seller['input'] = seller['element'].find_element(
                        By.XPATH, ".//input[@type='checkbox']")
                    is_checked = driver.execute_script(
                        "return arguments[0].checked;", seller['input'])
            
            if is_checked:
                logger.info(f"Продавец {seller['name']} уже выбран")
                return True
            
            # Клик с обработкой возможных ошибок
            try:
                ActionChains(driver).move_to_element(seller['element']).click().perform()
            except:
                driver.execute_script("arguments[0].click();", seller['element'])
            
            # Ожидание применения фильтра
            time.sleep(3)
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при выборе продавца {seller['name']}: {str(e)}")
            return False

    def _get_first_product_link(self, driver):
        """Получение ссылки на первый товар"""
        try:
            # Ищем первый товар
            product = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".tile-root"))
            )
            
            # Ищем ссылку внутри товара
            link_element = product.find_element(By.CSS_SELECTOR, "a")
            href = link_element.get_attribute("href")
            
            # Очищаем ссылку от параметров
            clean_href = href.split('?')[0] if '?' in href else href
            
            # Проверяем и нормализуем URL
            if clean_href.startswith("/product/"):
                clean_href = "https://www.ozon.ru" + clean_href
                
            return clean_href
            
        except Exception as e:
            logger.error(f"Ошибка при получении ссылки на товар: {str(e)}")
            return None

    def _scroll_to_seller_filter(self, driver):
        """Скролл до фильтра 'Продавец'"""
        try:
            # Поиск по тексту "Продавец"
            seller_filter = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Продавец')]"))
            )
            
            # Плавный скролл
            driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", 
                seller_filter
            )
            time.sleep(2)
            return True
            
        except Exception as e:
            logger.error(f"Ошибка скролла к фильтру: {str(e)}")
            return False

    def _get_all_sellers(self, driver):
        """Получение списка всех продавцов"""
        try:
            sellers = []
            
            # 1. Находим контейнер фильтра "Продавец" по XPath
            seller_container = None
            try:
                seller_container = driver.find_element(
                    By.XPATH, 
                    "//span[contains(@class, 'tsCompactControl500Medium') and contains(text(), 'Продавец')]/ancestor::div[contains(@class, 'ef9_11')]"
                )
                logger.info("Найден контейнер фильтра 'Продавец'")
            except Exception as e:
                logger.error(f"Не удалось найти контейнер фильтра 'Продавец': {str(e)}")
                return []
            
            # 2. Раскрываем полный список продавцов
            self._expand_seller_filter(driver)
            
            # 3. Ищем контейнеры продавцов
            seller_containers_xpaths = [
                ".//div[contains(@class, 'u5d_11')]",
                ".//div[contains(@class, 'w6d_11') and contains(@class, 'du_11')]"
            ]
            
            seller_containers = []
            for xpath in seller_containers_xpaths:
                try:
                    containers = seller_container.find_elements(By.XPATH, xpath)
                    if containers:
                        seller_containers = containers
                        logger.info(f"Найдено {len(containers)} контейнеров продавцов")
                        break
                except Exception as e:
                    logger.debug(f"Ошибка поиска контейнеров: {e}")
                    continue
            
            if not seller_containers:
                logger.error("Контейнеры продавцов не найдены")
                return []
            
            # 4. Извлекаем информацию о продавцах
            for container in seller_containers:
                try:
                    # Пропускаем пустые или невидимые контейнеры
                    if not container.is_displayed():
                        continue
                    
                    # Ищем название продавца
                    seller_name = None
                    name_xpaths = [
                        ".//span[contains(@class, 'tsBody500Medium')]",
                        ".//div[contains(@class, 'bq020-a')]//span[contains(@class, 'tsBody500Medium')]",
                        ".//div[contains(@class, 'bq020-a')]"
                    ]
                    
                    for xpath in name_xpaths:
                        try:
                            name_element = container.find_element(By.XPATH, xpath)
                            name_text = name_element.text.strip()
                            if name_text and name_text not in ['Неважно', 'Все продавцы', '']:
                                seller_name = name_text
                                break
                        except Exception:
                            continue
                    
                    if not seller_name:
                        logger.debug("Не удалось извлечь название продавца")
                        continue
                    
                    # Ищем чекбокс
                    try:
                        checkbox = container.find_element(By.XPATH, ".//label[contains(@class, 'b420-a')]")
                        checkbox_input = checkbox.find_element(By.XPATH, ".//input[@type='checkbox']")
                    except Exception as e:
                        logger.debug(f"Не удалось найти чекбокс: {e}")
                        checkbox = None
                        checkbox_input = None
                    
                    if checkbox and checkbox.is_displayed():
                        sellers.append({
                            'name': seller_name,
                            'element': checkbox,
                            'input': checkbox_input
                        })
                        logger.debug(f"Найден продавец: {seller_name}")
                    
                except Exception as e:
                    logger.debug(f"Ошибка обработки контейнера: {e}")
                    continue
            
            logger.info(f"Всего найдено продавцов: {len(sellers)}")
            return sellers
            
        except Exception as e:
            logger.error(f"Ошибка получения продавцов: {str(e)}")
            return []

    def _wait_for_products_update(self, driver):
        """Ожидание обновления товаров в infiniteVirtualPaginator"""
        try:
            logger.info("Ожидание обновления товаров...")
            time.sleep(3)  # Краткая пауза для начала загрузки
            
            # Основной селектор для контейнера товаров
            container_selector = '[data-widget="infiniteVirtualPaginator"]'
            
            # Ожидаем появления контейнера
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, container_selector))
            )
            
            # Ожидаем появления минимум 1 товара
            WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".tile-root"))
            )
            
            # Дополнительная проверка видимости товаров
            products = driver.find_elements(By.CSS_SELECTOR, ".tile-root")
            visible_products = [p for p in products if p.is_displayed()]
            
            if not visible_products:
                logger.warning("Товары не отображаются после обновления")
                return False
                
            logger.info(f"Найдено {len(visible_products)} видимых товаров")
            return True
            
        except TimeoutException:
            logger.error("Таймаут ожидания обновления товаров")
            return False
        except Exception as e:
            logger.error(f"Критическая ошибка: {str(e)}")
            return False

    def _get_category_name_from_url(self, url):
        """Извлечение имени категории из URL"""
        try:
            category_part = url.rstrip('/').split('/')[-1]
            if '?' in category_part:
                category_part = category_part.split('?')[0]
            category_name = category_part.replace('-', '_')
            if not category_name or len(category_name) < 3:
                category_name = "category"
            return category_name
        except Exception as e:
            logger.warning(f"Ошибка извлечения имени категории: {e}")
            return "category"

    def _save_sellers_to_file(self, sellers, category_name):
        """Сохранение списка продавцов в файл"""
        try:
            os.makedirs("output", exist_ok=True)
            
            filename = f"output/{category_name}_sellers.txt"
            with open(filename, "w", encoding="utf-8") as f:
                for seller in sellers:
                    f.write(f"{seller['name']}\n")
            
            logger.info(f"Список продавцов сохранен в файл: {os.path.abspath(filename)}")
        except Exception as e:
            logger.error(f"Ошибка сохранения списка продавцов: {str(e)}")

    def _save_seller_links_to_file(self, seller_links, category_name):
        """Сохранение ссылок продавцов в файл"""
        try:
            os.makedirs("output", exist_ok=True)
            
            filename = f"output/{category_name}_seller_links.txt"
            with open(filename, "w", encoding="utf-8") as f:
                for seller_name, link in seller_links.items():
                    f.write(f"{seller_name}: {link}\n")
            
            logger.info(f"Ссылки продавцов сохранены в файл: {os.path.abspath(filename)}")
        except Exception as e:
            logger.error(f"Ошибка сохранения ссылок продавцов: {str(e)}")

    # Для обратной совместимости оставляем старый метод
    def _extract_product_links(self, driver):
        """Извлечение ссылок на товары со страницы (для обратной совместимости)"""
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, ".tile-root a.tile-clickable-element")
            links = set()
            
            for element in elements:
                href = element.get_attribute("href")
                if href and "/product/" in href:
                    clean_href = href.split('?')[0] if '?' in href else href
                    if clean_href.startswith("https://www.ozon.ru/product/") or clean_href.startswith("/product/"):
                        if clean_href.startswith("/product/"):
                            clean_href = "https://www.ozon.ru" + clean_href
                        links.add(clean_href)
            
            return links
        except Exception as e:
            logger.warning(f"Ошибка извлечения ссылок: {str(e)}")
            return set()
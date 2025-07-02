import logging
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains

logger = logging.getLogger('parser.category_inn_parser.link_collector')

class LinkCollector:
    def __init__(self, config, driver_manager):
        self.config = config
        self.driver_manager = driver_manager
        self.max_sellers = int(config.get("MAX_SELLERS", "50"))
        self.scroll_delay = float(config.get("SCROLL_DELAY", "2.0"))
        self.load_timeout = int(config.get("LOAD_TIMEOUT", "30"))
        self.max_workers = int(config.get("MAX_PARSE_WORKERS", "5"))
        self.seller_data = {}
        self.lock = threading.Lock()

    def collect_product_links(self, category_url, seller_parser):
        logger.info(f"Начинаем сбор ссылок по продавцам из категории: {category_url}")
        
        driver = None
        try:
            driver = self.driver_manager.setup_driver()
            driver.get(category_url)
            
            try:
                WebDriverWait(driver, self.load_timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".tile-root")))
            except TimeoutException:
                logger.error("Не удалось дождаться загрузки товаров")
                return {}
            
            sellers = self._initialize_sellers_filter(driver)
            if not sellers:
                logger.error("Не удалось получить список продавцов")
                return {}
            
            sellers_to_process = sellers[:self.max_sellers]
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = []
                
                for i, seller in enumerate(sellers_to_process, 1):
                    logger.info(f"Обработка продавца {i}/{len(sellers_to_process)}: {seller['name']}")
                    
                    if self._process_single_seller(driver, seller, category_url):
                        product_link = self._get_first_product_link(driver)
                        if product_link:
                            future = executor.submit(
                                self._parse_seller,
                                seller_parser,
                                seller['name'],
                                product_link
                            )
                            futures.append(future)
                        else:
                            logger.warning("Не удалось получить ссылку на товар")
                    else:
                        logger.warning(f"Не удалось обработать продавца {seller['name']}")
                    
                    self._reset_filters_and_prepare_next(driver, category_url)
                
                for future in futures:
                    future.result()
            
            return self.seller_data
            
        except Exception as e:
            logger.error(f"Критическая ошибка: {str(e)}")
            return {}
        finally:
            if driver:
                self.driver_manager.close_driver(driver)

    def _parse_seller(self, seller_parser, seller_name, product_link):
        driver = None
        try:
            driver = self.driver_manager.setup_driver()
            logger.info(f"Парсинг продавца: {seller_name}")
            
            driver.get(product_link)
            time.sleep(2)
            
            seller_data = seller_parser.parse_single_seller(
                driver, 
                seller_name, 
                product_link
            )
            
            with self.lock:
                self.seller_data[seller_name] = seller_data
            
            logger.info(f"Данные продавца {seller_name} успешно получены")
            return seller_data
            
        except Exception as e:
            logger.error(f"Ошибка парсинга продавца {seller_name}: {str(e)}")
            return None
        finally:
            if driver:
                self.driver_manager.close_driver(driver)

    # =============== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ===============
    def _initialize_sellers_filter(self, driver):
        try:
            if not self._scroll_to_seller_filter(driver):
                logger.error("Не удалось найти фильтр 'Продавец'")
                return []
            
            sellers = self._get_all_sellers(driver)
            if not sellers:
                logger.error("Не удалось получить список продавцов")
                return []
                
            return sellers
            
        except Exception as e:
            logger.error(f"Ошибка инициализации фильтра продавцов: {str(e)}")
            return []

    def _process_single_seller(self, driver, seller, category_url):
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                current_seller = self._find_seller_by_name(driver, seller['name'])
                if not current_seller:
                    logger.warning(f"Попытка {attempt + 1}: Продавец '{seller['name']}' не найден")
                    if attempt < max_attempts - 1:
                        self._reinitialize_seller_filter(driver)
                        continue
                    else:
                        return False
                
                if self._select_seller(driver, current_seller):
                    if self._wait_for_products_update(driver):
                        return True
                    else:
                        logger.warning(f"Попытка {attempt + 1}: Товары не обновились")
                else:
                    logger.warning(f"Попытка {attempt + 1}: Не удалось выбрать продавца")
                
                if attempt < max_attempts - 1:
                    self._reset_filters_and_prepare_next(driver, category_url)
                    
            except Exception as e:
                logger.error(f"Попытка {attempt + 1} - Ошибка: {str(e)}")
                if attempt < max_attempts - 1:
                    self._reset_filters_and_prepare_next(driver, category_url)
                    
        return False

    def _reinitialize_seller_filter(self, driver):
        try:
            logger.info("Переинициализация фильтра продавцов...")
            if self._scroll_to_seller_filter(driver):
                self._expand_seller_filter(driver)
                time.sleep(2)
                return True
            return False
        except Exception as e:
            logger.error(f"Ошибка переинициализации: {str(e)}")
            return False

    def _expand_seller_filter(self, driver):
        try:
            seller_container = driver.find_element(
                By.XPATH, 
                "//span[contains(@class, 'tsCompactControl500Medium') and contains(text(), 'Продавец')]/ancestor::div[contains(@class, 'ef9_11')]"
            )
            
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
                    
            logger.debug("Кнопка 'Посмотреть все' не найдена")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка раскрытия списка: {str(e)}")
            return False

    def _reset_filters_and_prepare_next(self, driver, category_url):
        try:
            if self._soft_reset_filters(driver):
                logger.info("Мягкий сброс фильтров выполнен")
                self._reinitialize_seller_filter(driver)
            else:
                logger.info("Выполняем жесткий сброс через перезагрузку")
                driver.get(category_url)
                time.sleep(3)
                WebDriverWait(driver, self.load_timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".tile-root")))
                self._reinitialize_seller_filter(driver)
                
        except Exception as e:
            logger.error(f"Ошибка сброса фильтров: {str(e)}")

    def _soft_reset_filters(self, driver):
        try:
            reset_methods = [
                "//div[contains(@class, 'filters-active')]//button[contains(@class, 'remove-button')]",
                "//div[contains(@class, 'active-filters')]//button[contains(@class, 'close')]",
                "//button[contains(., 'Сбросить') or contains(., 'Очистить')]",
                "//div[contains(@class, 'filter')]//button[contains(@class, 'close')]"
            ]
            
            for xpath in reset_methods:
                try:
                    reset_button = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, xpath))
                    )
                    driver.execute_script("arguments[0].click();", reset_button)
                    time.sleep(2)
                    logger.info(f"Фильтр сброшен: {xpath}")
                    return True
                except:
                    continue
            
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
        try:
            normalized_seller_name = seller_name.strip().lower()
            
            try:
                seller_container = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, 
                        "//span[contains(@class, 'tsCompactControl500Medium') and contains(text(), 'Продавец')]/ancestor::div[contains(@class, 'ef9_11')]"))
                )
            except TimeoutException:
                logger.warning("Контейнер фильтра 'Продавец' не найден")
                return None
            
            seller_items = seller_container.find_elements(
                By.XPATH, ".//div[contains(@class, 'u5d_11') or contains(@class, 'w6d_11')]")
            
            for item in seller_items:
                try:
                    if not item.is_displayed():
                        continue
                        
                    name_element = item.find_element(
                        By.XPATH, ".//span[contains(@class, 'tsBody500Medium')]")
                    name_text = name_element.text.strip()
                    
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
                    
            logger.debug(f"Продавец '{seller_name}' не найден")
            return None
        except Exception as e:
            logger.error(f"Ошибка поиска продавца: {str(e)}")
            return None

    def _select_seller(self, driver, seller):
        try:
            driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", 
                seller['element'])
            time.sleep(1.5)
            
            is_checked = False
            if 'input' in seller:
                try:
                    is_checked = driver.execute_script(
                        "return arguments[0].checked;", seller['input'])
                except StaleElementReferenceException:
                    seller['input'] = seller['element'].find_element(
                        By.XPATH, ".//input[@type='checkbox']")
                    is_checked = driver.execute_script(
                        "return arguments[0].checked;", seller['input'])
            
            if is_checked:
                logger.info(f"Продавец {seller['name']} уже выбран")
                return True
            
            try:
                ActionChains(driver).move_to_element(seller['element']).click().perform()
            except:
                driver.execute_script("arguments[0].click();", seller['element'])
            
            time.sleep(3)
            return True
        except Exception as e:
            logger.error(f"Ошибка при выборе продавца: {str(e)}")
            return False

    def _get_first_product_link(self, driver):
        try:
            product = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".tile-root"))
            )
            
            link_element = product.find_element(By.CSS_SELECTOR, "a")
            href = link_element.get_attribute("href")
            
            clean_href = href.split('?')[0] if '?' in href else href
            
            if clean_href.startswith("/product/"):
                clean_href = "https://www.ozon.ru" + clean_href
                
            return clean_href
        except Exception as e:
            logger.error(f"Ошибка получения ссылки: {str(e)}")
            return None

    def _scroll_to_seller_filter(self, driver):
        try:
            seller_filter = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Продавец')]"))
            )
            
            driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", 
                seller_filter
            )
            time.sleep(2)
            return True
        except Exception as e:
            logger.error(f"Ошибка скролла: {str(e)}")
            return False

    def _get_all_sellers(self, driver):
        try:
            sellers = []
            
            try:
                seller_container = driver.find_element(
                    By.XPATH, 
                    "//span[contains(@class, 'tsCompactControl500Medium') and contains(text(), 'Продавец')]/ancestor::div[contains(@class, 'ef9_11')]"
                )
                logger.info("Найден контейнер фильтра 'Продавец'")
            except Exception as e:
                logger.error(f"Не удалось найти контейнер: {str(e)}")
                return []
            
            self._expand_seller_filter(driver)
            
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
                        logger.info(f"Найдено {len(containers)} контейнеров")
                        break
                except Exception as e:
                    logger.debug(f"Ошибка поиска: {e}")
                    continue
            
            if not seller_containers:
                logger.error("Контейнеры продавцов не найдены")
                return []
            
            for container in seller_containers:
                try:
                    if not container.is_displayed():
                        continue
                    
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
                        logger.debug("Не удалось извлечь название")
                        continue
                    
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
                    
                except Exception as e:
                    logger.debug(f"Ошибка обработки: {e}")
                    continue
            
            logger.info(f"Всего найдено продавцов: {len(sellers)}")
            return sellers
        except Exception as e:
            logger.error(f"Ошибка получения продавцов: {str(e)}")
            return []

    def _wait_for_products_update(self, driver):
        try:
            logger.info("Ожидание обновления товаров...")
            time.sleep(3)
            
            container_selector = '[data-widget="infiniteVirtualPaginator"]'
            
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, container_selector))
            )
            
            WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".tile-root"))
            )
            
            products = driver.find_elements(By.CSS_SELECTOR, ".tile-root")
            visible_products = [p for p in products if p.is_displayed()]
            
            if not visible_products:
                logger.warning("Товары не отображаются")
                return False
                
            logger.info(f"Найдено {len(visible_products)} видимых товаров")
            return True
        except TimeoutException:
            logger.error("Таймаут ожидания")
            return False
        except Exception as e:
            logger.error(f"Критическая ошибка: {str(e)}")
            return False

    def _get_category_name_from_url(self, url):
        try:
            category_part = url.rstrip('/').split('/')[-1]
            if '?' in category_part:
                category_part = category_part.split('?')[0]
            category_name = category_part.replace('-', '_')
            if not category_name or len(category_name) < 3:
                category_name = "category"
            return category_name
        except Exception as e:
            logger.warning(f"Ошибка извлечения имени: {e}")
            return "category"
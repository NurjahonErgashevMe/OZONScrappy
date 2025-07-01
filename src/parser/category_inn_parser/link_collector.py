import logging
import time
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

logger = logging.getLogger('parser.category_inn_parser.link_collector')

class LinkCollector:
    """Класс для сбора ссылок на товары из категории"""
    
    def __init__(self, config, driver_manager):
        self.config = config
        self.driver_manager = driver_manager
        self.total_links = int(config.get("TOTAL_LINKS", "150"))
        self.max_idle_scrolls = int(config.get("MAX_IDLE_SCROLLS", "100"))
        self.scroll_delay = float(config.get("SCROLL_DELAY", "2.0"))
        self.load_timeout = int(config.get("LOAD_TIMEOUT", "30"))

    def collect_product_links(self, category_url):
        """Сбор ссылок на товары из категории"""
        logger.info(f"Начинаем сбор ссылок из категории: {category_url}")
        
        driver = None
        unique_links = set()
        ordered_links = []
        idle_scrolls = 0
        
        try:
            driver = self.driver_manager.setup_driver()
            
            # Загружаем страницу категории
            logger.info(f"Загрузка страницы: {category_url}")
            driver.get(category_url)
            
            # Ожидаем появления товаров
            try:
                WebDriverWait(driver, self.load_timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".tile-root"))
                )
                logger.info("Страница успешно загружена")
            except TimeoutException:
                logger.error("Не удалось дождаться загрузки товаров")
                return []
            
            # Первоначальный сбор ссылок
            current_links = self._extract_product_links(driver)
            if current_links:
                unique_links.update(current_links)
                ordered_links.extend(current_links)
                logger.info(f"Начальное количество ссылок: {len(ordered_links)}")
            
            # Основной цикл сбора ссылок через скролл
            while len(ordered_links) < self.total_links and idle_scrolls < self.max_idle_scrolls:
                # Плавный скролл страницы
                self._scroll_page(driver)
                
                # Имитируем человеческое поведение
                self.driver_manager.simulate_human_behavior(driver)
                
                # Собираем новые ссылки
                current_links = self._extract_product_links(driver)
                new_links = current_links - unique_links
                
                if new_links:
                    logger.info(f"Найдено новых ссылок: {len(new_links)}")
                    unique_links.update(new_links)
                    ordered_links.extend(new_links)
                    idle_scrolls = 0  # Сбрасываем счетчик
                    
                    current_count = len(ordered_links)
                    logger.info(f"Всего ссылок: {min(current_count, self.total_links)}/{self.total_links}")
                else:
                    idle_scrolls += 1
                    logger.debug(f"Нет новых ссылок, idle_scrolls: {idle_scrolls}")
                
                # Проверяем конец страницы
                if self._is_page_end_reached(driver):
                    logger.info("Достигнут конец страницы")
                    break
                
                time.sleep(0.5)
            
            # Ограничиваем количество ссылок
            final_links = ordered_links[:self.total_links]
            
            # Сохраняем ссылки в файл
            category_name = self._get_category_name_from_url(category_url)
            self._save_links_to_file(final_links, category_name)
            
            logger.info(f"Сбор ссылок завершен. Собрано: {len(final_links)} ссылок")
            return final_links
            
        except Exception as e:
            logger.error(f"Ошибка при сборе ссылок: {str(e)}")
            return []
        finally:
            self.driver_manager.close_driver(driver)

    def _extract_product_links(self, driver):
        """Извлечение ссылок на товары со страницы"""
        try:
            # Используем селектор из link_parser.py
            elements = driver.find_elements(By.CSS_SELECTOR, ".tile-root a.tile-clickable-element")
            links = set()
            
            for element in elements:
                href = element.get_attribute("href")
                if href and "/product/" in href:
                    # Очищаем URL от лишних параметров, оставляя только основную часть
                    clean_href = href.split('?')[0] if '?' in href else href
                    if clean_href.startswith("https://www.ozon.ru/product/") or clean_href.startswith("/product/"):
                        # Преобразуем относительный URL в абсолютный
                        if clean_href.startswith("/product/"):
                            clean_href = "https://www.ozon.ru" + clean_href
                        links.add(clean_href)
            
            return links
        except Exception as e:
            logger.warning(f"Ошибка извлечения ссылок: {str(e)}")
            return set()

    def _scroll_page(self, driver):
        """Плавный скролл страницы"""
        try:
            current_scroll_position = driver.execute_script("return window.pageYOffset")
            scroll_height = driver.execute_script("return document.body.scrollHeight")
            
            # Плавный скролл порциями по 300px
            for i in range(current_scroll_position, scroll_height, 300):
                driver.execute_script(f"window.scrollTo(0, {i});")
                time.sleep(0.05)
            
            time.sleep(self.scroll_delay)
            
        except Exception as e:
            logger.warning(f"Ошибка при скролле: {str(e)}")

    def _is_page_end_reached(self, driver):
        """Проверка достижения конца страницы"""
        try:
            total_height = driver.execute_script("return document.body.scrollHeight")
            current_position = driver.execute_script("return window.pageYOffset + window.innerHeight")
            return (total_height - current_position) < 100
        except Exception as e:
            logger.warning(f"Ошибка проверки конца страницы: {str(e)}")
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

    def _save_links_to_file(self, links, category_name):
        """Сохранение ссылок в файл"""
        try:
            # Создаем директорию output если её нет
            os.makedirs("output", exist_ok=True)
            
            filename = f"output/links_{category_name}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write("\n".join(links))
            
            logger.info(f"Ссылки сохранены в файл: {os.path.abspath(filename)}")
        except Exception as e:
            logger.error(f"Ошибка сохранения ссылок: {str(e)}")
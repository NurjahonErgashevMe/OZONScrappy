import logging
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from selenium.webdriver.common.by import By
from src.parser.seller_info_parser import SellerInfoParser

logger = logging.getLogger('parser.category_inn_parser.seller_parser')

class SellerParser:
    """Класс для парсинга информации о продавцах"""
    
    def __init__(self, driver_manager):
        self.driver_manager = driver_manager
        self.seller_info_parser = SellerInfoParser()

    def parse_sellers_from_links(self, links, workers_count):
        """Парсинг ИНН продавцов из списка ссылок с использованием воркеров"""
        logger.info(f"Начинаем парсинг ИНН из {len(links)} ссылок с {workers_count} воркерами")
        
        all_sellers = {}
        sellers_lock = threading.Lock()
        
        def worker_parse_links(worker_id, worker_links):
            """Функция воркера для парсинга ссылок"""
            driver = None
            try:
                driver = self.driver_manager.setup_driver()
                logger.info(f"Воркер {worker_id}: Обрабатывает {len(worker_links)} ссылок")
                
                for i, link in enumerate(worker_links, 1):
                    try:
                        logger.info(f"Воркер {worker_id}: Обрабатывает ссылку {i}/{len(worker_links)}: {link}")
                        
                        # Переходим на страницу товара
                        driver.get(link)
                        time.sleep(4)
                        
                        # Имитируем человеческое поведение
                        self.driver_manager.simulate_human_behavior(driver)
                        
                        # Получаем информацию о продавце
                        seller_info = self.seller_info_parser.get_seller_details(driver)
                        
                        if seller_info and seller_info.get('company_name') != 'Не найдено':
                            seller_key = seller_info.get('company_name', 'Неизвестно')
                            
                            # Потокобезопасное обновление общего словаря
                            with sellers_lock:
                                if seller_key not in all_sellers:
                                    all_sellers[seller_key] = {
                                        'company_name': seller_info.get('company_name', 'Не найдено'),
                                        'inn': seller_info.get('inn', 'Не найдено'),
                                        'products_count': 0,
                                        'sample_products': []
                                    }
                                
                                all_sellers[seller_key]['products_count'] += 1
                                
                                # Добавляем примеры товаров (максимум 3)
                                if len(all_sellers[seller_key]['sample_products']) < 3:
                                    try:
                                        product_title = driver.find_element(By.CSS_SELECTOR, 'h1').text[:100]
                                        all_sellers[seller_key]['sample_products'].append({
                                            'title': product_title,
                                            'url': link
                                        })
                                    except:
                                        pass
                            
                            logger.info(f"Воркер {worker_id}: ✓ Добавлен продавец: {seller_key}")
                        else:
                            logger.warning(f"Воркер {worker_id}: Не удалось получить информацию о продавце")
                            
                    except Exception as e:
                        logger.error(f"Воркер {worker_id}: Ошибка при обработке ссылки {i}: {str(e)}")
                        continue
                        
            except Exception as e:
                logger.error(f"Воркер {worker_id}: Критическая ошибка: {str(e)}")
            finally:
                self.driver_manager.close_driver(driver)

        # Разделяем ссылки между воркерами
        worker_links = [[] for _ in range(workers_count)]
        for i, link in enumerate(links):
            worker_id = i % workers_count
            worker_links[worker_id].append(link)
        
        # Логируем распределение ссылок
        for i, links_list in enumerate(worker_links):
            logger.info(f"Воркер {i+1}: назначено {len(links_list)} ссылок")
        
        # Запускаем воркеры
        with ThreadPoolExecutor(max_workers=workers_count) as executor:
            futures = []
            for i in range(workers_count):
                if worker_links[i]:  # Запускаем только если есть ссылки для обработки
                    future = executor.submit(worker_parse_links, i+1, worker_links[i])
                    futures.append(future)
            
            # Ждем завершения всех воркеров
            for future in futures:
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Ошибка в воркере: {str(e)}")
        
        logger.info(f"Парсинг ИНН завершен. Найдено {len(all_sellers)} уникальных продавцов")
        return all_sellers
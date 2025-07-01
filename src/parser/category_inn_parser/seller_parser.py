import logging
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from src.parser.seller_info_parser import SellerInfoParser

logger = logging.getLogger('parser.category_inn_parser.seller_parser')

class SellerParser:
    """Класс для парсинга информации о продавцах"""
    
    def __init__(self, driver_manager):
        self.driver_manager = driver_manager
        self.seller_info_parser = SellerInfoParser()

    def parse_sellers_from_links(self, seller_links, workers_count):
        """Парсинг ИНН продавцов из словаря {seller_name: product_link}"""
        logger.info(f"Начинаем парсинг ИНН из {len(seller_links)} продавцов с {workers_count} воркерами")
        
        all_sellers = {}
        sellers_lock = threading.Lock()
        
        # Преобразуем словарь в список кортежей для удобства распределения
        seller_items = list(seller_links.items())
        
        def worker_parse_sellers(worker_id, worker_seller_items):
            """Функция воркера для парсинга продавцов"""
            driver = None
            try:
                driver = self.driver_manager.setup_driver()
                logger.info(f"Воркер {worker_id}: Обрабатывает {len(worker_seller_items)} продавцов")
                
                for i, (filter_name, product_link) in enumerate(worker_seller_items, 1):
                    seller_name_parsed = "Не найдено"  # Значение по умолчанию
                    try:
                        logger.info(f"Воркер {worker_id}: Обрабатывает продавца {i}/{len(worker_seller_items)}: {filter_name}")
                        logger.info(f"Воркер {worker_id}: Ссылка на товар: {product_link}")
                        
                        # Переходим на страницу товара
                        driver.get(product_link)
                        time.sleep(4)
                        
                        # Имитируем человеческое поведение
                        self.driver_manager.simulate_human_behavior(driver)
                        
                        # Парсим имя продавца
                        seller_name_parsed = self.seller_info_parser.get_seller_name(driver)
                        logger.info(f"Воркер {worker_id}: ✓ Имя продавца: {seller_name_parsed}")
                        
                        # Получаем информацию о продавце
                        seller_info = self.seller_info_parser.get_seller_details(driver)
                        
                        if seller_info and seller_info.get('company_name') != 'Не найдено':
                            # Получаем название товара для примера
                            product_title = "Товар не найден"
                            try:
                                product_title_element = driver.find_element(By.CSS_SELECTOR, 'h1')
                                product_title = product_title_element.text[:100]
                            except:
                                logger.warning(f"Воркер {worker_id}: Не удалось получить название товара")
                            
                            # Потокобезопасное обновление общего словаря
                            with sellers_lock:
                                all_sellers[filter_name] = {
                                    'seller_name': seller_name_parsed,  # Новое поле
                                    'company_name': seller_info.get('company_name', filter_name),
                                    'inn': seller_info.get('inn', 'Не найдено'),
                                    'products_count': 1,
                                    'sample_products': [{
                                        'title': product_title,
                                        'url': product_link
                                    }],
                                    'filter_name': filter_name,
                                    'parsed_company_name': seller_info.get('company_name', 'Не найдено')
                                }
                            
                            logger.info(f"Воркер {worker_id}: ✓ Обработан продавец: {filter_name}")
                            logger.info(f"Воркер {worker_id}: ✓ Компания: {seller_info.get('company_name', 'Не найдено')}")
                            logger.info(f"Воркер {worker_id}: ✓ ИНН: {seller_info.get('inn', 'Не найдено')}")
                        else:
                            logger.warning(f"Воркер {worker_id}: Не удалось получить информацию о продавце {filter_name}")
                            
                            # Сохраняем информацию о неудачной попытке
                            with sellers_lock:
                                all_sellers[filter_name] = {
                                    'seller_name': seller_name_parsed,  # Новое поле
                                    'company_name': filter_name,
                                    'inn': 'Не найдено',
                                    'products_count': 1,
                                    'sample_products': [{
                                        'title': 'Информация недоступна',
                                        'url': product_link
                                    }],
                                    'filter_name': filter_name,
                                    'parsed_company_name': 'Не найдено'
                                }
                            
                    except Exception as e:
                        logger.error(f"Воркер {worker_id}: Ошибка при обработке продавца {filter_name}: {str(e)}")
                        
                        # Сохраняем информацию об ошибке
                        with sellers_lock:
                            all_sellers[filter_name] = {
                                'seller_name': seller_name_parsed if 'seller_name_parsed' in locals() else 'Ошибка парсинга',
                                'company_name': filter_name,
                                'inn': 'Ошибка парсинга',
                                'products_count': 1,
                                'sample_products': [{
                                    'title': 'Ошибка получения данных',
                                    'url': product_link
                                }],
                                'filter_name': filter_name,
                                'parsed_company_name': 'Ошибка парсинга'
                            }
                        continue
                        
            except Exception as e:
                logger.error(f"Воркер {worker_id}: Критическая ошибка: {str(e)}")
            finally:
                self.driver_manager.close_driver(driver)

        # Разделяем продавцов между воркерами
        worker_seller_items = [[] for _ in range(workers_count)]
        for i, seller_item in enumerate(seller_items):
            worker_id = i % workers_count
            worker_seller_items[worker_id].append(seller_item)
        
        # Логируем распределение продавцов
        for i, seller_list in enumerate(worker_seller_items):
            logger.info(f"Воркер {i+1}: назначено {len(seller_list)} продавцов")
        
        # Запускаем воркеры
        with ThreadPoolExecutor(max_workers=workers_count) as executor:
            futures = []
            for i in range(workers_count):
                if worker_seller_items[i]:  # Запускаем только если есть продавцы для обработки
                    future = executor.submit(worker_parse_sellers, i+1, worker_seller_items[i])
                    futures.append(future)
            
            # Ждем завершения всех воркеров
            for future in futures:
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Ошибка в воркере: {str(e)}")
        
        logger.info(f"Парсинг ИНН завершен. Обработано {len(all_sellers)} продавцов")
        return all_sellers
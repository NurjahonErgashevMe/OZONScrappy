import logging
import time
import os
import tempfile
import threading
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import selenium_stealth

logger = logging.getLogger('parser.category_inn_parser.driver_manager')

class DriverManager:
    """Класс для управления веб-драйверами Selenium"""
    
    def __init__(self):
        self._driver_counter = 0
        self._counter_lock = threading.Lock()
    
    def setup_driver(self):
        # Получаем уникальный ID для драйвера
        with self._counter_lock:
            self._driver_counter += 1
            driver_id = self._driver_counter
        
        options = Options()

        # Создаем уникальную папку для пользовательских данных
        temp_dir = tempfile.mkdtemp(prefix=f"chrome_profile_{driver_id}_")
        options.add_argument(f'--user-data-dir={temp_dir}')
        
        # Уникальный порт для отладки
        debug_port = 9222 + driver_id
        options.add_argument(f'--remote-debugging-port={debug_port}')

        # options.add_argument('--headless')  
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')
        options.add_argument('--disable-features=VizDisplayCompositor')
        
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Увеличиваем лимиты для множественных вкладок
        options.add_argument('--max_old_space_size=4096')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-renderer-backgrounding')
        
        # Дополнительные опции для стабильности при множественных процессах
        options.add_argument('--no-first-run')
        options.add_argument('--disable-default-apps')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')
        
        options.add_argument(
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        try:
            driver = webdriver.Chrome(options=options)
            logger.info(f"Драйвер {driver_id} создан с профилем: {temp_dir}")
        except Exception as e:
            logger.error(f"Ошибка создания драйвера {driver_id}: {str(e)}")
            # Пытаемся очистить временную папку при ошибке
            try:
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
            except:
                pass
            raise
        
        selenium_stealth.stealth(
            driver,
            languages=["ru-RU", "ru"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )
        
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                         'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

        # Функция для проверки и очистки вкладок
        def validate_tabs():
            """Проверяет и закрывает подозрительные вкладки"""
            try:
                handles = driver.window_handles.copy()
                main_handle = handles[0] if handles else None
                
                for handle in handles:
                    try:
                        driver.switch_to.window(handle)
                        current_url = driver.current_url
                        
                        # Закрываем вкладки с подозрительными URL
                        if not (current_url.startswith("https://ozon.ru") or 
                               current_url.startswith("https://www.ozon.ru") or
                               current_url == "about:blank"):
                            logger.warning(f"Закрываем подозрительную вкладку: {current_url}")
                            driver.close()
                    except Exception as e:
                        logger.debug(f"Ошибка при проверке вкладки {handle}: {str(e)}")
                        try:
                            driver.close()
                        except:
                            pass
                
                # Возвращаемся на основную вкладку
                remaining_handles = driver.window_handles
                if remaining_handles:
                    if main_handle in remaining_handles:
                        driver.switch_to.window(main_handle)
                    else:
                        driver.switch_to.window(remaining_handles[0])
                else:
                    logger.error("Не осталось открытых вкладок!")
                    
            except Exception as e:
                logger.error(f"Ошибка при валидации вкладок: {str(e)}")

        def close_extra_tabs(keep_count=5):
            """Закрывает лишние вкладки, оставляя только указанное количество"""
            try:
                handles = driver.window_handles
                if len(handles) > keep_count:
                    for handle in handles[keep_count:]:
                        driver.switch_to.window(handle)
                        driver.close()
                    
                    # Переключаемся на первую вкладку
                    remaining_handles = driver.window_handles
                    if remaining_handles:
                        driver.switch_to.window(remaining_handles[0])
                        
                    logger.info(f"Закрыто {len(handles) - len(remaining_handles)} лишних вкладок")
                        
            except Exception as e:
                logger.error(f"Ошибка при закрытии лишних вкладок: {str(e)}")

        def get_tab_count():
            """Возвращает количество открытых вкладок"""
            try:
                return len(driver.window_handles)
            except:
                return 0

        # Сохраняем путь к временной папке для последующей очистки
        driver._temp_profile_dir = temp_dir
        driver._driver_id = driver_id
        
        # Прикрепляем функции к драйверу
        driver.validate_tabs = validate_tabs
        driver.close_extra_tabs = close_extra_tabs
        driver.get_tab_count = get_tab_count

        return driver

    def simulate_human_behavior(self, driver):
        """Имитация человеческого поведения для обхода детекции"""
        try:
            # Случайный скролл
            driver.execute_script("window.scrollTo(0, Math.floor(Math.random() * 500));")
            time.sleep(0.5)  # Уменьшаем задержку для ускорения
            
            # Движение мыши (имитация через JavaScript)
            driver.execute_script("""
                var event = new MouseEvent('mousemove', {
                    'view': window,
                    'bubbles': true,
                    'cancelable': true,
                    'clientX': Math.random() * window.innerWidth,
                    'clientY': Math.random() * window.innerHeight
                });
                document.dispatchEvent(event);
            """)
            time.sleep(0.3)  # Уменьшаем задержку
            
        except Exception as e:
            logger.debug(f"Ошибка при имитации поведения: {str(e)}")

    def close_driver(self, driver):
        """Безопасное закрытие драйвера с очисткой временных файлов"""
        if driver:
            temp_dir = None
            driver_id = "unknown"
            
            try:
                # Получаем информацию о драйвере
                temp_dir = getattr(driver, '_temp_profile_dir', None)
                driver_id = getattr(driver, '_driver_id', 'unknown')
                
                # Сначала закрываем все вкладки
                try:
                    handles = driver.window_handles
                    for handle in handles:
                        driver.switch_to.window(handle)
                        driver.close()
                except:
                    pass
                
                # Затем закрываем драйвер
                driver.quit()
                logger.info(f"Драйвер {driver_id} закрыт")
                
            except Exception as e:
                logger.warning(f"Ошибка при закрытии драйвера {driver_id}: {str(e)}")
            
            # Очищаем временную папку профиля
            if temp_dir and os.path.exists(temp_dir):
                try:
                    import shutil
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    logger.info(f"Временный профиль {temp_dir} удален")
                except Exception as e:
                    logger.warning(f"Не удалось удалить временный профиль {temp_dir}: {str(e)}")
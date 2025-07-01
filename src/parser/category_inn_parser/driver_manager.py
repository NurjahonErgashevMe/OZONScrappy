import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import selenium_stealth

logger = logging.getLogger('parser.category_inn_parser.driver_manager')

class DriverManager:
    """Класс для управления веб-драйверами Selenium"""
    
    def setup_driver(self):
        options = Options()

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
        
        options.add_argument(
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        

        
        driver = webdriver.Chrome(options=options)
        
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

        # Функция для проверки вкладок
        # def validate_tabs():
        #     handles = driver.window_handles
        #     for handle in handles:
        #         driver.switch_to.window(handle)
        #         current_url = driver.current_url
        #         if not current_url.startswith("https://ozon.ru"):
        #             driver.close()
            
        #     # Возвращаемся на первую вкладку
        #     if driver.window_handles:
        #         driver.switch_to.window(driver.window_handles[0])

        # # Прикрепляем функцию к драйверу
        # driver.validate_tabs = validate_tabs

        return driver

    def simulate_human_behavior(self, driver):
        """Имитация человеческого поведения для обхода детекции"""
        try:
            # Случайный скролл
            driver.execute_script("window.scrollTo(0, Math.floor(Math.random() * 500));")
            time.sleep(1)
            
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
            time.sleep(0.5)
            
        except Exception as e:
            logger.debug(f"Ошибка при имитации поведения: {str(e)}")

    def close_driver(self, driver):
        """Безопасное закрытие драйвера"""
        if driver:
            try:
                driver.quit()
                logger.info("Драйвер закрыт")
            except Exception as e:
                logger.warning(f"Ошибка при закрытии драйвера: {str(e)}")
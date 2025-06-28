from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium_stealth import stealth
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройка опций браузера
options = webdriver.ChromeOptions()
# options.add_argument('--headless')  # Без графического интерфейса
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

# Инициализация драйвера
driver = webdriver.Chrome(options=options)

# Применение stealth
stealth(
    driver,
    languages=["en-US", "en"],
    vendor="Google Inc.",
    platform="Win32",
    webgl_vendor="Intel Inc.",
    renderer="Intel Iris OpenGL Engine",
    fix_hairline=True,
    webdriver=False
)

# Функция ожидания элемента
def wait_for_element(driver, locator, timeout=15):
    try:
        return WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located(locator)
        )
    except TimeoutException:
        logger.error(f"Элемент не найден: {locator}")
        raise

# Открытие страницы
url = "https://ozon.ru/seller/trade-electronics-183434/?miniapp=seller_183434"
driver.get(url)

# Извлечение названия магазина
def extract_shop_name(driver):
    try:
        locator = (By.CSS_SELECTOR, 'span.tsHeadline600Large')  # Локатор для названия магазина
        element = wait_for_element(driver, locator)
        return element.text.strip()
    except (TimeoutException, NoSuchElementException) as e:
        logger.error(f"Ошибка извлечения названия: {str(e)}")
        return "Название магазина не найдено."

# Вывод результата
shop_name = extract_shop_name(driver)
print(f"Название магазина: {shop_name}")

# Завершение работы драйвера
driver.quit()

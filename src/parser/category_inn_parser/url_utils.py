import logging
import re
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger('parser.url_utils')

class UrlUtils:
    def __init__(self):
        pass

    def get_category_name(self, url):
        """Извлечение имени категории из URL"""
        try:
            # Извлекаем последнюю часть URL после последнего слеша
            category_part = url.rstrip('/').split('/')[-1]
            
            # Убираем параметры запроса
            if '?' in category_part:
                category_part = category_part.split('?')[0]
            
            # Заменяем дефисы на подчеркивания для имени файла
            category_name = category_part.replace('-', '_')
            
            # Если не удалось извлечь осмысленное имя, используем дефолтное
            if not category_name or len(category_name) < 3:
                category_name = "category"
                
            return category_name
        except Exception as e:
            logger.warning(f"Ошибка извлечения имени категории: {e}")
            return "category"

    def clean_product_url(self, url):
        """Очистка URL товара от лишних параметров"""
        try:
            if not url:
                return None
            
            # Очищаем URL от лишних параметров, оставляя только основную часть
            clean_url = url.split('?')[0] if '?' in url else url
            
            # Проверяем, что это действительно URL товара
            if self.is_product_url(clean_url):
                # Преобразуем относительный URL в абсолютный
                if clean_url.startswith("/product/"):
                    clean_url = "https://www.ozon.ru" + clean_url
                return clean_url
            
            return None
        except Exception as e:
            logger.warning(f"Ошибка очистки URL: {str(e)}")
            return None

    def is_product_url(self, url):
        """Проверка, является ли URL ссылкой на товар"""
        try:
            if not url:
                return False
            
            # Проверяем наличие /product/ в URL
            return "/product/" in url and (
                url.startswith("https://www.ozon.ru/product/") or 
                url.startswith("/product/")
            )
        except Exception:
            return False

    def is_category_url(self, url):
        """Проверка, является ли URL ссылкой на категорию"""
        try:
            if not url:
                return False
            
            # Проверяем, что это URL категории Ozon
            return (
                url.startswith("https://www.ozon.ru/category/") or
                url.startswith("https://ozon.ru/category/") or
                "/category/" in url
            )
        except Exception:
            return False

    def validate_ozon_url(self, url):
        """Валидация URL Ozon"""
        try:
            if not url:
                return False, "URL не предоставлен"
            
            # Парсим URL
            parsed = urlparse(url)
            
            # Проверяем домен
            valid_domains = ['www.ozon.ru', 'ozon.ru', 'm.ozon.ru']
            if parsed.netloc not in valid_domains:
                return False, "URL не принадлежит Ozon"
            
            # Проверяем протокол
            if parsed.scheme not in ['http', 'https']:
                return False, "Некорректный протокол URL"
            
            return True, "URL корректен"
            
        except Exception as e:
            return False, f"Ошибка валидации URL: {str(e)}"

    def extract_product_id(self, url):
        """Извлечение ID товара из URL"""
        try:
            if not url:
                return None
            
            # Паттерн для извлечения ID товара
            pattern = r'/product/[^/]*?-(\d+)/?'
            match = re.search(pattern, url)
            
            if match:
                return match.group(1)
            
            return None
        except Exception as e:
            logger.warning(f"Ошибка извлечения ID товара: {str(e)}")
            return None

    def build_product_url(self, product_id, product_slug=""):
        """Построение URL товара по ID"""
        try:
            if not product_id:
                return None
            
            base_url = "https://www.ozon.ru/product/"
            
            if product_slug:
                return f"{base_url}{product_slug}-{product_id}/"
            else:
                return f"{base_url}product-{product_id}/"
                
        except Exception as e:
            logger.warning(f"Ошибка построения URL товара: {str(e)}")
            return None

    def get_url_parameters(self, url):
        """Извлечение параметров из URL"""
        try:
            if not url:
                return {}
            
            parsed = urlparse(url)
            return parse_qs(parsed.query)
            
        except Exception as e:
            logger.warning(f"Ошибка извлечения параметров URL: {str(e)}")
            return {}

    def normalize_url(self, url):
        """Нормализация URL (приведение к стандартному виду)"""
        try:
            if not url:
                return None
            
            # Убираем лишние пробелы
            url = url.strip()
            
            # Добавляем протокол если отсутствует
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Парсим и пересобираем URL
            parsed = urlparse(url)
            
            # Нормализуем домен
            netloc = parsed.netloc.lower()
            if netloc == 'ozon.ru':
                netloc = 'www.ozon.ru'
            
            # Убираем лишние слеши в конце пути
            path = parsed.path.rstrip('/')
            
            # Собираем нормализованный URL
            normalized = f"{parsed.scheme}://{netloc}{path}"
            
            if parsed.query:
                normalized += f"?{parsed.query}"
            
            return normalized
            
        except Exception as e:
            logger.warning(f"Ошибка нормализации URL: {str(e)}")
            return url
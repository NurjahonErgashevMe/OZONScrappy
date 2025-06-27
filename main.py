import logging
from parser.ozon_parser import OzonSellerParser

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

if __name__ == "__main__":
    URL = "https://www.ozon.ru/seller/treidcomputers-2620543/?miniapp=seller_2620543"
    
    try:
        parser = OzonSellerParser(headless=False)
        result = parser.parse_seller(URL)
        
        print("\nРезультаты парсинга:")
        print(f"Premium магазин: {'Да' if result['is_premium'] else 'Нет'}")
        print(f"Заказов: {result['orders_count']}")
        print(f"Работает с Ozon: {result['working_since']}")
        print(f"Средняя оценка: {result['average_rating']}")
        print(f"Отзывов: {result['reviews_count']}")
        
    except Exception as e:
        logging.error(f"Критическая ошибка: {str(e)}")
        exit(1)
import logging
from parser.ozon_parser import OzonSellerParser
from parser.product_parser import OzonProductParser

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

if __name__ == "__main__":
    URL = "https://www.ozon.ru/seller/treidcomputers-2620543/?miniapp=seller_2620543"
    
    try:
        # Парсинг информации о продавце
        seller_parser = OzonSellerParser(headless=False)
        seller_result = seller_parser.parse_seller(URL)
        
        print("\n=== Результаты парсинга продавца ===")
        print(f"Premium магазин: {'Да' if seller_result['is_premium'] else 'Нет'}")
        print(f"Заказов: {seller_result['orders_count']}")
        print(f"Работает с Ozon: {seller_result['working_since']}")
        print(f"Средняя оценка: {seller_result['average_rating']}")
        print(f"Отзывов: {seller_result['reviews_count']}")
        
        # Парсинг товаров продавца
        print("\n=== Начинаем парсинг товаров ===")
        product_parser = OzonProductParser(headless=False)
        success = product_parser.parse_products(URL)
        
        if success:
            products = product_parser.get_products()
            print(f"\n=== Парсинг товаров завершен ===")
            print(f"Всего спарсено товаров: {len(products)}")
            print("Excel файл создан в папке 'output'")
        else:
            print("Ошибка при парсинге товаров!")
        
    except Exception as e:
        logging.error(f"Критическая ошибка: {str(e)}")
        exit(1)
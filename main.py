import logging
from parser.ozon_parser import OzonSellerParser
from parser.seller_products_parser import OzonProductParser

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

if __name__ == "__main__":
    URL = "https://www.ozon.ru/seller/trade-electronics-183434/?miniapp=seller_183434"
    
    try:
        # Парсинг информации о продавце
        seller_parser = OzonSellerParser(headless=False)
        seller_result = seller_parser.parse_seller(URL)
        
        print("\n=== Результаты парсинга продавца ===")
        print(f"Premium магазин: {'Да' if seller_result.get('is_premium') else 'Нет'}")
        print(f"Заказов: {seller_result.get('orders_count', 'N/A')}")
        print(f"Работает с Ozon: {seller_result.get('working_since', 'N/A')}")
        print(f"Средняя оценка: {seller_result.get('average_rating', 'N/A')}")
        print(f"Отзывов: {seller_result.get('reviews_count', 'N/A')}")
        
        print(seller_result)
        
        # Вывод дополнительной информации о продавце
        if seller_result.get('company_name') or seller_result.get('inn') or seller_result.get('working_hours'):
            print("\n=== Дополнительная информация о продавце ===")
            
            if seller_result.get('company_name'):
                print(f"Название компании: {seller_result['company_name']}")
            
            if seller_result.get('inn'):
                print(f"ИНН: {seller_result['inn']}")
            
            if seller_result.get('working_hours'):
                print(f"Режим работы: {seller_result['working_hours']}")
        else:
            print("\n=== Дополнительная информация не получена ===")
                
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
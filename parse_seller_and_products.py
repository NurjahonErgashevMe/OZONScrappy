import logging
from parser.ozon_parser import OzonSellerParser
from parser.seller_products_parser import OzonProductParser

logger = logging.getLogger('parse_seller_and_products')

def parse_seller_and_products(seller_url, headless=True, callback=None):
    try:
        # Парсинг информации о продавце
        seller_parser = OzonSellerParser(headless=headless)
        seller_result = seller_parser.parse_seller(seller_url)
        
        # Немедленная отправка информации о продавце
        if callback:
            seller_info = (
                "✓ Информация о продавце:\n"
                f"Название: {seller_result.get('name', 'N/A')}\n"
                f"Premium: {'Да' if seller_result.get('is_premium') else 'Нет'}\n"
                f"Заказов: {seller_result.get('orders_count', 'N/A')}\n"
                f"Работает с: {seller_result.get('working_since', 'N/A')}\n"
            )
            callback(seller_info)
        
        # Парсинг товаров
        product_parser = OzonProductParser(headless=headless)
        success,excel_path = product_parser.parse_products(seller_url)
        
        # # Проверяем тип возвращаемого значения
        # if isinstance(product_result, bool):
        #     # Если метод возвращает булево значение
        #     success = product_result
        #     excel_path = getattr(product_parser, 'excel_path', '') if hasattr(product_parser, 'excel_path') else ''
        # elif isinstance(product_result, dict):
        #     # Если метод возвращает словарь
        #     success = product_result.get('success', False)
        #     excel_path = product_result.get('excel_path', '')
        # else:
        #     # Неожиданный тип результата
        #     logger.warning(f"Неожиданный тип результата от parse_products: {type(product_result)}")
        #     success = False
        #     excel_path = ''
        
        print(success , 'success')
        print(excel_path , 'excel_path')
        
        return {
            'seller': seller_result,
            'products': product_parser.get_products(),
            'excel_path': excel_path,
            'success': success
        }
    except Exception as e:
        logger.error(f"Общая ошибка: {str(e)}")
        if callback:
            callback(f"💥 Критическая ошибка: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
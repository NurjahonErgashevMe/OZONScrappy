import logging
import asyncio
from src.parser.ozon_parser import OzonSellerParser
from src.parser.seller_products_parser import OzonProductParser

logger = logging.getLogger('parse_seller_and_products')


# Сохраняем старую синхронную функцию для совместимости
def parse_seller_and_products(seller_url, headless=True):
    try:
        # Парсинг информации о продавце
        seller_parser = OzonSellerParser(headless=True)
        seller_result = seller_parser.parse_seller(seller_url)
        
        
        # Парсинг товаров
        product_parser = OzonProductParser(headless=headless)
        success, excel_path,seller_name = product_parser.parse_products(seller_url)
        
        print(success, 'success')
        print(excel_path, 'excel_path')
        print(seller_name, 'seller_name')
        
        #  отправка информации о продавце
        seller_info = (
                "✓ Информация о продавце:\n"
                f"Название магазина: {seller_name}\n"
                f"Название компании: {seller_result.get('company_name', 'N/A')}\n"
                f"ИНН: {seller_result.get('inn', 'N/A')}\n"
                f"Premium: {'Да' if seller_result.get('is_premium') else 'Нет'}\n"
                f"Заказов: {seller_result.get('orders_count', 'N/A')}\n"
                f"Работает с: {seller_result.get('working_since', 'N/A')}\n"
        )
        
        logger.info(f"Информация о продавце: {seller_info}")
        
        return {
            'seller': {**seller_result,'seller_name':seller_name},
            'products': product_parser.get_products(),
            'excel_path': excel_path,
            'success': success,
            'seller_info': seller_info
        }
    except Exception as e:
        logger.error(f"Общая ошибка: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
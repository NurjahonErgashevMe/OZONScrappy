import logging
from parser.ozon_parser import OzonSellerParser
from parser.seller_products_parser import OzonProductParser

def parse_seller_and_products(url: str, headless: bool = False):
    """Функция для парсинга продавца и товаров"""
    try:
        # Парсинг информации о продавце
        seller_parser = OzonSellerParser(headless=headless)
        seller_result = seller_parser.parse_seller(url)
        
        # Парсинг товаров продавца
        product_parser = OzonProductParser(headless=headless)
        success = product_parser.parse_products(url)
        products = product_parser.get_products() if success else None
        
        return {
            "seller": seller_result,
            "products": products
        }
        
    except Exception as e:
        logging.error(f"Ошибка при парсинге: {str(e)}")
        return None
    finally:
        if 'seller_parser' in locals():
            seller_parser.close()
        if 'product_parser' in locals():
            product_parser.close()
            
            
if __name__ == "__main__":
    parse_seller_and_products("https://www.ozon.ru/seller/treidcomputers-2620543/?miniapp=seller_2620543",True)
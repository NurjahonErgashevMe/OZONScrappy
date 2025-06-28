import logging
from parser.product_inn_parser import ProductINNParser

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

def run_product_inn_parser():
    """Запуск парсера продавцов из товаров"""
    parser = None
    
    try:
        print("🚀 Запуск парсера продавцов из товаров Ozon")
        print("📁 Убедитесь, что файл products.txt находится в корне проекта")
        print("🔗 В файле должны быть ссылки на товары Ozon (по одной на строку)")
        
        # Создание парсера
        parser = ProductINNParser()  # headless=True для работы в фоне
        
        # Проверка наличия файла products.txt
        product_urls = parser.load_product_urls()
        if not product_urls:
            print("❌ Файл products.txt не найден или пуст!")
            print("💡 Создайте файл products.txt и добавьте ссылки на товары Ozon")
            print("   Пример содержимого:")
            print("   https://www.ozon.ru/product/example-1/")
            print("   https://www.ozon.ru/product/example-2/")
            return
        
        print(f"📊 Найдено {len(product_urls)} товаров для парсинга")
        print("⏱️  Примерное время выполнения: ~{:.1f} минут".format(len(product_urls) * 0.5))
        
        # Запуск парсинга
        success = parser.parse_all_products()
        
        if success and parser.results:
            # Сохранение результатов
            filepath = parser.save_to_excel()
            
            # Вывод статистики
            print("\n" + "="*70)
            print("📈 СТАТИСТИКА ПАРСИНГА ПРОДАВЦОВ")
            print("="*70)
            
            total = len(parser.results)
            inn_found = len([r for r in parser.results if r['inn'] not in ['Не найдено', 'Ошибка']])
            seller_found = len([r for r in parser.results if r['seller_name'] not in ['Не найдено', 'Ошибка']])
            company_found = len([r for r in parser.results if r['company_name'] not in ['Не найдено', 'Ошибка']])
            
            print(f"📦 Всего товаров обработано: {total}")
            print(f"🏪 Продавец найден у: {seller_found} товаров ({(seller_found/total*100):.1f}%)")
            print(f"🏢 Компания найдена у: {company_found} товаров ({(company_found/total*100):.1f}%)")
            print(f"🆔 ИНН найден у: {inn_found} товаров ({(inn_found/total*100):.1f}%)")
            
            # Показываем примеры найденных данных
            successful_results = [r for r in parser.results if r['inn'] not in ['Не найдено', 'Ошибка']]
            if successful_results:
                print(f"\n🎯 Примеры найденных данных:")
                for i, result in enumerate(successful_results[:3], 1):
                    print(f"\n  {i}. Продавец: {result['seller_name']}")
                    print(f"     Компания: {result['company_name']}")
                    print(f"     ИНН: {result['inn']}")
                    print(f"     Товар: {result['product_url']}")
            
            # Показываем товары без ИНН
            failed_results = [r for r in parser.results if r['inn'] in ['Не найдено', 'Ошибка']]
            if failed_results:
                print(f"\n⚠️  Товары без ИНН ({len(failed_results)} шт.):")
                for i, result in enumerate(failed_results[:3], 1):
                    print(f"  {i}. Продавец: {result['seller_name']}")
                if len(failed_results) > 3:
                    print(f"     ... и еще {len(failed_results) - 3} товаров")
            
            if filepath:
                print(f"\n💾 Результаты сохранены в файл: {filepath}")
            
            print("✨ Парсинг завершен успешно!")
            
        else:
            print("❌ Парсинг завершился с ошибками или нет данных")
            
    except KeyboardInterrupt:
        print("\n⏹️  Парсинг прерван пользователем")
    except Exception as e:
        print(f"💥 Критическая ошибка: {str(e)}")
        logging.error(f"Критическая ошибка: {str(e)}")
    finally:
        if parser:
            parser.close()
            print("🔒 Браузер закрыт")

def create_sample_products_file():
    """Создание примера файла products.txt"""
    sample_content = """# Примеры ссылок на товары Ozon
# Замените эти ссылки на реальные ссылки товаров
# Каждая ссылка должна быть на отдельной строке

https://www.ozon.ru/product/example-product-1/
https://www.ozon.ru/product/example-product-2/
https://www.ozon.ru/product/example-product-3/

# Убедитесь, что ссылки ведут на страницы конкретных товаров
# Формат: https://www.ozon.ru/product/название-товара-артикул/
"""
    
    try:
        with open('products_sample.txt', 'w', encoding='utf-8') as f:
            f.write(sample_content)
        print("📝 Создан файл products_sample.txt с примерами ссылок")
        print("📋 Скопируйте его в products.txt и замените ссылки на реальные")
    except Exception as e:
        print(f"❌ Ошибка при создании файла примера: {e}")

if __name__ == "__main__":
    print("="*70)
    print("🔍 ПАРСЕР ПРОДАВЦОВ ИЗ ТОВАРОВ OZON")
    print("="*70)
    
    import os
    if not os.path.exists('products.txt'):
        print("📁 Файл products.txt не найден")
        print("🤔 Хотите создать файл с примерами? (y/n): ", end="")
        
        try:
            choice = input().lower().strip()
            if choice in ['y', 'yes', 'да', 'д']:
                create_sample_products_file()
                print("\n⚠️  Отредактируйте файл products.txt и запустите скрипт снова")
            else:
                print("📝 Создайте файл products.txt со ссылками на товары и запустите скрипт снова")
        except KeyboardInterrupt:
            print("\n👋 До свидания!")
    else:
        run_product_inn_parser()
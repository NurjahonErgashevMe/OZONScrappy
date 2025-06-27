import logging
from parser.inn_parser import INNParser

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

def run_inn_parser():
    """Запуск парсера ИНН"""
    parser = None
    
    try:
        print("🚀 Запуск парсера ИНН продавцов Ozon")
        print("📁 Убедитесь, что файл sellers.txt находится в корне проекта")
        
        # Создание парсера
        parser = INNParser(headless=False)  # headless=True для работы в фоне
        
        # Проверка наличия файла sellers.txt
        seller_urls = parser.load_seller_urls()
        if not seller_urls:
            print("❌ Файл sellers.txt не найден или пуст!")
            return
        
        print(f"📊 Найдено {len(seller_urls)} продавцов для парсинга")
        
        # Запуск парсинга
        success = parser.parse_all_sellers()
        
        if success and parser.results:
            # Сохранение результатов
            parser.save_to_excel()
            
            # Вывод статистики
            print("\n" + "="*60)
            print("📈 СТАТИСТИКА ПАРСИНГА")
            print("="*60)
            
            total = len(parser.results)
            inn_found = len([r for r in parser.results if r['inn'] not in ['Не найдено', 'Ошибка']])
            
            print(f"👥 Всего продавцов: {total}")
            print(f"🆔 ИНН найден у: {inn_found} продавцов")
            print(f"📊 Процент успеха: {(inn_found/total*100):.1f}%")
            
            # Показываем примеры найденных ИНН
            successful_results = [r for r in parser.results if r['inn'] not in ['Не найдено', 'Ошибка']]
            if successful_results:
                print(f"\n🎯 Примеры найденных ИНН:")
                for i, result in enumerate(successful_results[:3], 1):
                    print(f"  {i}. {result['seller_name']}: {result['inn']}")
                    if result['company_name'] != 'Не найдено':
                        print(f"     Компания: {result['company_name']}")
            
            print(f"\n💾 Результаты сохранены в папку 'output'")
            print("✨ Парсинг завершен успешно!")
            
        else:
            print("❌ Парсинг завершился с ошибками")
            
    except KeyboardInterrupt:
        print("\n⏹️  Парсинг прерван пользователем")
    except Exception as e:
        print(f"💥 Критическая ошибка: {str(e)}")
        logging.error(f"Критическая ошибка: {str(e)}")
    finally:
        if parser:
            parser.close()
            print("🔒 Браузер закрыт")

if __name__ == "__main__":
    run_inn_parser()
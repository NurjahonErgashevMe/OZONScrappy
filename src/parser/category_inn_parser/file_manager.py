import logging
import os
from datetime import datetime
from aiogram.types import FSInputFile

logger = logging.getLogger('parser.file_manager')

class FileManager:
    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
        
        # Создаем папку output если её нет
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def save_links_to_file(self, links, category_name):
        """Сохранение ссылок в файл"""
        try:
            filename = f"links_{category_name}.txt"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(links))
            
            logger.info(f"Ссылки сохранены в файл: {os.path.abspath(filepath)}")
            return filepath
        except Exception as e:
            logger.error(f"Ошибка сохранения ссылок: {str(e)}")
            return None

    def save_inn_to_txt(self, sellers_data, category_name):
        """Сохранение только ИНН в текстовый файл"""
        try:
            timestamp = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
            filename = f"{category_name}_inn_{timestamp}.txt"
            filepath = os.path.join(self.output_dir, filename)
            
            # Собираем уникальные ИНН
            inn_list = []
            for seller_name, data in sellers_data.items():
                # Пропускаем служебные данные
                if seller_name.startswith('_'):
                    continue
                    
                inn = data.get('inn', '')
                if inn and inn != 'Не найдено' and inn not in inn_list:
                    inn_list.append(inn)
            
            # Сохраняем в файл
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('\n'.join(inn_list))
            
            logger.info(f"Файл с ИНН сохранен: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Ошибка сохранения файла с ИНН: {str(e)}")
            return None

    async def send_file_to_user(self, bot, chat_id, filepath, caption):
        """Отправка файла пользователю"""
        try:
            if os.path.exists(filepath):
                file = FSInputFile(filepath)
                await bot.send_document(chat_id, file, caption=caption)
                logger.info(f"Файл отправлен пользователю: {filepath}")
            else:
                logger.error(f"Файл не найден: {filepath}")
        except Exception as e:
            logger.error(f"Ошибка отправки файла: {str(e)}")

    def cleanup_temp_files(self, filepaths):
        """Очистка временных файлов"""
        try:
            for filepath in filepaths:
                if filepath and os.path.exists(filepath):
                    os.remove(filepath)
                    logger.info(f"Временный файл удален: {filepath}")
        except Exception as e:
            logger.warning(f"Ошибка при удалении временных файлов: {str(e)}")

    def get_output_stats(self):
        """Получение статистики выходной папки"""
        try:
            if not os.path.exists(self.output_dir):
                return {"files_count": 0, "total_size": 0}
            
            files_count = 0
            total_size = 0
            
            for filename in os.listdir(self.output_dir):
                filepath = os.path.join(self.output_dir, filename)
                if os.path.isfile(filepath):
                    files_count += 1
                    total_size += os.path.getsize(filepath)
            
            return {
                "files_count": files_count,
                "total_size": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2)
            }
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {str(e)}")
            return {"files_count": 0, "total_size": 0}
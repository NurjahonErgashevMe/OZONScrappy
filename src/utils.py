import os
import sys
import logging

logger = logging.getLogger('utils')

def get_app_dir() -> str:
    """
    Возвращает путь к корневой директории проекта.
    Для PyInstaller — директория .exe, для скрипта — директория main.py.
    """
    if getattr(sys, 'frozen', False):
        app_dir = os.path.dirname(sys.executable)  # Корень для .exe
    else:
        # Поднимаемся на уровень выше, так как utils.py в src/
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logger.debug(f"Путь к директории приложения: {app_dir}")
    return app_dir

def get_config_path() -> str:
    """
    Возвращает полный путь к файлу config.txt в корневой директории.
    """
    config_path = os.path.join(get_app_dir(), "config.txt")
    logger.debug(f"Путь к файлу конфигурации: {config_path}")
    return config_path

def create_default_config(path: str = None) -> None:
    """
    Создаёт файл config.txt с пустыми значениями в корневой директории, если его нет.
    """
    if path is None:
        path = get_config_path()
    
    default_content = (
        "TELEGRAM_BOT_TOKEN=\n"
        "TELEGRAM_CHAT_ID=\n"
    )
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(default_content)
        logger.info(f"Создан шаблонный файл конфигурации: {path}")
    except Exception as e:
        logger.error(f"Ошибка при создании config.txt: {e}")

def load_config(config_path: str = None) -> dict:
    """
    Загружает конфигурацию из config.txt в корневой директории.
    Если файла нет, создаёт шаблонный файл и возвращает пустой словарь.
    """
    if config_path is None:
        config_path = get_config_path()
    
    logger.info(f"Загрузка конфигурации из {config_path}")
    
    if not os.path.exists(config_path):
        logger.warning(f"Файл конфигурации {config_path} не найден, создаётся шаблон")
        create_default_config(config_path)
        return {}

    config = {}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line and line.strip():
                    key, value = line.strip().split("=", 1)
                    config[key] = value
        logger.debug(f"Конфигурация загружена: {config}")
    except Exception as e:
        logger.error(f"Ошибка при загрузке конфигурации: {e}")
        return {}
    
    return config

def get_config_value(key: str, default: str = "") -> str:
    """
    Получает значение конфигурации по ключу.
    """
    config = load_config()
    value = config.get(key, default)
    logger.debug(f"Получено значение для ключа {key}: {value}")
    return value
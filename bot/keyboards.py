from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_keyboard():
    buttons = [
        [KeyboardButton(text="🔍 Парсинг продавца и товары")],
        [KeyboardButton(text="🆔 Парсинг ИНН продавцов")],
        [KeyboardButton(text="📦 Парсинг ИНН из товаров")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
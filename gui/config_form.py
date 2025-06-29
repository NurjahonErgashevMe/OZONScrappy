import tkinter as tk
from tkinter import messagebox
import os
import sys

def get_app_dir():
    """Возвращает путь к директории с запускаемым файлом"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def get_config_path():
    """Возвращает полный путь к файлу config.txt"""
    return os.path.join(get_app_dir(), "config.txt")

def show_config_form():
    """Показывает форму для настройки конфигурации"""
    
    def load_existing_config():
        """Загружает существующие настройки"""
        config_path = get_config_path()
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if "=" in line:
                            key, value = line.strip().split("=", 1)
                            if key == "TELEGRAM_BOT_TOKEN" and value:
                                token_entry.insert(0, value)
                            elif key == "TELEGRAM_CHAT_ID" and value:
                                chat_id_entry.insert(0, value)
            except:
                pass  # Игнорируем ошибки загрузки
    
    def save_config():
        """Сохраняет конфигурацию"""
        token = token_entry.get().strip()
        chat_id = chat_id_entry.get().strip()

        if not token or not chat_id:
            messagebox.showerror("Ошибка", "Пожалуйста, заполните оба поля.")
            return

        try:
            config_path = get_config_path()
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(f"TELEGRAM_BOT_TOKEN={token}\n")
                f.write(f"TELEGRAM_CHAT_ID={chat_id}\n")
            messagebox.showinfo("Успех", "Настройки сохранены!")
            root.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {e}")

    # Создание окна
    root = tk.Tk()
    root.title("Настройки Telegram бота")
    root.geometry("450x200")
    root.resizable(False, False)
    
    # Центрирование окна
    root.eval('tk::PlaceWindow . center')

    # Элементы интерфейса
    tk.Label(root, text="TELEGRAM_BOT_TOKEN:", font=('Arial', 10)).pack(pady=(20, 5))
    token_entry = tk.Entry(root, width=60, show="*")
    token_entry.pack(pady=(0, 10))

    tk.Label(root, text="TELEGRAM_CHAT_ID:", font=('Arial', 10)).pack(pady=(5, 5))
    chat_id_entry = tk.Entry(root, width=60)
    chat_id_entry.pack(pady=(0, 20))

    # Кнопки
    button_frame = tk.Frame(root)
    button_frame.pack(pady=10)
    
    save_btn = tk.Button(button_frame, text="Сохранить", command=save_config, 
                        bg="#4CAF50", fg="white", font=('Arial', 10, 'bold'))
    save_btn.pack(side=tk.LEFT, padx=(0, 10))
    
    cancel_btn = tk.Button(button_frame, text="Отмена", command=root.destroy,
                          bg="#f44336", fg="white", font=('Arial', 10))
    cancel_btn.pack(side=tk.LEFT)

    # Загрузка существующей конфигурации
    load_existing_config()

    root.mainloop()

if __name__ == "__main__":
    show_config_form()
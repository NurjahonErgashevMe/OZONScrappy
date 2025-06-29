import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext
import os
import sys
import threading
import logging
import asyncio
from datetime import datetime
from pathlib import Path
import queue
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from src.bot.register_handlers import register_handlers
from src.utils import load_config

class LogHandler(logging.Handler):
    """Кастомный обработчик логов для отображения в GUI"""
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue
    
    def emit(self, record):
        log_entry = self.format(record)
        self.log_queue.put(log_entry)

class TelegramBotApp:
    def __init__(self):
        self.root = tk.Tk()
        self.log_queue = queue.Queue()
        self.setup_logging()
        self.setup_ui()
        self.load_existing_config()
        
        # Переменные для бота
        self.bot = None
        self.dp = None
        self.bot_task = None
        self.bot_loop = None
        self.is_bot_running = False
        
        # Запуск обновления логов
        self.update_logs()
    
    def setup_logging(self):
        """Настройка системы логирования"""
        # Создаем корневой логгер
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        
        # Очищаем существующие обработчики
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Создаем форматтер
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Добавляем обработчик для GUI
        gui_handler = LogHandler(self.log_queue)
        gui_handler.setFormatter(formatter)
        self.logger.addHandler(gui_handler)
        
        # Добавляем обработчик для файла
        try:
            file_handler = logging.FileHandler('bot.log', encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        except:
            pass  # Игнорируем ошибки создания файла логов
    
    def get_app_dir(self):
        """Возвращает путь к директории с запускаемым файлом"""
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        else:
            return os.path.dirname(os.path.abspath(__file__))
    
    def get_config_path(self):
        """Возвращает полный путь к файлу config.txt"""
        return os.path.join(self.get_app_dir(), "config.txt")
    
    def setup_ui(self):
        """Настройка интерфейса"""
        self.root.title("Telegram Bot Manager")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # Центрирование окна
        self.root.eval('tk::PlaceWindow . center')
        
        # Создаем notebook для вкладок
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Вкладка настроек
        self.setup_config_tab(notebook)
        
        # Вкладка логов
        self.setup_logs_tab(notebook)
        
        # Вкладка управления ботом
        self.setup_control_tab(notebook)
        
        # Статус бар
        self.status_var = tk.StringVar()
        self.status_var.set("Готов к работе")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 10))
    
    def setup_config_tab(self, notebook):
        """Настройка вкладки конфигурации"""
        config_frame = ttk.Frame(notebook, padding="20")
        notebook.add(config_frame, text="Настройки")
        
        # Заголовок
        title_label = ttk.Label(config_frame, text="Настройки Telegram бота", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 30))
        
        # Поле для токена
        ttk.Label(config_frame, text="TELEGRAM_BOT_TOKEN:", 
                 font=('Arial', 12)).grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        self.token_entry = ttk.Entry(config_frame, width=70, show="*", font=('Arial', 10))
        self.token_entry.grid(row=2, column=0, columnspan=2, pady=(0, 20), sticky=(tk.W, tk.E))
        
        # Кнопка показать/скрыть токен
        self.show_token_var = tk.BooleanVar()
        show_token_cb = ttk.Checkbutton(config_frame, text="Показать токен", 
                                       variable=self.show_token_var, 
                                       command=self.toggle_token_visibility)
        show_token_cb.grid(row=3, column=0, sticky=tk.W, pady=(0, 15))
        
        # Поле для chat_id
        ttk.Label(config_frame, text="TELEGRAM_CHAT_ID:", 
                 font=('Arial', 12)).grid(row=4, column=0, sticky=tk.W, pady=(0, 5))
        self.chat_id_entry = ttk.Entry(config_frame, width=70, font=('Arial', 10))
        self.chat_id_entry.grid(row=5, column=0, columnspan=2, pady=(0, 25), sticky=(tk.W, tk.E))
        
        # Кнопки
        button_frame = ttk.Frame(config_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=15)
        
        save_btn = ttk.Button(button_frame, text="💾 Сохранить", command=self.save_config)
        save_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        test_btn = ttk.Button(button_frame, text="🔍 Проверить", command=self.test_config)
        test_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        clear_btn = ttk.Button(button_frame, text="🗑️ Очистить", command=self.clear_fields)
        clear_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        load_btn = ttk.Button(button_frame, text="📁 Загрузить", command=self.load_existing_config)
        load_btn.pack(side=tk.LEFT)
        
        # Информационное поле
        info_frame = ttk.LabelFrame(config_frame, text="📋 Как получить данные", padding="15")
        info_frame.grid(row=7, column=0, columnspan=2, pady=25, sticky=(tk.W, tk.E))
        
        info_text = """1. Создайте бота через @BotFather в Telegram:
   • Отправьте команду /newbot
   • Следуйте инструкциям и получите токен
   
2. Узнайте свой Chat ID:
   • Напишите боту @userinfobot
   • Или найдите свой ID через @getmyid_bot
   
3. Введите полученные данные в поля выше
4. Нажмите 'Сохранить' для сохранения настроек
5. Перейдите на вкладку 'Управление' для запуска бота"""
        
        info_label = ttk.Label(info_frame, text=info_text, justify=tk.LEFT, font=('Arial', 10))
        info_label.pack()
        
        # Настройка растягивания
        config_frame.columnconfigure(0, weight=1)
    
    def setup_logs_tab(self, notebook):
        """Настройка вкладки логов"""
        logs_frame = ttk.Frame(notebook, padding="10")
        notebook.add(logs_frame, text="Логи")
        
        # Заголовок
        ttk.Label(logs_frame, text="Логи работы приложения", 
                 font=('Arial', 14, 'bold')).pack(pady=(0, 10))
        
        # Кнопки управления логами
        log_buttons_frame = ttk.Frame(logs_frame)
        log_buttons_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(log_buttons_frame, text="🗑️ Очистить логи", 
                  command=self.clear_logs).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(log_buttons_frame, text="💾 Сохранить логи", 
                  command=self.save_logs).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(log_buttons_frame, text="🔄 Обновить", 
                  command=self.refresh_logs).pack(side=tk.LEFT)
        
        # Поле для отображения логов
        self.log_text = scrolledtext.ScrolledText(logs_frame, wrap=tk.WORD, 
                                                 font=('Consolas', 10), 
                                                 bg='#1e1e1e', fg='#ffffff',
                                                 insertbackground='white')
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Настройка цветов для разных уровней логов
        self.log_text.tag_config("INFO", foreground="#00ff00")
        self.log_text.tag_config("WARNING", foreground="#ffff00")
        self.log_text.tag_config("ERROR", foreground="#ff0000")
        self.log_text.tag_config("DEBUG", foreground="#00ffff")
    
    def setup_control_tab(self, notebook):
        """Настройка вкладки управления ботом"""
        control_frame = ttk.Frame(notebook, padding="20")
        notebook.add(control_frame, text="Управление")
        
        # Заголовок
        ttk.Label(control_frame, text="Управление Telegram ботом", 
                 font=('Arial', 16, 'bold')).pack(pady=(0, 30))
        
        # Статус бота
        status_frame = ttk.LabelFrame(control_frame, text="Статус бота", padding="15")
        status_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.bot_status_var = tk.StringVar()
        self.bot_status_var.set("🔴 Остановлен")
        ttk.Label(status_frame, textvariable=self.bot_status_var, 
                 font=('Arial', 14, 'bold')).pack()
        
        # Кнопки управления
        control_buttons_frame = ttk.Frame(control_frame)
        control_buttons_frame.pack(pady=20)
        
        self.start_btn = ttk.Button(control_buttons_frame, text="▶️ Запустить бота", 
                                   command=self.start_bot, state=tk.NORMAL)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        self.stop_btn = ttk.Button(control_buttons_frame, text="⏹️ Остановить бота", 
                                  command=self.stop_bot, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        self.restart_btn = ttk.Button(control_buttons_frame, text="🔄 Перезапустить", 
                                     command=self.restart_bot, state=tk.DISABLED)
        self.restart_btn.pack(side=tk.LEFT)
        
        # Информация о конфигурации
        config_info_frame = ttk.LabelFrame(control_frame, text="Информация о конфигурации", 
                                          padding="15")
        config_info_frame.pack(fill=tk.X, pady=20)
        
        self.config_info_var = tk.StringVar()
        self.config_info_var.set("Конфигурация не загружена")
        ttk.Label(config_info_frame, textvariable=self.config_info_var, 
                 font=('Arial', 10)).pack()
        
        # Обновляем информацию о конфигурации
        self.update_config_info()
    
    def toggle_token_visibility(self):
        """Переключает видимость токена"""
        if self.show_token_var.get():
            self.token_entry.config(show="")
        else:
            self.token_entry.config(show="*")
    
    def load_existing_config(self):
        """Загружает существующую конфигурацию"""
        config_path = self.get_config_path()
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if "=" in line:
                            key, value = line.strip().split("=", 1)
                            if key == "TELEGRAM_BOT_TOKEN" and value:
                                self.token_entry.delete(0, tk.END)
                                self.token_entry.insert(0, value)
                            elif key == "TELEGRAM_CHAT_ID" and value:
                                self.chat_id_entry.delete(0, tk.END)
                                self.chat_id_entry.insert(0, value)
                self.status_var.set("Конфигурация загружена")
                self.update_config_info()
                self.logger.info("Конфигурация успешно загружена")
            except Exception as e:
                self.status_var.set(f"Ошибка загрузки: {e}")
                self.logger.error(f"Ошибка загрузки конфигурации: {e}")
    
    def save_config(self):
        """Сохраняет конфигурацию"""
        token = self.token_entry.get().strip()
        chat_id = self.chat_id_entry.get().strip()
        
        if not token or not chat_id:
            messagebox.showerror("Ошибка", "Пожалуйста, заполните оба поля.")
            self.logger.warning("Попытка сохранения пустой конфигурации")
            return
        
        try:
            config_path = self.get_config_path()
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(f"TELEGRAM_BOT_TOKEN={token}\n")
                f.write(f"TELEGRAM_CHAT_ID={chat_id}\n")
            
            messagebox.showinfo("Успех", f"Настройки сохранены!")
            self.status_var.set("Конфигурация сохранена")
            self.update_config_info()
            self.logger.info("Конфигурация успешно сохранена")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {e}")
            self.status_var.set("Ошибка сохранения")
            self.logger.error(f"Ошибка сохранения конфигурации: {e}")
    
    def test_config(self):
        """Проверяет корректность введенных данных"""
        token = self.token_entry.get().strip()
        chat_id = self.chat_id_entry.get().strip()
        
        if not token or not chat_id:
            messagebox.showwarning("Предупреждение", "Заполните оба поля для проверки.")
            return
        
        issues = []
        
        # Проверка токена
        if ':' not in token:
            issues.append("Токен должен содержать символ ':'")
        
        if len(token) < 35:
            issues.append("Токен слишком короткий")
        
        # Проверка chat_id
        if not chat_id.lstrip('-').isdigit():
            issues.append("Chat ID должен быть числом (может начинаться с '-')")
        
        if issues:
            messagebox.showwarning("Проблемы с конфигурацией", "\n".join(issues))
            self.logger.warning(f"Проблемы с конфигурацией: {', '.join(issues)}")
        else:
            messagebox.showinfo("Проверка", "Базовая проверка формата пройдена!")
            self.logger.info("Конфигурация прошла базовую проверку")
        
        self.status_var.set("Проверка завершена")
    
    def clear_fields(self):
        """Очищает поля ввода"""
        self.token_entry.delete(0, tk.END)
        self.chat_id_entry.delete(0, tk.END)
        self.status_var.set("Поля очищены")
        self.update_config_info()
        self.logger.info("Поля конфигурации очищены")
    
    def update_config_info(self):
        """Обновляет информацию о конфигурации"""
        config_path = self.get_config_path()
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    token_set = any(line.startswith("TELEGRAM_BOT_TOKEN=") and len(line.strip()) > len("TELEGRAM_BOT_TOKEN=") for line in lines)
                    chat_id_set = any(line.startswith("TELEGRAM_CHAT_ID=") and len(line.strip()) > len("TELEGRAM_CHAT_ID=") for line in lines)
                    
                    if token_set and chat_id_set:
                        self.config_info_var.set("✅ Конфигурация настроена и готова к использованию")
                    else:
                        missing = []
                        if not token_set:
                            missing.append("токен")
                        if not chat_id_set:
                            missing.append("chat_id")
                        self.config_info_var.set(f"⚠️ Отсутствует: {', '.join(missing)}")
            except:
                self.config_info_var.set("❌ Ошибка чтения конфигурации")
        else:
            self.config_info_var.set("❌ Файл конфигурации не найден")

    async def run_bot_async(self):
        """Асинхронный запуск бота"""
        try:
            # Загружаем конфигурацию
            config = load_config(self.get_config_path())
            token = config["TELEGRAM_BOT_TOKEN"]
            
            # Создаем бота и диспетчер
            self.bot = Bot(
                token=token
            )
            self.dp = Dispatcher()
            
            # Регистрируем обработчики
            register_handlers(self.dp, self.bot)
            
            self.logger.info("Telegram бот инициализирован")
            
            # Запускаем polling
            await self.dp.start_polling(self.bot)
            
        except Exception as e:
            self.logger.error(f"Ошибка при запуске бота: {e}")
            # Обновляем UI в основном потоке
            self.root.after(0, self._bot_error_callback, str(e))

    def _bot_error_callback(self, error_msg):
        """Callback для обработки ошибок бота в главном потоке"""
        self.is_bot_running = False
        self.bot_status_var.set("❌ Ошибка")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.restart_btn.config(state=tk.DISABLED)
        self.status_var.set(f"Ошибка бота: {error_msg}")

    def start_bot_thread(self):
        """Запуск бота в отдельном потоке"""
        def run_bot():
            # Создаем новый event loop для этого потока
            self.bot_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.bot_loop)
            
            try:
                # Запускаем бота
                self.bot_loop.run_until_complete(self.run_bot_async())
            except Exception as e:
                self.logger.error(f"Ошибка в потоке бота: {e}")
            finally:
                self.bot_loop.close()
        
        # Запускаем в отдельном потоке
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
    
    def start_bot(self):
        """Запускает бота"""
        self.logger.info("Попытка запуска бота...")
        
        # Проверяем конфигурацию
        config_path = self.get_config_path()
        if not os.path.exists(config_path):
            messagebox.showerror("Ошибка", "Сначала настройте конфигурацию!")
            return
        
        try:
            # Проверяем, что конфигурация корректна
            config = load_config(config_path)
            if not config.get("TELEGRAM_BOT_TOKEN") or not config.get("TELEGRAM_CHAT_ID"):
                messagebox.showerror("Ошибка", "Некорректная конфигурация!")
                return
            
            # Обновляем UI
            self.is_bot_running = True
            self.bot_status_var.set("🟡 Запускается...")
            self.start_btn.config(state=tk.DISABLED)
            self.status_var.set("Запуск бота...")
            
            # Запускаем бота в отдельном потоке
            self.start_bot_thread()
            
            # Даем немного времени на запуск и обновляем статус
            self.root.after(2000, self._update_bot_started_status)
            
        except Exception as e:
            self.logger.error(f"Ошибка при запуске бота: {e}")
            messagebox.showerror("Ошибка", f"Не удалось запустить бота: {e}")
            self.is_bot_running = False
            self.bot_status_var.set("🔴 Остановлен")
            self.start_btn.config(state=tk.NORMAL)

    def _update_bot_started_status(self):
        """Обновляет статус после запуска бота"""
        if self.is_bot_running:
            self.bot_status_var.set("🟢 Запущен")
            self.stop_btn.config(state=tk.NORMAL)
            self.restart_btn.config(state=tk.NORMAL)
            self.status_var.set("Бот запущен и готов к работе")
            self.logger.info("Бот успешно запущен и готов к работе")
    
    def stop_bot(self):
        """Останавливает бота"""
        self.logger.info("Остановка бота...")
        
        try:
            self.is_bot_running = False
            
            # Останавливаем бота если он существует
            if self.bot_loop and not self.bot_loop.is_closed():
                # Планируем остановку в event loop бота
                asyncio.run_coroutine_threadsafe(self._stop_bot_async(), self.bot_loop)
                
                # Даем время на корректное завершение
                self.root.after(1000, self._update_bot_stopped_status)
            else:
                self._update_bot_stopped_status()
                
        except Exception as e:
            self.logger.error(f"Ошибка при остановке бота: {e}")
            self._update_bot_stopped_status()

    async def _stop_bot_async(self):
        """Асинхронная остановка бота"""
        try:
            if self.bot:
                await self.bot.session.close()
                self.logger.info("Сессия бота закрыта")
        except Exception as e:
            self.logger.error(f"Ошибка при закрытии сессии бота: {e}")

    def _update_bot_stopped_status(self):
        """Обновляет UI после остановки бота"""
        self.bot_status_var.set("🔴 Остановлен")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.restart_btn.config(state=tk.DISABLED)
        self.status_var.set("Бот остановлен")
        self.logger.info("Бот остановлен")
    
    def restart_bot(self):
        """Перезапускает бота"""
        self.logger.info("Перезапуск бота...")
        self.stop_bot()
        self.root.after(2000, self.start_bot)  # Запуск через 2 секунды
    
    def clear_logs(self):
        """Очищает логи"""
        self.log_text.delete(1.0, tk.END)
        self.logger.info("Логи очищены")
    
    def save_logs(self):
        """Сохраняет логи в файл"""
        try:
            logs_content = self.log_text.get(1.0, tk.END)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"logs_{timestamp}.txt"
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(logs_content)
            
            messagebox.showinfo("Успех", f"Логи сохранены в файл: {filename}")
            self.logger.info(f"Логи сохранены в файл: {filename}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить логи: {e}")
            self.logger.error(f"Ошибка сохранения логов: {e}")
    
    def refresh_logs(self):
        """Обновляет отображение логов"""
        self.logger.info("Обновление логов...")
    
    def update_logs(self):
        """Обновляет логи в GUI"""
        try:
            while True:
                try:
                    log_entry = self.log_queue.get_nowait()
                    
                    # Определяем уровень лога для раскраски
                    tag = "INFO"
                    if "WARNING" in log_entry:
                        tag = "WARNING"
                    elif "ERROR" in log_entry:
                        tag = "ERROR"
                    elif "DEBUG" in log_entry:
                        tag = "DEBUG"
                    
                    # Добавляем запись в текстовое поле
                    self.log_text.insert(tk.END, log_entry + "\n", tag)
                    self.log_text.see(tk.END)
                    
                    # Ограничиваем количество строк (оставляем последние 1000)
                    lines = int(self.log_text.index('end-1c').split('.')[0])
                    if lines > 1000:
                        self.log_text.delete(1.0, f"{lines-1000}.0")
                        
                except queue.Empty:
                    break
        except:
            pass
        
        # Планируем следующее обновление
        self.root.after(100, self.update_logs)
    
    def run(self):
        """Запуск приложения"""
        self.logger.info("Приложение запущено")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        """Обработка закрытия приложения"""
        if self.is_bot_running:
            if messagebox.askokcancel("Выход", "Бот все еще работает. Остановить его и выйти?"):
                self.stop_bot()
                # Даем время на остановку бота
                self.root.after(1500, self.root.destroy)
        else:
            self.logger.info("Приложение закрыто")
            self.root.destroy()

if __name__ == "__main__":
    app = TelegramBotApp()
    app.run()
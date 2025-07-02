import os
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import webbrowser

class TabManager:
    def setup_ui(self):
        self.root.title("Telegram Bot Manager")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        self.root.eval('tk::PlaceWindow . center')
        
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.setup_config_tab(notebook)
        self.setup_logs_tab(notebook)
        self.setup_control_tab(notebook)
        self.setup_developer_tab(notebook)
        
        self.status_var = tk.StringVar()
        self.status_var.set("Готов к работе")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 10))
    
    def setup_config_tab(self, notebook):
        """Настройка вкладки конфигурации"""
        config_frame = ttk.Frame(notebook, padding="20")
        notebook.add(config_frame, text="Настройки")
        
        title_label = ttk.Label(config_frame, text="Настройки Telegram бота", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 30))
        
        ttk.Label(config_frame, text="TELEGRAM_BOT_TOKEN:", 
                 font=('Arial', 12)).grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        self.token_entry = ttk.Entry(config_frame, width=70, show="*", font=('Arial', 10))
        self.token_entry.grid(row=2, column=0, columnspan=2, pady=(0, 20), sticky=(tk.W, tk.E))
        
        self.show_token_var = tk.BooleanVar()
        show_token_cb = ttk.Checkbutton(config_frame, text="Показать токен", 
                                       variable=self.show_token_var, 
                                       command=self.toggle_token_visibility)
        show_token_cb.grid(row=3, column=0, sticky=tk.W, pady=(0, 15))
        
        ttk.Label(config_frame, text="TELEGRAM_CHAT_ID:", 
                 font=('Arial', 12)).grid(row=4, column=0, sticky=tk.W, pady=(0, 5))
        self.chat_id_entry = ttk.Entry(config_frame, width=70, font=('Arial', 10))
        self.chat_id_entry.grid(row=5, column=0, columnspan=2, pady=(0, 25), sticky=(tk.W, tk.E))
        
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
        
        config_frame.columnconfigure(0, weight=1)
    
    def setup_logs_tab(self, notebook):
        """Настройка вкладки логов"""
        logs_frame = ttk.Frame(notebook, padding="10")
        notebook.add(logs_frame, text="Логи")
        
        ttk.Label(logs_frame, text="Логи работы приложения", 
                 font=('Arial', 14, 'bold')).pack(pady=(0, 10))
        
        log_buttons_frame = ttk.Frame(logs_frame)
        log_buttons_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(log_buttons_frame, text="🗑️ Очистить логи", 
                  command=self.clear_logs).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(log_buttons_frame, text="💾 Сохранить логи", 
                  command=self.save_logs).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(log_buttons_frame, text="🔄 Обновить", 
                  command=self.refresh_logs).pack(side=tk.LEFT)
        
        self.log_text = scrolledtext.ScrolledText(logs_frame, wrap=tk.WORD, 
                                                 font=('Consolas', 10), 
                                                 bg='#1e1e1e', fg='#ffffff',
                                                 insertbackground='white')
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        self.log_text.tag_config("INFO", foreground="#00ff00")
        self.log_text.tag_config("WARNING", foreground="#ffff00")
        self.log_text.tag_config("ERROR", foreground="#ff0000")
        self.log_text.tag_config("DEBUG", foreground="#00ffff")
    
    def setup_control_tab(self, notebook):
        """Настройка вкладки управления ботом"""
        control_frame = ttk.Frame(notebook, padding="20")
        notebook.add(control_frame, text="Управление")
        
        # Создаем прокручиваемый фрейм
        canvas = tk.Canvas(control_frame)
        scrollbar = ttk.Scrollbar(control_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Привязываем скроллинг к колесу мыши
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Настраиваем ширину прокручиваемого контента
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Устанавливаем ширину прокручиваемого фрейма равной ширине canvas
            canvas_width = event.width
            canvas.itemconfig(canvas.create_window((0, 0), window=scrollable_frame, anchor="nw"), width=canvas_width)
        
        canvas.bind('<Configure>', configure_scroll_region)
        
        # Заголовок
        ttk.Label(scrollable_frame, text="Управление Telegram ботом", 
                 font=('Arial', 16, 'bold')).pack(pady=(0, 30))
        
        # Секция статуса бота
        status_frame = ttk.LabelFrame(scrollable_frame, text="Статус бота", padding="15")
        status_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.bot_status_var = tk.StringVar()
        self.bot_status_var.set("🔴 Остановлен")
        ttk.Label(status_frame, textvariable=self.bot_status_var, 
                 font=('Arial', 14, 'bold')).pack()
        
        # Кнопки управления ботом
        control_buttons_frame = ttk.Frame(scrollable_frame)
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
        
        # Новая секция настроек парсера
        parser_settings_frame = ttk.LabelFrame(scrollable_frame, text="⚙️ Настройки парсера категорий", 
                                              padding="20")
        parser_settings_frame.pack(fill=tk.X, pady=20)
        
        # Первая строка настроек
        settings_row1 = ttk.Frame(parser_settings_frame)
        settings_row1.pack(fill=tk.X, pady=(0, 15))
        
        # Общее количество ссылок
        ttk.Label(settings_row1, text="Количество товаров:", 
                 font=('Arial', 11)).pack(side=tk.LEFT)
        self.max_sellers_var = tk.StringVar(value="150")
        max_sellers_entry = ttk.Entry(settings_row1, textvariable=self.max_sellers_var, 
                                     width=10, font=('Arial', 10))
        max_sellers_entry.pack(side=tk.LEFT, padx=(10, 20))
        
        # Количество воркеров
        # ttk.Label(settings_row1, text="Воркеры:", 
        #          font=('Arial', 11)).pack(side=tk.LEFT)
        # self.workers_var = tk.StringVar(value="3")
        # workers_entry = ttk.Entry(settings_row1, textvariable=self.workers_var, 
        #                          width=10, font=('Arial', 10))
        # workers_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # Вторая строка настроек
        settings_row2 = ttk.Frame(parser_settings_frame)
        settings_row2.pack(fill=tk.X, pady=(0, 15))
        
        # Максимальное количество холостых скроллов
        # ttk.Label(settings_row2, text="Макс. холостых скроллов:", 
        #          font=('Arial', 11)).pack(side=tk.LEFT)
        # self.max_idle_scrolls_var = tk.StringVar(value="100")
        # idle_scrolls_entry = ttk.Entry(settings_row2, textvariable=self.max_idle_scrolls_var, 
        #                               width=10, font=('Arial', 10))
        # idle_scrolls_entry.pack(side=tk.LEFT, padx=(10, 20))
        
        # Задержка скролла
        ttk.Label(settings_row2, text="Задержка скролла (сек):", 
                 font=('Arial', 11)).pack(side=tk.LEFT)
        self.scroll_delay_var = tk.StringVar(value="2.0")
        scroll_delay_entry = ttk.Entry(settings_row2, textvariable=self.scroll_delay_var, 
                                      width=10, font=('Arial', 10))
        scroll_delay_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # Третья строка настроек
        settings_row3 = ttk.Frame(parser_settings_frame)
        settings_row3.pack(fill=tk.X, pady=(0, 15))
        
        # Таймаут загрузки
        ttk.Label(settings_row3, text="Таймаут загрузки (сек):", 
                 font=('Arial', 11)).pack(side=tk.LEFT)
        self.load_timeout_var = tk.StringVar(value="30")
        load_timeout_entry = ttk.Entry(settings_row3, textvariable=self.load_timeout_var, 
                                      width=10, font=('Arial', 10))
        load_timeout_entry.pack(side=tk.LEFT, padx=(10, 20))
        
        # Режим браузера (исправленная логика)
        # ttk.Label(settings_row3, text="Скрытый режим браузера:", 
        #          font=('Arial', 11)).pack(side=tk.LEFT)
        # self.headless_var = tk.BooleanVar(value=False)  # False = показывать браузер
        # headless_cb = ttk.Checkbutton(settings_row3, variable=self.headless_var)
        # headless_cb.pack(side=tk.LEFT, padx=(10, 0))
        
        # Кнопки управления настройками парсера
        parser_buttons_frame = ttk.Frame(parser_settings_frame)
        parser_buttons_frame.pack(pady=(15, 0))
        
        save_parser_btn = ttk.Button(parser_buttons_frame, text="💾 Сохранить настройки", 
                                    command=self.save_parser_settings)
        save_parser_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        load_parser_btn = ttk.Button(parser_buttons_frame, text="📁 Загрузить настройки", 
                                    command=self.load_parser_settings)
        load_parser_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        reset_parser_btn = ttk.Button(parser_buttons_frame, text="🔄 Сбросить", 
                                     command=self.reset_parser_settings)
        reset_parser_btn.pack(side=tk.LEFT)
        
        # Справочная информация
        parser_info_frame = ttk.LabelFrame(parser_settings_frame, text="📋 Описание настроек", 
                                          padding="10")
        parser_info_frame.pack(fill=tk.X, pady=(20, 0))
        
        info_text = """• Количество товаров - максимальное количество ссылок для сбора
• Воркеры - количество параллельных потоков для парсинга ИНН (рекомендуется 3-5)
• Макс. холостых скроллов - сколько скроллов без новых товаров перед остановкой
• Задержка скролла - пауза между скроллами в секундах (для имитации человека)
• Таймаут загрузки - время ожидания загрузки страницы в секундах
• Скрытый режим браузера - если включен, браузер запускается скрыто (--headless)"""
        
        info_label = ttk.Label(parser_info_frame, text=info_text, justify=tk.LEFT, 
                              font=('Arial', 9), wraplength=750)
        info_label.pack(anchor=tk.W)
        
        # Информация о конфигурации
        config_info_frame = ttk.LabelFrame(scrollable_frame, text="Информация о конфигурации", 
                                          padding="15")
        config_info_frame.pack(fill=tk.X, pady=20)
        
        self.config_info_var = tk.StringVar()
        self.config_info_var.set("Конфигурация не загружена")
        ttk.Label(config_info_frame, textvariable=self.config_info_var, 
                 font=('Arial', 10)).pack()
        
        self.update_config_info()
        
        # Загружаем настройки парсера при инициализации
        self.load_parser_settings()
    
    def setup_developer_tab(self, notebook):
        """Настройка вкладки разработчика"""
        dev_frame = ttk.Frame(notebook, padding="20")
        notebook.add(dev_frame, text="Разработчик")
        
        title_label = ttk.Label(dev_frame, text="Информация о разработчике", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 30))
        
        info_frame = ttk.LabelFrame(dev_frame, text="Контакты и ссылки", padding="20")
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        link_style = ttk.Style()
        link_style.configure("Link.TLabel", foreground="blue", font=('Arial', 12, 'underline'))
        
        ttk.Label(info_frame, text="Telegram:", font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        telegram_link = ttk.Label(info_frame, text="@NurjahonErgashevMe", style="Link.TLabel", cursor="hand2")
        telegram_link.pack(anchor=tk.W, padx=20, pady=(0, 20))
        telegram_link.bind("<Button-1>", lambda e: webbrowser.open("https://t.me/NurjahonErgashevMe"))
        
        ttk.Label(info_frame, text="Kwork:", font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        kwork_link = ttk.Label(info_frame, text="https://kwork.ru/user/nurjahonergashevme", 
                              style="Link.TLabel", cursor="hand2")
        kwork_link.pack(anchor=tk.W, padx=20, pady=(0, 20))
        kwork_link.bind("<Button-1>", lambda e: webbrowser.open("https://kwork.ru/user/nurjahonergashevme"))
        
        ttk.Label(info_frame, text="Приложение:", font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        ttk.Label(info_frame, text="Telegram Bot Manager v1.0", font=('Arial', 11)).pack(anchor=tk.W, padx=20)
        ttk.Label(info_frame, text="© 2026 Nurjahon Ergashev", font=('Arial', 11)).pack(anchor=tk.W, padx=20, pady=(0, 20))
        
        logo_frame = ttk.Frame(dev_frame)
        logo_frame.pack(pady=20)
        ttk.Label(logo_frame, text="[ЛОГОТИП]", font=('Arial', 24), 
                 foreground="gray", borderwidth=2, relief="solid", 
                 width=15).pack()
    
    def save_parser_settings(self):
        """Сохранение настроек парсера в конфигурационный файл"""
        try:
            # Валидация значений
            try:
                max_sellers = int(self.max_sellers_var.get())
                # workers = int(self.workers_var.get())
                # max_idle_scrolls = int(self.max_idle_scrolls_var.get())
                scroll_delay = float(self.scroll_delay_var.get())
                load_timeout = int(self.load_timeout_var.get())
                
                # if max_sellers <= 0 or workers <= 0 or max_idle_scrolls <= 0 or scroll_delay < 0 or load_timeout <= 0:
                #     raise ValueError("Значения должны быть положительными")
                    
            except ValueError as e:
                messagebox.showerror("Ошибка", f"Некорректные значения настроек: {e}")
                return
            
            # Читаем существующий конфиг
            config_lines = []
            config_file = "config.txt"
            
            if os.path.exists(config_file):
                with open(config_file, "r", encoding="utf-8") as f:
                    config_lines = f.readlines()
            
            # Обновляем или добавляем настройки парсера
            parser_settings = {
                "MAX_SELLERS": str(max_sellers),
                # "WORKERS_COUNT": str(workers),
                # "MAX_IDLE_SCROLLS": str(max_idle_scrolls),
                "SCROLL_DELAY": str(scroll_delay),
                "LOAD_TIMEOUT": str(load_timeout),
                # "HEADLESS": "False" if self.headless_var.get() else "True"
            }
            
            # Обновляем существующие настройки или добавляем новые
            updated_lines = []
            updated_keys = set()
            
            for line in config_lines:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key = line.split('=')[0].strip()
                    if key in parser_settings:
                        updated_lines.append(f"{key}={parser_settings[key]}\n")
                        updated_keys.add(key)
                    else:
                        updated_lines.append(line + "\n")
                else:
                    updated_lines.append(line + "\n")
            
            # Добавляем новые настройки, которых не было в файле
            if not updated_keys:  # Если секции парсера не было
                updated_lines.append("\n# Настройки парсера категорий\n")
            
            for key, value in parser_settings.items():
                if key not in updated_keys:
                    updated_lines.append(f"{key}={value}\n")
            
            # Сохраняем конфиг
            with open(config_file, "w", encoding="utf-8") as f:
                f.writelines(updated_lines)
            
            messagebox.showinfo("Успех", "Настройки парсера сохранены!")
            self.status_var.set("Настройки парсера сохранены")
            if hasattr(self, 'logger'):
                self.logger.info("Настройки парсера сохранены в config.txt")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить настройки: {e}")
            if hasattr(self, 'logger'):
                self.logger.error(f"Ошибка сохранения настроек парсера: {e}")
    
    def load_parser_settings(self):
        """Загрузка настроек парсера из конфигурационного файла"""
        try:
            config_file = "config.txt"
            if not os.path.exists(config_file):
                return
            
            with open(config_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        if key == "MAX_SELLERS":
                            self.max_sellers_var.set(value)
                        # elif key == "WORKERS_COUNT":
                        #     self.workers_var.set(value)
                        # elif key == "MAX_IDLE_SCROLLS":
                        #     self.max_idle_scrolls_var.set(value)
                        elif key == "SCROLL_DELAY":
                            self.scroll_delay_var.set(value)
                        elif key == "LOAD_TIMEOUT":
                            self.load_timeout_var.set(value)
                        # elif key == "HEADLESS":
                        #     self.headless_var.set(value.lower() == "false")
            
            if hasattr(self, 'logger'):
                self.logger.info("Настройки парсера загружены из config.txt")
                
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.warning(f"Не удалось загрузить настройки парсера: {e}")
    
    def reset_parser_settings(self):
        """Сброс настроек парсера к значениям по умолчанию"""
        self.max_sellers_var.set("150")
        # self.workers_var.set("3")
        # self.max_idle_scrolls_var.set("100")
        self.scroll_delay_var.set("2.0")
        self.load_timeout_var.set("30")
        # self.headless_var.set(False)
        
        self.status_var.set("Настройки парсера сброшены к значениям по умолчанию")
        if hasattr(self, 'logger'):
            self.logger.info("Настройки парсера сброшены к значениям по умолчанию")
    
    def clear_fields(self):
        self.token_entry.delete(0, tk.END)
        self.chat_id_entry.delete(0, tk.END)
        self.status_var.set("Поля очищены")
        self.update_config_info()
        if hasattr(self, 'logger'):
            self.logger.info("Поля конфигурации очищены")
    
    def save_logs(self):
        try:
            logs_content = self.log_text.get(1.0, tk.END)
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"logs_{timestamp}.txt"
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(logs_content)
            
            messagebox.showinfo("Успех", f"Логи сохранены в файл: {filename}")
            if hasattr(self, 'logger'):
                self.logger.info(f"Логи сохранены в файл: {filename}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить логи: {e}")
            if hasattr(self, 'logger'):
                self.logger.error(f"Ошибка сохранения логов: {e}")
    
    def refresh_logs(self):
        if hasattr(self, 'logger'):
            self.logger.info("Обновление логов...")
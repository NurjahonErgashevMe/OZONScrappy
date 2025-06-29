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
        
        ttk.Label(control_frame, text="Управление Telegram ботом", 
                 font=('Arial', 16, 'bold')).pack(pady=(0, 30))
        
        status_frame = ttk.LabelFrame(control_frame, text="Статус бота", padding="15")
        status_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.bot_status_var = tk.StringVar()
        self.bot_status_var.set("🔴 Остановлен")
        ttk.Label(status_frame, textvariable=self.bot_status_var, 
                 font=('Arial', 14, 'bold')).pack()
        
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
        
        config_info_frame = ttk.LabelFrame(control_frame, text="Информация о конфигурации", 
                                          padding="15")
        config_info_frame.pack(fill=tk.X, pady=20)
        
        self.config_info_var = tk.StringVar()
        self.config_info_var.set("Конфигурация не загружена")
        ttk.Label(config_info_frame, textvariable=self.config_info_var, 
                 font=('Arial', 10)).pack()
        
        self.update_config_info()
    
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
    
    def clear_fields(self):
        self.token_entry.delete(0, tk.END)
        self.chat_id_entry.delete(0, tk.END)
        self.status_var.set("Поля очищены")
        self.update_config_info()
        self.logger.info("Поля конфигурации очищены")
    
    def save_logs(self):
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
        self.logger.info("Обновление логов...")
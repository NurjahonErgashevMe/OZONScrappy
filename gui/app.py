import tkinter as tk
import queue
from .config import ConfigManager
from .bot import BotManager
from .logs import LogManager
from .tabs import TabManager
from .utils import Utils

class TelegramBotApp(ConfigManager, BotManager, LogManager, TabManager, Utils):
    def __init__(self):
        self.root = tk.Tk()
        self.log_queue = queue.Queue()
        self.setup_logging()
        self.setup_ui()
        self.load_existing_config()
        
        self.bot = None
        self.dp = None
        self.bot_task = None
        self.bot_loop = None
        self.is_bot_running = False
        
        self.update_logs()
    
    def run(self):
        self.logger.info("Приложение запущено")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
        
    def on_closing(self):
        if self.is_bot_running:
            if tk.messagebox.askokcancel("Выход", "Бот все еще работает. Остановить его и выйти?"):
                self.stop_bot()
                self.root.after(1500, self.root.destroy)
        else:
            self.logger.info("Приложение закрыто")
            self.root.destroy()
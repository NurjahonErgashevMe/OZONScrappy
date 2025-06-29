import logging
from datetime import datetime
import queue

import tkinter as tk

class LogHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue
    
    def emit(self, record):
        log_entry = self.format(record)
        self.log_queue.put(log_entry)

class LogManager:
    def setup_logging(self):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        gui_handler = LogHandler(self.log_queue)
        gui_handler.setFormatter(formatter)
        self.logger.addHandler(gui_handler)
        
        try:
            file_handler = logging.FileHandler('bot.log', encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        except:
            pass
    
    def update_logs(self):
        try:
            while True:
                try:
                    log_entry = self.log_queue.get_nowait()
                    tag = "INFO"
                    if "WARNING" in log_entry: tag = "WARNING"
                    elif "ERROR" in log_entry: tag = "ERROR"
                    elif "DEBUG" in log_entry: tag = "DEBUG"
                    
                    self.log_text.insert(tk.END, log_entry + "\n", tag)
                    self.log_text.see(tk.END)
                    
                    lines = int(self.log_text.index('end-1c').split('.')[0])
                    if lines > 1000:
                        self.log_text.delete(1.0, f"{lines-1000}.0")
                except queue.Empty:
                    break
        except:
            pass
        self.root.after(100, self.update_logs)
    
    def clear_logs(self):
        self.log_text.delete(1.0, tk.END)
        self.logger.info("Логи очищены")
import logging
import queue
import threading
import time

class CentralLogger:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.log_queue = queue.Queue()
                cls._instance.setup_logger()
            return cls._instance
    
    def setup_logger(self):
        self.logger = logging.getLogger('central')
        self.logger.setLevel(logging.INFO)
        
        # Консольный хендлер для отладки
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))
        self.logger.addHandler(console_handler)
    
    def log(self, level, message):
        """Основной метод логирования"""
        if self.log_queue.qsize() > 1000:  # Ограничение очереди
            self.log_queue.get_nowait()  # Удаляем старые сообщения
        
        log_entry = {
            'level': level,
            'message': message,
            'timestamp': time.time()
        }
        self.log_queue.put(log_entry)
        self.logger.log(level, message)
    
    def debug(self, message):
        self.log(logging.DEBUG, message)
    
    def info(self, message):
        self.log(logging.INFO, message)
    
    def warning(self, message):
        self.log(logging.WARNING, message)
    
    def error(self, message):
        self.log(logging.ERROR, message)
    
    def critical(self, message):
        self.log(logging.CRITICAL, message)

# Синглтон-экземпляр
central_logger = CentralLogger()
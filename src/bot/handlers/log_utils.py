import logging
import asyncio
import time

logger = logging.getLogger('bot.log_utils')

class LogUpdater:
    def __init__(self, bot, chat_id, message_id=None):
        self.bot = bot
        self.chat_id = chat_id
        self.message_id = message_id
        self.log_buffer = []
        self.buffer_size = 15
        self.max_message_length = 4000
        self.last_update_time = 0
        self.update_interval = 2.0
        self.too_many_requests_count = 0

    async def init(self):
        """Создает начальное сообщение для логов"""
        if not self.message_id:
            msg = await self.bot.send_message(
                self.chat_id,
                "<pre>🔄 Инициализация логов...</pre>",
                parse_mode="HTML"
            )
            self.message_id = msg.message_id

    async def add_log(self, log_entry):
        """Добавляет запись в лог и обновляет сообщение"""
        # Упрощаем лог (убираем временные метки)
        clean_log = log_entry.split(" - ", 3)[-1] if " - " in log_entry else log_entry
        
        # Обработка разделителей - очистка буфера
        if "====" in clean_log or "▬▬▬" in clean_log:
            self.log_buffer = []
        
        self.log_buffer.append(clean_log)
        
        # Ограничение размера буфера
        if len(self.log_buffer) > self.buffer_size:
            self.log_buffer.pop(0)
        
        # Формируем текст
        log_text = "\n".join(self.log_buffer)
        
        # Обрезаем до лимита Telegram
        if len(log_text) > self.max_message_length:
            log_text = log_text[-self.max_message_length:]
        
        # Обновляем сообщение с защитой от Too Many Requests
        await self._safe_update(log_text)

    async def _safe_update(self, log_text):
        """Безопасное обновление сообщения с обработкой ошибок"""
        current_time = time.time()
        if current_time - self.last_update_time < self.update_interval:
            return
            
        try:
            await self.bot.edit_message_text(
                chat_id=self.chat_id,
                message_id=self.message_id,
                text=f"<pre>{log_text}</pre>",
                parse_mode="HTML"
            )
            self.last_update_time = current_time
            self.too_many_requests_count = 0
        except Exception as e:
            if "Too Many Requests" in str(e):
                self.too_many_requests_count += 1
                self.update_interval = min(10.0, 2.0 + self.too_many_requests_count)
                await asyncio.sleep(5)
            else:
                logger.error(f"Ошибка обновления логов: {str(e)}")

    async def final_message(self, message):
        """Отправляет финальное сообщение"""
        try:
            await self.bot.edit_message_text(
                chat_id=self.chat_id,
                message_id=self.message_id,
                text=f"<pre>{message}</pre>",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Ошибка отправки финального сообщения: {str(e)}")
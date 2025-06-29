import asyncio
import logging
import time
import re
import html
from .central_logger import central_logger

class TelegramLogsHandler:
    def __init__(self, bot, chat_id):
        self.bot = bot
        self.chat_id = chat_id
        self.message_id = None
        self.is_running = True
        self.log_buffer = []
        self.buffer_size = 15
        self.max_message_length = 4090  # Telegram limit is 4096 chars
        self.last_update_time = 0
        self.update_interval = 2.0
        self.too_many_requests_count = 0
        self.task = asyncio.create_task(self.process_logs())

    def clean_html_tags(self, text):
        """Удаляет HTML-теги и экранирует спецсимволы"""
        # Удаляем все HTML-теги
        cleaned = re.sub(r'<[^>]+>', '', text)
        # Заменяем HTML-сущности на безопасные аналоги
        return html.escape(cleaned)

    async def process_logs(self):
        """Асинхронная задача для обработки логов из очереди"""
        while self.is_running:
            try:
                if not central_logger.log_queue.empty():
                    log_entry = central_logger.log_queue.get_nowait()
                    await self.add_log(log_entry['message'])
                else:
                    await asyncio.sleep(0.5)
            except Exception as e:
                logging.error(f"Ошибка обработки логов: {str(e)}")
    
    async def add_log(self, log_entry):
        """Добавляет запись в лог и обновляет сообщение"""
        # Упрощаем лог (убираем временные метки)
        clean_log = log_entry.split(" - ", 3)[-1] if " - " in log_entry else log_entry
        
        # Очищаем от HTML-тегов и экранируем спецсимволы
        clean_log = self.clean_html_tags(clean_log)
        
        # Обработка разделителей
        if "====" in clean_log or "▬▬▬" in clean_log:
            self.log_buffer = []
        
        self.log_buffer.append(clean_log)
        
        if len(self.log_buffer) > self.buffer_size:
            self.log_buffer.pop(0)
        
        log_text = "\n".join(self.log_buffer)
        
        # Обрезаем до лимита Telegram
        if len(log_text) > self.max_message_length:
            log_text = log_text[-self.max_message_length:]
        
        await self._safe_update(log_text)
    
    async def _safe_update(self, log_text):
        """Безопасное обновление сообщения с обработкой ошибок"""
        current_time = time.time()
        if current_time - self.last_update_time < self.update_interval:
            return
            
        try:
            if self.message_id:
                # Пытаемся обновить существующее сообщение
                await self.bot.edit_message_text(
                    chat_id=self.chat_id,
                    message_id=self.message_id,
                    text=f"<pre>{log_text}</pre>",
                    parse_mode="HTML"
                )
            else:
                # Создаем новое сообщение если нет ID
                msg = await self.bot.send_message(
                    self.chat_id,
                    f"<pre>{log_text}</pre>",
                    parse_mode="HTML"
                )
                self.message_id = msg.message_id
            
            self.last_update_time = current_time
            self.too_many_requests_count = 0
        except Exception as e:
            error_msg = str(e)
            
            # Обработка случая, когда сообщение не найдено
            if "message to edit not found" in error_msg:
                self.message_id = None  # Сбрасываем ID сообщения
                await self._safe_update(log_text)  # Пробуем снова
                return
            
            if "Too Many Requests" in error_msg:
                self.too_many_requests_count += 1
                self.update_interval = min(10.0, 2.0 + self.too_many_requests_count)
                await asyncio.sleep(5)
            elif "can't parse entities" in error_msg:
                # Пробуем отправить как plain text при ошибках парсинга
                try:
                    if self.message_id:
                        await self.bot.edit_message_text(
                            chat_id=self.chat_id,
                            message_id=self.message_id,
                            text=log_text  # Без parse_mode
                        )
                    else:
                        msg = await self.bot.send_message(
                            self.chat_id,
                            log_text  # Без parse_mode
                        )
                        self.message_id = msg.message_id
                except Exception as fallback_e:
                    logging.error(f"Fallback error: {str(fallback_e)}")
            else:
                logging.error(f"Ошибка обновления логов: {error_msg}")
    
    async def send_result_message(self, message):
        """Отправляет результат в отдельном сообщении"""
        try:
            # Очищаем сообщение от HTML-тегов
            clean_message = self.clean_html_tags(message)
            # Обрезаем до безопасной длины
            if len(clean_message) > 4000:
                clean_message = clean_message[:4000] + "... [сообщение обрезано]"
                
            # Отправляем как новое сообщение
            await self.bot.send_message(
                self.chat_id,
                f"<pre>{clean_message}</pre>",
                parse_mode="HTML"
            )
        except Exception as e:
            try:
                # Fallback: отправка без форматирования
                await self.bot.send_message(
                    self.chat_id,
                    clean_message[:4090]
                )
            except Exception as fallback_e:
                logging.error(f"Ошибка отправки результата: {str(fallback_e)}")
    
    async def final_message(self, message):
        """Отправляет финальное сообщение"""
        self.is_running = False
        await self.send_result_message(message)
    
    async def stop(self):
        """Останавливает обработчик"""
        self.is_running = False
        try:
            await self.task
        except asyncio.CancelledError:
            pass
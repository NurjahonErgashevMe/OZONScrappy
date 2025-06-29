import tkinter.messagebox as messagebox
import os
import tkinter as tk

class Utils:
    def toggle_token_visibility(self):
        if self.show_token_var.get():
            self.token_entry.config(show="")
        else:
            self.token_entry.config(show="*")
    
    def test_config(self):
        token = self.token_entry.get().strip()
        chat_id = self.chat_id_entry.get().strip()
        
        if not token or not chat_id:
            messagebox.showwarning("Предупреждение", "Заполните оба поля для проверки.")
            return
        
        issues = []
        if ':' not in token: issues.append("Токен должен содержать символ ':'")
        if len(token) < 35: issues.append("Токен слишком короткий")
        if not chat_id.lstrip('-').isdigit(): 
            issues.append("Chat ID должен быть числом (может начинаться с '-')")
        
        if issues:
            messagebox.showwarning("Проблемы", "\n".join(issues))
            self.logger.warning(f"Проблемы с конфигурацией: {', '.join(issues)}")
        else:
            messagebox.showinfo("Проверка", "Базовая проверка формата пройдена!")
            self.logger.info("Конфигурация прошла проверку")
        
        self.status_var.set("Проверка завершена")
    
    def update_config_info(self):
        config_path = self.get_config_path()
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    token_set = any(line.startswith("TELEGRAM_BOT_TOKEN=") and len(line.strip()) > len("TELEGRAM_BOT_TOKEN=") for line in lines)
                    chat_id_set = any(line.startswith("TELEGRAM_CHAT_ID=") and len(line.strip()) > len("TELEGRAM_CHAT_ID=") for line in lines)
                    
                    if token_set and chat_id_set:
                        self.config_info_var.set("✅ Конфигурация настроена")
                    else:
                        missing = []
                        if not token_set: missing.append("токен")
                        if not chat_id_set: missing.append("chat_id")
                        self.config_info_var.set(f"⚠️ Отсутствует: {', '.join(missing)}")
            except:
                self.config_info_var.set("❌ Ошибка чтения")
        else:
            self.config_info_var.set("❌ Файл не найден")
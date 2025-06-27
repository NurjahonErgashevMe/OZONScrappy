# parser/data_validators.py
import logging

logger = logging.getLogger(__name__)

class DataValidators:
    @staticmethod
    def is_company_name(text):
        """Проверяет, является ли текст названием компании"""
        company_indicators = ['ИП', 'ООО', 'АО', 'ЗАО', 'ПАО', 'Ltd', 'LLC', 'Inc']
        return any(indicator in text for indicator in company_indicators)

    @staticmethod
    def is_inn(text):
        """Проверяет, является ли текст ИНН/ОГРН"""
        # Более гибкая проверка ИНН/ОГРН
        digits_only = ''.join(filter(str.isdigit, text))
        return 10 <= len(digits_only) <= 15

    @staticmethod
    def is_address(text):
        """Проверяет, является ли текст адресом"""
        address_indicators = [
            'г.', 'город', 'ул.', 'улица', 'пр.', 'проспект', 
            'д.', 'дом', 'обл.', 'область', 'кв.', 'квартира'
        ]
        return any(indicator in text.lower() for indicator in address_indicators)

    @staticmethod
    def is_working_hours(text):
        """Проверяет, является ли текст режимом работы"""
        working_hours_indicators = ['режим работы', 'работает', 'часы работы']
        return any(indicator in text.lower() for indicator in working_hours_indicators)
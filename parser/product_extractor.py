import re
import logging
from selenium.webdriver.common.by import By

class ProductExtractor:
    def __init__(self):
        self.logger = logging.getLogger('product_extractor')
    
    def extract_product_data(self, product_card):
        """Извлечение всех данных о товаре из карточки"""
        try:
            product_data = {
                'name': self._extract_name(product_card),
                'price_with_discount': self._extract_price_with_discount(product_card),
                'price_without_discount': self._extract_price_without_discount(product_card),
                'discount_percent': self._extract_discount_percent(product_card),
                'rating': self._extract_rating(product_card),
                'reviews_count': self._extract_reviews_count(product_card),
                'url': self._extract_url(product_card)
            }
            
            # Проверяем, что основные данные есть
            if product_data['name'] and product_data['url']:
                return product_data
            else:
                self.logger.debug(f"Недостаточно данных: {product_data}")
                return None
                
        except Exception as e:
            self.logger.debug(f"Ошибка извлечения данных товара: {str(e)}")
            return None
    
    def _extract_name(self, card):
        """Извлечение названия товара"""
        try:
            # Приоритетные селекторы из вашего HTML
            selectors = [
                '.bq020-a4 span.tsBody500Medium',  # Основной селектор
                '.bq020-a span.tsBody500Medium',
                '.bq020-a span',
                '.tsBody500Medium',
                'span.tsBody500Medium',
                'a[target="_blank"] span',
                '.tile-clickable-element span'
            ]
            
            for selector in selectors:
                try:
                    element = card.find_element(By.CSS_SELECTOR, selector)
                    text = element.text.strip()
                    if text:  # Убрали проверку длины
                        return text
                except:
                    continue
            
            return ""  # Пустая строка вместо дефолтного текста
            
        except Exception as e:
            self.logger.debug(f"Ошибка извлечения названия: {str(e)}")
            return ""
    
    def _extract_price_with_discount(self, card):
        """Извлечение цены со скидкой"""
        try:
            # Основные селекторы для акционной цены
            selectors = [
                '.c320-a1.tsHeadline500Medium',  # Самый специфичный
                '.tsHeadline500Medium',
                'span.tsHeadline500Medium',
                '[class*="price"]',
                '[class*="discount"] + span'
            ]
            
            for selector in selectors:
                try:
                    element = card.find_element(By.CSS_SELECTOR, selector)
                    price_text = element.text.strip()
                    price = self._parse_price(price_text)
                    if price:
                        return price
                except:
                    continue
            
            return "0"
            
        except Exception as e:
            self.logger.debug(f"Ошибка извлечения цены со скидкой: {str(e)}")
            return "0"
    
    def _extract_price_without_discount(self, card):
        """Извлечение цены без скидки (зачеркнутая цена)"""
        try:
            # Селекторы для зачеркнутой цены
            selectors = [
                '.c320-a1.tsBodyControl400Small',  # Основной селектор
                '.tsBodyControl400Small',
                'span.tsBodyControl400Small',
                '[class*="strike"]',
                '[class*="old-price"]'
            ]
            
            for selector in selectors:
                try:
                    elements = card.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        price_text = element.text.strip()
                        # Убрали проверку на валюту
                        if price_text and price_text != self._extract_price_with_discount(card):
                            price = self._parse_price(price_text)
                            if price:
                                return price
                except:
                    continue
            
            # Если цена без скидки не найдена, возвращаем цену со скидкой
            return self._extract_price_with_discount(card)
            
        except Exception as e:
            self.logger.debug(f"Ошибка извлечения цены без скидки: {str(e)}")
            return self._extract_price_with_discount(card)
    
    def _extract_discount_percent(self, card):
        """Извлечение процента скидки"""
        try:
            # Селекторы для процента скидки
            selectors = [
                '.c320-b4',  # Основной селектор
                'span.c320-b4',
                '[class*="discount-percent"]',
                '[class*="discount"]'
            ]
            
            for selector in selectors:
                try:
                    element = card.find_element(By.CSS_SELECTOR, selector)
                    discount_text = element.text.strip()
                    if '%' in discount_text:
                        # Извлекаем число из строки
                        match = re.search(r'(\d+)%', discount_text)
                        if match:
                            return match.group(1) + "%"
                except:
                    continue
            
            # Если скидка не найдена, вычисляем
            price_with = self._parse_price_number(self._extract_price_with_discount(card))
            price_without = self._parse_price_number(self._extract_price_without_discount(card))
            
            if price_with and price_without and price_without > price_with:
                discount = int(((price_without - price_with) / price_without) * 100)
                return f"{discount}%"
            
            return "0%"
            
        except Exception as e:
            self.logger.debug(f"Ошибка извлечения скидки: {str(e)}")
            return "0%"
    
    def _extract_rating(self, card):
        """Извлечение рейтинга"""
        try:
            # Улучшенные селекторы для рейтинга
            selectors = [
                '.p6b20-a5 + span',  # Рейтинг рядом с иконкой звезды
                '[class*="rating-value"]',
                '[class*="star-rating"] + span',
                'span[aria-label*="рейтинг"]'
            ]
            
            for selector in selectors:
                try:
                    element = card.find_element(By.CSS_SELECTOR, selector)
                    text = element.text.strip()
                    if re.match(r'^\d+(\.\d+)?$', text) and float(text) <= 5:
                        return text
                except:
                    continue
            
            return "Нет рейтинга"
            
        except Exception as e:
            self.logger.debug(f"Ошибка извлечения рейтинга: {str(e)}")
            return "Нет рейтинга"
    
    def _extract_reviews_count(self, card):
        """Извлечение количества отзывов"""
        try:
            # Улучшенные селекторы для отзывов
            selectors = [
                '.p6b20-a5 ~ span',  # Элемент рядом с иконкой отзывов
                '[class*="reviews-count"]',
                'span:contains("отзыв")',
                'span:contains("review")'
            ]
            
            for selector in selectors:
                try:
                    element = card.find_element(By.CSS_SELECTOR, selector)
                    text = element.text.strip()
                    if 'отзыв' in text.lower():
                        match = re.search(r'(\d+)', text)
                        if match:
                            return match.group(1)
                except:
                    continue
            
            return "0"
            
        except Exception as e:
            self.logger.debug(f"Ошибка извлечения количества отзывов: {str(e)}")
            return "0"
    
    def _extract_url(self, card):
        """Извлечение ссылки на товар"""
        try:
            # Улучшенные селекторы для URL
            selectors = [
                'a.tile-clickable-element[href*="/product/"]',  # Основной селектор
                'a[href*="/product/"][target="_blank"]',
                'a[href*="/product/"]',
                'a[target="_blank"][href]'
            ]
            
            for selector in selectors:
                try:
                    element = card.find_element(By.CSS_SELECTOR, selector)
                    href = element.get_attribute('href')
                    if href and '/product/' in href:
                        return href.split('?')[0]  # Очищаем от параметров
                except:
                    continue
            
            return ""
            
        except Exception as e:
            self.logger.debug(f"Ошибка извлечения URL: {str(e)}")
            return ""
    
    def _parse_price(self, price_text):
        """Парсинг цены из текста"""
        if not price_text:
            return "0"
        
        # Удаляем все символы кроме цифр и пробелов
        cleaned = re.sub(r'[^\d\s]', '', price_text)
        return cleaned.strip() if cleaned.strip() else "0"
    
    def _parse_price_number(self, price_text):
        """Парсинг цены как числа для вычислений"""
        if not price_text:
            return 0
        
        # Извлекаем только цифры
        numbers = re.findall(r'\d+', price_text)
        if numbers:
            return int(''.join(numbers))
        return 0
"""
Тесты для фронтенд-стандартов 2025 ExamFlow
"""

import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings


class FrontendStandardsTestCase(TestCase):
    """Тесты соответствия фронтенд-стандартам 2025"""
    
    def setUp(self):
        """Настройка тестов"""
        self.client = Client()
    
    def test_css_minification_available(self):
        """Тест доступности минифицированного CSS"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        # Проверяем, что минифицированный CSS существует
        import os
        min_css_path = os.path.join(settings.STATIC_ROOT or 'static', 'css', 'examflow-2.0.min.css')
        self.assertTrue(os.path.exists(min_css_path), "Минифицированный CSS не найден")
    
    def test_js_minification_available(self):
        """Тест доступности минифицированного JS"""
        import os
        min_js_path = os.path.join(settings.STATIC_ROOT or 'static', 'js', 'core-functions.min.js')
        self.assertTrue(os.path.exists(min_js_path), "Минифицированный JS не найден")
    
    def test_lazy_loading_images(self):
        """Тест lazy loading для изображений"""
        response = self.client.get('/')
        self.assertContains(response, 'loading="lazy"', msg_prefix="Lazy loading не найден в изображениях")
    
    def test_css_variables_updated(self):
        """Тест обновления CSS переменных"""
        import os
        css_path = os.path.join(settings.STATIC_ROOT or 'static', 'css', 'examflow-2.0.css')
        
        with open(css_path, 'r', encoding='utf-8') as f:
            css_content = f.read()
        
        # Проверяем новый цвет
        self.assertIn('#4A90E2', css_content, "Новый цвет #4A90E2 не найден в CSS")
        
        # Проверяем упрощенную типографику
        self.assertIn('/* Размеры шрифтов (стандарт 2025: 3 основных размера) */', css_content)
    
    def test_flat_buttons_design(self):
        """Тест плоского дизайна кнопок"""
        import os
        css_path = os.path.join(settings.STATIC_ROOT or 'static', 'css', 'examflow-2.0.css')
        
        with open(css_path, 'r', encoding='utf-8') as f:
            css_content = f.read()
        
        # Проверяем, что градиенты убраны
        self.assertNotIn('var(--gradient-primary)', css_content, "Градиенты не убраны из кнопок")
        
        # Проверяем плоский дизайн
        self.assertIn('/* Основная кнопка (плоский дизайн 2025) */', css_content)
        self.assertIn('box-shadow: none;', css_content)


class TelegramBotStandardsTestCase(TestCase):
    """Тесты стандартов Telegram бота"""
    
    def test_standard_button_functions(self):
        """Тест функций стандартных кнопок"""
        from telegram_bot.bot_handlers import create_standard_button, create_main_message, create_warning_message
        
        # Тест создания кнопки
        button = create_standard_button("test", "test_data")
        self.assertEqual(button.text, "TEST")
        self.assertEqual(button.callback_data, "test_data")
        
        # Тест основного сообщения
        message = create_main_message("test")
        self.assertEqual(message, "**test**")
        
        # Тест предупреждающего сообщения
        warning = create_warning_message("test")
        self.assertEqual(warning, "⚠️ test")


class PerformanceTestCase(TestCase):
    """Тесты производительности"""
    
    def test_css_file_size(self):
        """Тест размера CSS файла"""
        import os
        
        # Обычный CSS
        css_path = os.path.join(settings.STATIC_ROOT or 'static', 'css', 'examflow-2.0.css')
        css_size = os.path.getsize(css_path)
        
        # Минифицированный CSS
        min_css_path = os.path.join(settings.STATIC_ROOT or 'static', 'css', 'examflow-2.0.min.css')
        min_css_size = os.path.getsize(min_css_path)
        
        # Минифицированный должен быть меньше
        self.assertLess(min_css_size, css_size, "Минифицированный CSS не меньше обычного")
        
        # Сжатие должно быть значительным (хотя бы 20%)
        compression_ratio = (css_size - min_css_size) / css_size
        self.assertGreater(compression_ratio, 0.2, f"Сжатие CSS менее 20%: {compression_ratio:.1%}")
    
    def test_js_file_size(self):
        """Тест размера JS файла"""
        import os
        
        # Обычный JS
        js_path = os.path.join(settings.STATIC_ROOT or 'static', 'js', 'core-functions.js')
        js_size = os.path.getsize(js_path)
        
        # Минифицированный JS
        min_js_path = os.path.join(settings.STATIC_ROOT or 'static', 'js', 'core-functions.min.js')
        min_js_size = os.path.getsize(min_js_path)
        
        # Минифицированный должен быть меньше
        self.assertLess(min_js_size, js_size, "Минифицированный JS не меньше обычного")

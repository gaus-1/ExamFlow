#!/usr/bin/env python
"""
Простой тест ИИ модуля
"""
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')
django.setup()

def test_ai_basic():
    """Базовый тест ИИ"""
    print("🔍 Базовое тестирование ИИ...")
    
    try:
        # Проверяем импорт
        print("1. Проверка импорта...")
        from ai import models
        print("   ✅ Модели импортированы")
        
        from ai import views
        print("   ✅ Views импортированы")
        
        from ai import services
        print("   ✅ Services импортированы")
        
        # Проверяем URL'ы
        print("2. Проверка URL'ов...")
        from django.urls import reverse
        try:
            chat_url = reverse('ai:chat')
            print(f"   ✅ URL чата: {chat_url}")
        except Exception as e:
            print(f"   ❌ Ошибка URL чата: {e}")
        
        # Проверяем шаблоны
        print("3. Проверка шаблонов...")
        from django.template.loader import get_template
        try:
            chat_template = get_template('ai/chat.html')
            print("   ✅ Шаблон чата найден")
        except Exception as e:
            print(f"   ❌ Ошибка шаблона чата: {e}")
        
        print("🎉 Базовое тестирование завершено!")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ai_basic()

#!/usr/bin/env python
"""
Тест работы ИИ модуля ExamFlow
"""
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')
django.setup()

def test_ai_module():
    """Тестируем ИИ модуль"""
    print("🔍 Тестирование ИИ модуля ExamFlow...")
    
    try:
        # 1. Проверяем импорт моделей
        print("1. Проверка моделей ИИ...")
        from ai.models import AiRequest, AiLimit, AiProvider, AiResponse
        print("   ✅ Модели ИИ импортированы успешно")
        
        # 2. Проверяем импорт views
        print("2. Проверка views ИИ...")
        from ai import views
        print("   ✅ Views ИИ импортированы успешно")
        
        # 3. Проверяем импорт services
        print("3. Проверка services ИИ...")
        from ai import services
        print("   ✅ Services ИИ импортированы успешно")
        
        # 4. Проверяем URL'ы
        print("4. Проверка URL'ов ИИ...")
        from django.urls import reverse
        try:
            chat_url = reverse('ai:chat')
            print(f"   ✅ URL чата: {chat_url}")
        except Exception as e:
            print(f"   ❌ Ошибка URL чата: {e}")
        
        # 5. Проверяем шаблоны
        print("5. Проверка шаблонов ИИ...")
        from django.template.loader import get_template
        try:
            chat_template = get_template('ai/chat.html')
            print("   ✅ Шаблон чата найден")
        except Exception as e:
            print(f"   ❌ Ошибка шаблона чата: {e}")
        
        # 6. Проверяем подключение к БД
        print("6. Проверка подключения к БД...")
        from django.db import connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                print("   ✅ Подключение к БД работает")
        except Exception as e:
            print(f"   ❌ Ошибка подключения к БД: {e}")
        
        # 7. Проверяем таблицы ИИ в БД
        print("7. Проверка таблиц ИИ в БД...")
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name LIKE 'ai_%'
                """)
                tables = cursor.fetchall()
                if tables:
                    print(f"   ✅ Найдены таблицы ИИ: {[t[0] for t in tables]}")
                else:
                    print("   ⚠️ Таблицы ИИ не найдены (нужно создать миграции)")
        except Exception as e:
            print(f"   ❌ Ошибка проверки таблиц: {e}")
        
        print("\n🎉 Тестирование ИИ модуля завершено!")
        
        # Рекомендации
        if not tables:
            print("\n📋 Рекомендации:")
            print("1. Создайте миграции: python manage.py makemigrations ai")
            print("2. Примените миграции: python manage.py migrate")
            print("3. Перезапустите сервер")
        
    except Exception as e:
        print(f"❌ Критическая ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ai_module()

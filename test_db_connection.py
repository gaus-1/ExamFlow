#!/usr/bin/env python
"""
Тест подключения к базе данных
"""
import os
import sys
import django

# Принудительно устанавливаем переменные окружения
os.environ['USE_SQLITE'] = 'False'
os.environ['DATABASE_URL'] = 'postgresql://postgres:Slava2402@localhost:5432/examflow_db'
os.environ['DEBUG'] = 'True'

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')
django.setup()

def test_database():
    """Тестируем подключение к базе данных"""
    print("🔍 Тестирование подключения к базе данных...")
    
    try:
        from django.conf import settings
        from django.db import connection
        
        # Проверяем настройки БД
        print(f"1. Настройки базы данных:")
        print(f"   ENGINE: {settings.DATABASES['default']['ENGINE']}")
        print(f"   NAME: {settings.DATABASES['default']['NAME']}")
        print(f"   USER: {settings.DATABASES['default']['USER']}")
        print(f"   HOST: {settings.DATABASES['default']['HOST']}")
        print(f"   PORT: {settings.DATABASES['default']['PORT']}")
        
        # Проверяем подключение
        print(f"\n2. Тест подключения:")
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"   ✅ Подключение успешно!")
            print(f"   📊 Версия PostgreSQL: {version[0]}")
        
        # Проверяем таблицы
        print(f"\n3. Существующие таблицы:")
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            print(f"   📋 Найдено таблиц: {len(tables)}")
            
            if tables:
                print("   📋 Таблицы:")
                for table in tables[:15]:  # Показываем первые 15
                    print(f"      - {table[0]}")
                if len(tables) > 15:
                    print(f"      ... и еще {len(tables) - 15} таблиц")
        
        print(f"\n🎉 Тест базы данных завершен успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании базы данных: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_database()

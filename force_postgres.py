#!/usr/bin/env python
"""
Принудительное переключение на PostgreSQL
"""
import os
import sys
import django

# Принудительно устанавливаем переменные окружения
os.environ['USE_SQLITE'] = 'False'
os.environ['DATABASE_URL'] = 'postgresql://postgre:Slava2402@localhost:5432/examflow_db'
os.environ['DEBUG'] = 'True'

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')
django.setup()

def test_postgres():
    """Тестируем подключение к PostgreSQL"""
    print("🔍 Тестирование подключения к PostgreSQL...")
    
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"   ✅ Подключение к PostgreSQL успешно!")
            print(f"   📊 Версия: {version[0]}")
            
            # Проверяем таблицы
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
                for table in tables[:10]:  # Показываем первые 10
                    print(f"      - {table[0]}")
                if len(tables) > 10:
                    print(f"      ... и еще {len(tables) - 10} таблиц")
            
    except Exception as e:
        print(f"   ❌ Ошибка подключения к PostgreSQL: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_postgres()

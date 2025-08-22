#!/usr/bin/env python
"""
Скрипт исправления миграций ExamFlow
"""
import os
import sys
import django

def fix_migrations():
    """Исправляем проблемы с миграциями"""
    print("🔧 Исправление миграций ExamFlow...")
    
    # Устанавливаем переменные окружения
    os.environ['USE_SQLITE'] = 'False'
    os.environ['DATABASE_URL'] = 'postgresql://postgres:Slava2402@localhost:5432/examflow_db'
    os.environ['DEBUG'] = 'True'
    
    # Настройка Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')
    django.setup()
    
    print("✅ Django настроен")
    
    try:
        from django.db import connection
        from django.core.management import call_command
        
        # Проверяем подключение
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"📊 Подключение к PostgreSQL: {version[0]}")
        
        # Создаем миграции заново
        print("\n🔧 Создание миграций...")
        
        # Удаляем старые миграции core
        core_migrations_dir = "core/migrations"
        if os.path.exists(core_migrations_dir):
            for file in os.listdir(core_migrations_dir):
                if file.startswith("0009_") or file.startswith("0010_"):
                    file_path = os.path.join(core_migrations_dir, file)
                    os.remove(file_path)
                    print(f"🗑️ Удалена миграция: {file}")
        
        # Создаем новые миграции
        print("\n📝 Создание миграций для core...")
        call_command('makemigrations', 'core', verbosity=1)
        
        print("\n📝 Создание миграций для themes...")
        call_command('makemigrations', 'themes', verbosity=1)
        
        print("\n📝 Создание миграций для ai...")
        call_command('makemigrations', 'ai', verbosity=1)
        
        # Применяем миграции
        print("\n🚀 Применение миграций...")
        call_command('migrate', verbosity=1)
        
        print("\n✅ Миграции исправлены и применены!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_migrations()

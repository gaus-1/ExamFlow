#!/usr/bin/env python
"""
Скрипт для деплоя ExamFlow на Render
Автоматически применяет миграции и создает необходимые таблицы
"""

import os
import sys
import django
from pathlib import Path

# Добавляем путь к проекту
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')
django.setup()

from django.core.management import execute_from_command_line
from django.db import connection
from django.db.utils import OperationalError

def check_database():
    """Проверяет подключение к базе данных"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            print("✅ Подключение к базе данных успешно")
            return True
    except OperationalError as e:
        print(f"❌ Ошибка подключения к базе данных: {e}")
        return False

def apply_migrations():
    """Применяет миграции"""
    try:
        print("🔄 Применяем миграции...")
        execute_from_command_line(['manage.py', 'migrate'])
        print("✅ Миграции применены успешно")
        return True
    except Exception as e:
        print(f"❌ Ошибка при применении миграций: {e}")
        return False

def check_tables():
    """Проверяет наличие основных таблиц"""
    try:
        from learning.models import Subject, Task
        from authentication.models import UserProfile
        
        # Проверяем количество записей
        subject_count = Subject.objects.count()
        task_count = Task.objects.count()
        
        print(f"✅ Таблица Subject: {subject_count} записей")
        print(f"✅ Таблица Task: {task_count} записей")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка при проверке таблиц: {e}")
        return False

def create_sample_data():
    """Создает образцы данных если таблицы пустые"""
    try:
        from learning.models import Subject, Topic, Task
        
        if Subject.objects.count() == 0:
            print("📚 Создаем образцы предметов...")
            
            # Создаем предметы
            subjects = [
                Subject(name="Математика", description="Алгебра и геометрия"),
                Subject(name="Физика", description="Механика и электричество"),
                Subject(name="Химия", description="Органическая и неорганическая химия"),
                Subject(name="Биология", description="Анатомия и экология"),
                Subject(name="История", description="Российская и всемирная история"),
                Subject(name="География", description="Физическая и экономическая география"),
                Subject(name="Литература", description="Русская и зарубежная литература"),
                Subject(name="Информатика", description="Программирование и алгоритмы"),
            ]
            
            Subject.objects.bulk_create(subjects)
            print(f"✅ Создано {len(subjects)} предметов")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка при создании образцов данных: {e}")
        return False

def main():
    """Основная функция"""
    print("🚀 ДЕПЛОЙ EXAMFLOW НА RENDER")
    print("=" * 50)
    
    # Проверяем базу данных
    if not check_database():
        print("❌ Не удалось подключиться к базе данных")
        return False
    
    # Применяем миграции
    if not apply_migrations():
        print("❌ Не удалось применить миграции")
        return False
    
    # Проверяем таблицы
    if not check_tables():
        print("❌ Проблемы с таблицами")
        return False
    
    # Создаем образцы данных
    create_sample_data()
    
    print("=" * 50)
    print("🎉 ДЕПЛОЙ ЗАВЕРШЕН УСПЕШНО!")
    print("✅ База данных настроена")
    print("✅ Таблицы созданы")
    print("✅ Миграции применены")
    print("✅ Образцы данных добавлены")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

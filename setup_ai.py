#!/usr/bin/env python
"""
Скрипт настройки ИИ модуля ExamFlow
"""
import os
import sys
import subprocess
import django

def setup_ai():
    """Настройка ИИ модуля"""
    print("🚀 Настройка ИИ модуля ExamFlow...")
    
    # Устанавливаем переменные окружения
    os.environ['USE_SQLITE'] = 'False'
    os.environ['DATABASE_URL'] = 'postgresql://postgres:Slava2402@localhost:5432/examflow_db'
    os.environ['DEBUG'] = 'True'
    
    # Настройка Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')
    django.setup()
    
    print("✅ Django настроен")
    
    # Выполняем команды Django
    commands = [
        ['python', 'manage.py', 'makemigrations', 'ai'],
        ['python', 'manage.py', 'migrate'],
        ['python', 'manage.py', 'check']
    ]
    
    for cmd in commands:
        print(f"\n🔧 Выполняю: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
            if result.stdout:
                print("📤 Вывод:")
                print(result.stdout)
            if result.stderr:
                print("⚠️ Ошибки:")
                print(result.stderr)
            if result.returncode == 0:
                print("✅ Команда выполнена успешно")
            else:
                print(f"❌ Команда завершилась с кодом {result.returncode}")
        except Exception as e:
            print(f"❌ Ошибка выполнения команды: {e}")
    
    print("\n🎉 Настройка завершена!")

if __name__ == "__main__":
    setup_ai()

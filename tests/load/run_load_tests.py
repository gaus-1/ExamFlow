"""
Скрипт для запуска load тестов ExamFlow
"""

import os
import sys
import subprocess
import time
from pathlib import Path


def run_load_tests():
    """Запуск load тестов с разными конфигурациями"""
    
    # Добавляем путь к проекту
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    # Устанавливаем переменные окружения
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')
    
    # Импортируем Django
    import django
    django.setup()
    
    print("🚀 Запуск load тестов для ExamFlow")
    print("=" * 50)
    
    # Конфигурации для разных сценариев
    test_configs = [
        {
            'name': 'Обычная нагрузка',
            'users': 10,
            'spawn_rate': 2,
            'duration': '2m',
            'class': 'WebsiteUser'
        },
        {
            'name': 'API нагрузка',
            'users': 20,
            'spawn_rate': 5,
            'duration': '3m',
            'class': 'APIUser'
        },
        {
            'name': 'Стресс-тест',
            'users': 50,
            'spawn_rate': 10,
            'duration': '5m',
            'class': 'HeavyUser'
        }
    ]
    
    for config in test_configs:
        print(f"\n📊 Тестирование: {config['name']}")
        print(f"👥 Пользователей: {config['users']}")
        print(f"⚡ Скорость создания: {config['spawn_rate']}/сек")
        print(f"⏱️ Длительность: {config['duration']}")
        print("-" * 30)
        
        # Команда для запуска locust
        cmd = [
            'locust',
            '-f', 'tests/load/locustfile.py',
            '--host', 'http://localhost:8000',  # Измените на ваш URL
            '--users', str(config['users']),
            '--spawn-rate', str(config['spawn_rate']),
            '--run-time', config['duration'],
            '--headless',
            '--html', f'reports/load_test_{config["class"]}.html',
            '--csv', f'reports/load_test_{config["class"]}',
            '--class', config['class']
        ]
        
        try:
            # Запускаем тест
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                print(f"✅ {config['name']} завершен успешно")
            else:
                print(f"❌ {config['name']} завершен с ошибками")
                print(f"Ошибка: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print(f"⏰ {config['name']} превысил время ожидания")
        except Exception as e:
            print(f"💥 Ошибка при запуске {config['name']}: {e}")
        
        # Пауза между тестами
        time.sleep(10)
    
    print("\n🎉 Все load тесты завершены!")
    print("📁 Отчеты сохранены в папке reports/")


def run_single_test(users=10, duration='2m', test_class='WebsiteUser'):
    """Запуск одного теста с заданными параметрами"""
    
    print(f"🚀 Запуск load теста: {test_class}")
    print(f"👥 Пользователей: {users}")
    print(f"⏱️ Длительность: {duration}")
    
    cmd = [
        'locust',
        '-f', 'tests/load/locustfile.py',
        '--host', 'http://localhost:8000',
        '--users', str(users),
        '--spawn-rate', '5',
        '--run-time', duration,
        '--headless',
        '--html', f'reports/load_test_{test_class}.html',
        '--csv', f'reports/load_test_{test_class}',
        '--class', test_class
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Тест завершен успешно")
            print("📁 Отчет сохранен в папке reports/")
        else:
            print("❌ Тест завершен с ошибками")
            print(f"Ошибка: {result.stderr}")
            
    except Exception as e:
        print(f"💥 Ошибка при запуске теста: {e}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Запуск load тестов ExamFlow')
    parser.add_argument('--users', type=int, default=10, help='Количество пользователей')
    parser.add_argument('--duration', default='2m', help='Длительность теста')
    parser.add_argument('--class', dest='test_class', default='WebsiteUser', 
                       choices=['WebsiteUser', 'APIUser', 'HeavyUser'],
                       help='Класс теста')
    parser.add_argument('--all', action='store_true', help='Запустить все тесты')
    
    args = parser.parse_args()
    
    if args.all:
        run_load_tests()
    else:
        run_single_test(args.users, args.duration, args.test_class)

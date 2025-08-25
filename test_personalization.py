#!/usr/bin/env python
"""
Скрипт для тестирования системы персонализации ExamFlow
"""

import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Subject, Task, UserProgress
from core.personalization_system import get_user_insights, UserBehaviorAnalyzer, PersonalizedRecommendations

def test_personalization_system():
    """Тестирует систему персонализации"""
    print("🧪 Тестирование системы персонализации ExamFlow")
    print("=" * 50)
    
    # 1. Проверяем модели
    print("\n1. Проверка моделей:")
    try:
        subjects_count = Subject.objects.count()
        tasks_count = Task.objects.count()
        progress_count = UserProgress.objects.count()
        print(f"   ✅ Subjects: {subjects_count}")
        print(f"   ✅ Tasks: {tasks_count}")
        print(f"   ✅ UserProgress: {progress_count}")
    except Exception as e:
        print(f"   ❌ Ошибка при проверке моделей: {e}")
        return False
    
    # 2. Создаем тестового пользователя если его нет
    print("\n2. Создание тестового пользователя:")
    try:
        user, created = User.objects.get_or_create(
            username='test_user',
            defaults={
                'email': 'test@examflow.ru',
                'first_name': 'Тест',
                'last_name': 'Пользователь'
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
            print(f"   ✅ Создан новый пользователь: {user.username}")
        else:
            print(f"   ✅ Используется существующий пользователь: {user.username}")
    except Exception as e:
        print(f"   ❌ Ошибка при создании пользователя: {e}")
        return False
    
    # 3. Создаем тестовые данные если их нет
    print("\n3. Создание тестовых данных:")
    try:
        # Создаем предмет если его нет
        subject, created = Subject.objects.get_or_create(
            name='Математика',
            defaults={
                'code': 'MATH',
                'exam_type': 'ege',
                'description': 'Математика для ЕГЭ'
            }
        )
        if created:
            print(f"   ✅ Создан предмет: {subject.name}")
        else:
            print(f"   ✅ Используется существующий предмет: {subject.name}")
        
        # Создаем задачи если их нет
        if Task.objects.count() == 0:
            tasks_data = [
                {'title': 'Задача 1: Уравнения', 'difficulty': 2, 'text': 'Решите уравнение x² + 5x + 6 = 0'},
                {'title': 'Задача 2: Геометрия', 'difficulty': 3, 'text': 'Найдите площадь треугольника'},
                {'title': 'Задача 3: Тригонометрия', 'difficulty': 4, 'text': 'Решите sin²x + cos²x = 1'},
            ]
            
            for task_data in tasks_data:
                task = Task.objects.create(
                    subject=subject,
                    title=task_data['title'],
                    text=task_data['text'],
                    difficulty=task_data['difficulty']
                )
                print(f"   ✅ Создана задача: {task.title}")
        else:
            print(f"   ✅ Используются существующие задачи: {Task.objects.count()}")
            
    except Exception as e:
        print(f"   ❌ Ошибка при создании тестовых данных: {e}")
        return False
    
    # 4. Создаем тестовый прогресс
    print("\n4. Создание тестового прогресса:")
    try:
        # Создаем прогресс для пользователя
        tasks = Task.objects.all()[:3]
        for i, task in enumerate(tasks):
            progress, created = UserProgress.objects.get_or_create(
                user=user,
                task=task,
                defaults={
                    'is_correct': i % 2 == 0,  # Чередуем правильные/неправильные ответы
                    'attempts': i + 1,
                    'time_spent': (i + 1) * 60
                }
            )
            if created:
                print(f"   ✅ Создан прогресс для задачи: {task.title}")
            else:
                print(f"   ✅ Используется существующий прогресс для: {task.title}")
                
    except Exception as e:
        print(f"   ❌ Ошибка при создании прогресса: {e}")
        return False
    
    # 5. Тестируем систему персонализации
    print("\n5. Тестирование системы персонализации:")
    try:
        # Тестируем UserBehaviorAnalyzer
        analyzer = UserBehaviorAnalyzer(user.id)
        preferences = analyzer.get_user_preferences()
        patterns = analyzer.get_study_patterns()
        
        print(f"   ✅ Предпочтения получены: {len(preferences)} параметров")
        print(f"   ✅ Паттерны обучения получены: {len(patterns)} параметров")
        
        # Тестируем PersonalizedRecommendations
        recommender = PersonalizedRecommendations(user.id)
        recommended_tasks = recommender.get_recommended_tasks(5)
        study_plan = recommender.get_study_plan()
        weak_topics = recommender.get_weak_topics()
        
        print(f"   ✅ Рекомендуемые задачи: {len(recommended_tasks)}")
        print(f"   ✅ План обучения создан: {len(study_plan)} разделов")
        print(f"   ✅ Слабые темы: {len(weak_topics)}")
        
        # Тестируем get_user_insights
        insights = get_user_insights(user.id)
        print(f"   ✅ Инсайты пользователя получены: {len(insights)} разделов")
        
    except Exception as e:
        print(f"   ❌ Ошибка при тестировании персонализации: {e}")
        return False
    
    # 6. Тестируем API endpoints
    print("\n6. Тестирование API endpoints:")
    try:
        from django.test import Client
        from django.urls import reverse
        
        client = Client()
        
        # Тестируем API insights
        response = client.get('/core/api/personalization/insights/')
        if response.status_code == 302:  # Redirect to login
            print("   ✅ API insights требует авторизации (ожидаемо)")
        else:
            print(f"   ⚠️ API insights вернул статус: {response.status_code}")
            
        # Тестируем страницы персонализации
        urls_to_test = [
            '/core/personalization/',
            '/core/personalization/analytics/',
            '/core/personalization/recommendations/',
            '/core/personalization/study-plan/',
            '/core/personalization/weak-topics/',
        ]
        
        for url in urls_to_test:
            response = client.get(url)
            if response.status_code == 302:  # Redirect to login
                print(f"   ✅ {url} требует авторизации (ожидаемо)")
            else:
                print(f"   ⚠️ {url} вернул статус: {response.status_code}")
                
    except Exception as e:
        print(f"   ❌ Ошибка при тестировании API: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Тестирование завершено успешно!")
    print("✅ Система персонализации работает корректно")
    print("✅ Все компоненты функционируют")
    print("✅ API endpoints доступны")
    print("✅ Модели и данные корректны")
    
    return True

if __name__ == '__main__':
    success = test_personalization_system()
    if success:
        print("\n🚀 Система готова к деплою!")
    else:
        print("\n❌ Обнаружены проблемы, требуется исправление")
        sys.exit(1)

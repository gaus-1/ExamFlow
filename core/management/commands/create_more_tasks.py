"""
Создает больше задач для математики и русского языка
"""

from django.core.management.base import BaseCommand
from learning.models import Subject, Task
import random


class Command(BaseCommand):
    help = 'Создает дополнительные задачи для математики и русского языка'

    def handle(self, *args, **options):
        self.stdout.write('🎯 СОЗДАНИЕ ДОПОЛНИТЕЛЬНЫХ ЗАДАЧ')
        self.stdout.write('=' * 50)

        # Получаем предметы
        try:
            math_subjects = Subject.objects.filter(name__icontains='математик')  # type: ignore
            russian_subjects = Subject.objects.filter(name__icontains='русск')  # type: ignore
            
            self.stdout.write(f'Найдено математических предметов: {math_subjects.count()}')
            self.stdout.write(f'Найдено предметов русского языка: {russian_subjects.count()}')
            
            # Создаем задачи по математике
            math_tasks = [
                {
                    'title': 'Найдите производную функции f(x) = x³ + 2x² - 5x + 1',
                    'description': 'Вычислите производную функции f(x) = x³ + 2x² - 5x + 1',
                    'answer': 'f\'(x) = 3x² + 4x - 5',
                    'difficulty': 3
                },
                {
                    'title': 'Решите неравенство 2x + 3 > 7',
                    'description': 'Найдите множество решений неравенства 2x + 3 > 7',
                    'answer': 'x > 2',
                    'difficulty': 1
                },
                {
                    'title': 'Найдите площадь треугольника со сторонами 3, 4, 5',
                    'description': 'Вычислите площадь треугольника со сторонами a=3, b=4, c=5',
                    'answer': '6',
                    'difficulty': 2
                },
                {
                    'title': 'Упростите выражение (x + 2)² - (x - 1)²',
                    'description': 'Упростите алгебраическое выражение (x + 2)² - (x - 1)²',
                    'answer': '6x + 3',
                    'difficulty': 2
                },
                {
                    'title': 'Найдите корни уравнения x² - 7x + 12 = 0',
                    'description': 'Решите квадратное уравнение x² - 7x + 12 = 0',
                    'answer': 'x₁ = 3, x₂ = 4',
                    'difficulty': 2
                }
            ]
            
            # Создаем задачи по русскому языку
            russian_tasks = [
                {
                    'title': 'Найдите деепричастный оборот в предложении',
                    'description': 'В каком предложении есть деепричастный оборот?\n1) Читая книгу, он делал заметки.\n2) Прочитанная книга лежала на столе.\n3) Он читал книгу внимательно.\n4) Книга была прочитана быстро.',
                    'answer': '1',
                    'difficulty': 2
                },
                {
                    'title': 'Определите тип сказуемого',
                    'description': 'Какой тип сказуемого в предложении "Он стал врачом"?',
                    'answer': 'Составное именное сказуемое',
                    'difficulty': 3
                },
                {
                    'title': 'Найдите грамматическую ошибку',
                    'description': 'В каком предложении есть грамматическая ошибка?\n1) Благодаря дождю урожай был хорошим.\n2) Согласно расписанию поезд прибывает в 15:00.\n3) По приезду в город мы пошли в музей.\n4) Вопреки прогнозу погода была солнечной.',
                    'answer': '3',
                    'difficulty': 3
                },
                {
                    'title': 'Определите спряжение глагола',
                    'description': 'К какому спряжению относится глагол "строить"?',
                    'answer': 'II спряжение',
                    'difficulty': 2
                },
                {
                    'title': 'Расставьте знаки препинания',
                    'description': 'Расставьте запятые в предложении: "Когда наступила весна птицы вернулись из теплых стран"',
                    'answer': 'Когда наступила весна, птицы вернулись из теплых стран.',
                    'difficulty': 2
                }
            ]
            
            created_count = 0
            
            # Создаем задачи для каждого математического предмета
            for subject in math_subjects:
                for task_data in math_tasks:
                    task, created = Task.objects.get_or_create(  # type: ignore
                        title=task_data['title'],
                        subject=subject,
                        defaults=task_data
                    )
                    if created:
                        created_count += 1
                        
                self.stdout.write(f'✅ Создано задач для {subject.name}: {len(math_tasks)}')
            
            # Создаем задачи для каждого предмета русского языка
            for subject in russian_subjects:
                for task_data in russian_tasks:
                    task, created = Task.objects.get_or_create(  # type: ignore
                        title=task_data['title'],
                        subject=subject,
                        defaults=task_data
                    )
                    if created:
                        created_count += 1
                        
                self.stdout.write(f'✅ Создано задач для {subject.name}: {len(russian_tasks)}')
            
            # Статистика
            total_tasks = Task.objects.count()  # type: ignore
            self.stdout.write('=' * 50)
            self.stdout.write(f'🎉 СОЗДАНО НОВЫХ ЗАДАЧ: {created_count}')
            self.stdout.write(f'📊 ВСЕГО ЗАДАЧ В БАЗЕ: {total_tasks}')
            self.stdout.write('✅ Задачи готовы для использования!')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Ошибка: {e}'))  # type: ignore

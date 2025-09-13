"""
Команда для инициализации фокусированных предметов
Создает предметы математики и русского языка с полным наполнением
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from learning.models import Subject, Topic, Task
from core.fipi_parser import FipiParser
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Инициализация фокусированных предметов (математика и русский язык)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистить существующие данные перед созданием',
        )
        parser.add_argument(
            '--load-data',
            action='store_true',
            help='Загрузить данные с ФИПИ',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.clear_existing_data()

        self.create_focused_subjects()

        if options['load_data']:
            self.load_fipi_data()

        self.stdout.write(
            self.style.SUCCESS(  # type: ignore
                'Фокусированные предметы успешно инициализированы!')  # type: ignore
        )

    def clear_existing_data(self):
        """Очищает существующие данные"""
        self.stdout.write('Очищаем существующие данные...')

        with transaction.atomic():  # type: ignore
            # Удаляем все предметы
            Subject.objects.all().delete()  # type: ignore
            self.stdout.write('  - Удалены все предметы')

            # Удаляем все темы
            Topic.objects.all().delete()  # type: ignore
            self.stdout.write('  - Удалены все темы')

            # Удаляем все задания
            Task.objects.all().delete()  # type: ignore
            self.stdout.write('  - Удалены все задания')

    def create_focused_subjects(self):
        """Создает фокусированные предметы"""
        self.stdout.write('Создаем фокусированные предметы...')

        subjects_data = [
            # Математика
                'name': 'Математика (профильная)',
                'code': 'math_pro',
                'exam_type': 'ЕГЭ',
                'description': 'Профильная математика ЕГЭ - задания 1-19 с полными решениями',
                'icon': '📐',
                'is_primary': True,
                'topics': [
                    'Алгебра',
                    'Геометрия',
                    'Тригонометрия',
                    'Производная и интеграл',
                    'Теория вероятностей',
                    'Стереометрия',
                    'Планиметрия',
                    'Уравнения и неравенства',
                    'Функции и графики',
                    'Логарифмы и степени'
                ]
            },
                'name': 'Математика (непрофильная)',
                'code': 'math_base',
                'exam_type': 'ЕГЭ',
                'description': 'Базовая математика ЕГЭ - задания 1-20 с пошаговыми объяснениями',
                'icon': '📊',
                'is_primary': True,
                'topics': [
                    'Арифметика',
                    'Алгебра',
                    'Геометрия',
                    'Тригонометрия',
                    'Функции',
                    'Статистика и вероятность',
                    'Практические задачи'
                ]
            },
                'name': 'Математика (ОГЭ)',
                'code': 'math_oge',
                'exam_type': 'ОГЭ',
                'description': 'Математика ОГЭ - задания 1-26 с детальными разборами',
                'icon': '🔢',
                'is_primary': True,
                'topics': [
                    'Числа и вычисления',
                    'Алгебраические выражения',
                    'Уравнения и неравенства',
                    'Функции и графики',
                    'Геометрия',
                    'Статистика и вероятность',
                    'Практические задачи'
                ]
            },
            # Русский язык
                'name': 'Русский язык (ЕГЭ)',
                'code': 'russian_ege',
                'exam_type': 'ЕГЭ',
                'description': 'Русский язык ЕГЭ - сочинение, тесты, грамматические нормы',
                'icon': '📝',
                'is_primary': True,
                'topics': [
                    'Сочинение (задание 27)',
                    'Изложение (задания 1-3)',
                    'Орфография',
                    'Пунктуация',
                    'Лексические нормы',
                    'Синтаксические нормы',
                    'Морфологические нормы',
                    'Средства выразительности',
                    'Типы речи',
                    'Стили речи'
                ]
            },
                'name': 'Русский язык (ОГЭ)',
                'code': 'russian_oge',
                'exam_type': 'ОГЭ',
                'description': 'Русский язык ОГЭ - изложение, сочинение, тестовые задания',
                'icon': '📖',
                'is_primary': True,
                'topics': [
                    'Изложение',
                    'Сочинение',
                    'Орфография',
                    'Пунктуация',
                    'Грамматика',
                    'Лексика',
                    'Синтаксис',
                    'Морфология',
                    'Фонетика',
                    'Словообразование'
                ]
            }
        ]

        created_subjects = []

        with transaction.atomic():  # type: ignore
            for subject_data in subjects_data:
                subject, created = Subject.objects.get_or_create(  # type: ignore
                    name=subject_data['name'],
                    defaults={
                        'code': subject_data['code'],
                        'exam_type': subject_data['exam_type'],
                        'description': subject_data['description'],
                        'icon': subject_data['icon'],
                        'is_primary': subject_data['is_primary']
                    }
                )

                if created:
                    self.stdout.write('  ✓ Создан предмет: {subject.name}')
                else:
                    self.stdout.write('  - Предмет уже существует: {subject.name}')

                # Создаем темы для предмета
                self.create_topics_for_subject(subject, subject_data['topics'])

                created_subjects.append(subject)

        return created_subjects

    def create_topics_for_subject(self, subject, topics_data):
        """Создает темы для предмета"""
        for i, topic_name in enumerate(topics_data):
            # Создаем короткий код для темы
            topic_code = "topic_{i+1:02d}"

            topic, created = Topic.objects.get_or_create(  # type: ignore
                name=topic_name,
                subject=subject,
                defaults={
                    'code': topic_code
                }
            )

            if created:
                self.stdout.write('    ✓ Создана тема: {topic_name}')

    def load_fipi_data(self):
        """Загружает данные с ФИПИ"""
        self.stdout.write('Загружаем данные с ФИПИ...')

        try:
            parser = FipiParser()

            # Получаем предметы
            subjects = Subject.objects.filter(is_primary=True)  # type: ignore

            for subject in subjects:
                self.stdout.write('  Загружаем данные для {subject.name}...')

                # Определяем тип экзамена для парсера
                exam_type = 'ЕГЭ' if subject.exam_type == 'ЕГЭ' else 'ОГЭ'

                # Парсим задания
                tasks_data = parser.parse_tasks_for_subject(
                    subject.name.split('(')[0].strip(),
                    exam_type
                )

                # Создаем задания
                created_tasks = 0
                # Ограничиваем количество для тестирования
                for task_data in tasks_data[:50]:
                    task, created = Task.objects.get_or_create(  # type: ignore
                        title=task_data.get('title', 'Задание'),
                        subject=subject,
                        defaults={
                            'description': task_data.get('description', ''),
                            'difficulty': task_data.get('difficulty', 'medium'),
                            'solution': task_data.get('solution', ''),
                            'answer': task_data.get('answer', '')
                        }
                    )

                    if created:
                        created_tasks += 1

                self.stdout.write('    ✓ Создано заданий: {created_tasks}')

        except Exception as e:
            self.stdout.write(
                # type: ignore
                # type: ignore
                self.style.ERROR('Ошибка при загрузке данных с ФИПИ: {e}')
            )
            logger.error('Ошибка при загрузке данных с ФИПИ: {e}')

    def show_statistics(self):
        """Показывает статистику созданных данных"""
        self.stdout.write('\nСтатистика:')

        subjects = Subject.objects.filter(is_primary=True)  # type: ignore
        self.stdout.write('  Предметов: {subjects.count()}')

        topics = Topic.objects.filter(subject__in=subjects)  # type: ignore
        self.stdout.write('  Тем: {topics.count()}')

        tasks = Task.objects.filter(subject__in=subjects)  # type: ignore
        self.stdout.write('  Заданий: {tasks.count()}')

        # Статистика по предметам
        for subject in subjects:
            subject_topics = topics.filter(subject=subject).count()  # type: ignore
            subject_tasks = tasks.filter(subject=subject).count()  # type: ignore
            self.stdout.write(
                '    {subject.name}: {subject_topics} тем, {subject_tasks} заданий')

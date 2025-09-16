"""
Команда для исправления предметов - оставляет только математику и русский язык
"""

from django.core.management.base import BaseCommand
from learning.models import Subject

class Command(BaseCommand):
    help = 'Исправляет предметы - оставляет только математику и русский язык'

    def handle(self, *args, **options):
        self.stdout.write('Исправляем предметы...')

        # Удаляем все предметы
        Subject.objects.all().delete()  # type: ignore
        self.stdout.write('Все предметы удалены')

        # Создаем только нужные предметы
        subjects_data = [
            {
                'name': 'Математика (профильная)',
                'code': 'math_pro',
                'exam_type': 'ЕГЭ',
                'description': 'Профильная математика ЕГЭ - задания 1-19',
                'icon': '📐',
                'is_primary': True,
                'is_archived': False,
            },
            {
                'name': 'Математика (непрофильная)',
                'code': 'math_base',
                'exam_type': 'ЕГЭ',
                'description': 'Базовая математика ЕГЭ - задания 1-20',
                'icon': '📊',
                'is_primary': True,
                'is_archived': False,
            },
            {
                'name': 'Математика (ОГЭ)',
                'code': 'math_oge',
                'exam_type': 'ОГЭ',
                'description': 'Математика ОГЭ - задания 1-26',
                'icon': '🔢',
                'is_primary': True,
                'is_archived': False,
            },
            {
                'name': 'Русский язык (ЕГЭ)',
                'code': 'russian_ege',
                'exam_type': 'ЕГЭ',
                'description': 'Русский язык ЕГЭ - сочинение, тесты, грамматика',
                'icon': '📝',
                'is_primary': True,
                'is_archived': False,
            },
            {
                'name': 'Русский язык (ОГЭ)',
                'code': 'russian_oge',
                'exam_type': 'ОГЭ',
                'description': 'Русский язык ОГЭ - изложение, сочинение, тесты',
                'icon': '📖',
                'is_primary': True,
                'is_archived': False,
            },
        ]

        for data in subjects_data:
            subject = Subject.objects.create(**data)  # type: ignore
            self.stdout.write(f'✓ Создан предмет: {subject.name}')

        self.stdout.write(self.style.SUCCESS( # type: ignore
            'Предметы исправлены! Теперь только математика и русский язык.'))  # type: ignore

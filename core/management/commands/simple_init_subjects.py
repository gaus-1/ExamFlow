"""
Простая команда для инициализации предметов
"""

from django.core.management.base import BaseCommand
from learning.models import Subject, Topic
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Простая инициализация предметов математики и русского языка'

    def handle(self, *args, **options):
        self.stdout.write('Создаем предметы математики и русского языка...')
        
        # Создаем предметы
        subjects_data = [
            {
                'name': 'Математика (профильная)',
                'code': 'math_prof',
                'exam_type': 'ЕГЭ',
                'description': 'Профильная математика ЕГЭ - задания 1-19',
                'icon': '📐',
                'is_primary': True
            },
            {
                'name': 'Математика (непрофильная)',
                'code': 'math_base',
                'exam_type': 'ЕГЭ',
                'description': 'Базовая математика ЕГЭ - задания 1-20',
                'icon': '📊',
                'is_primary': True
            },
            {
                'name': 'Математика (ОГЭ)',
                'code': 'math_oge',
                'exam_type': 'ОГЭ',
                'description': 'Математика ОГЭ - задания 1-26',
                'icon': '🔢',
                'is_primary': True
            },
            {
                'name': 'Русский язык (ЕГЭ)',
                'code': 'russian_ege',
                'exam_type': 'ЕГЭ',
                'description': 'Русский язык ЕГЭ - сочинение, тесты, грамматика',
                'icon': '📝',
                'is_primary': True
            },
            {
                'name': 'Русский язык (ОГЭ)',
                'code': 'russian_oge',
                'exam_type': 'ОГЭ',
                'description': 'Русский язык ОГЭ - изложение, сочинение, тесты',
                'icon': '📖',
                'is_primary': True
            },
        ]
        
        created_count = 0
        
        for subject_data in subjects_data:
            subject, created = Subject.objects.get_or_create(
                name=subject_data['name'],
                defaults=subject_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'  ✓ Создан предмет: {subject.name}')
            else:
                self.stdout.write(f'  - Предмет уже существует: {subject.name}')
        
        # Архивируем ненужные предметы
        unused_subjects = [
            'Физика', 'Химия', 'Биология', 'История', 'География',
            'Литература', 'Информатика', 'Обществознание',
            'Английский язык', 'Немецкий язык', 'Французский язык', 'Испанский язык'
        ]
        
        archived_count = 0
        for subject_name in unused_subjects:
            updated = Subject.objects.filter(name=subject_name).update(is_archived=True)
            if updated:
                archived_count += 1
        
        self.stdout.write(f'  ✓ Архивировано предметов: {archived_count}')
        self.stdout.write(f'  ✓ Создано предметов: {created_count}')
        
        # Показываем статистику
        total_subjects = Subject.objects.count()
        primary_subjects = Subject.objects.filter(is_primary=True).count()
        archived_subjects = Subject.objects.filter(is_archived=True).count()
        
        self.stdout.write(f'\nСтатистика:')
        self.stdout.write(f'  Всего предметов: {total_subjects}')
        self.stdout.write(f'  Основных предметов: {primary_subjects}')
        self.stdout.write(f'  Архивированных предметов: {archived_subjects}')
        
        self.stdout.write(
            self.style.SUCCESS('\nПредметы успешно инициализированы!')
        )

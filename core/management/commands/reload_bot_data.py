"""
Команда для перезагрузки данных бота
Очищает старые данные и загружает новые с ответами
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from core.models import Task, Subject, UserProgress, UserRating
from django.db import connection


class Command(BaseCommand):
    help = 'Перезагружает данные для бота (очищает старые и загружает новые)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Принудительно перезагрузить все данные',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING('🔄 ПЕРЕЗАГРУЗКА ДАННЫХ ДЛЯ БОТА')
        )
        self.stdout.write('=' * 50)
        
        # Проверяем текущее состояние
        subjects_count = Subject.objects.count()
        tasks_count = Task.objects.count()
        
        self.stdout.write(f'📊 Текущее состояние:')
        self.stdout.write(f'   Предметов: {subjects_count}')
        self.stdout.write(f'   Заданий: {tasks_count}')
        
        if not options['force'] and tasks_count > 0:
            self.stdout.write(
                self.style.WARNING('⚠️  Данные уже есть. Используйте --force для перезагрузки')
            )
            return
        
        # Очищаем старые данные
        self.stdout.write('🗑️  Очистка старых данных...')
        
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM core_userprogress")
            cursor.execute("DELETE FROM core_userrating")
            cursor.execute("DELETE FROM core_task")
            cursor.execute("DELETE FROM core_subject")
        
        self.stdout.write(self.style.SUCCESS('✅ Старые данные очищены'))
        
        # Загружаем новые данные
        self.stdout.write('📥 Загрузка новых данных...')
        call_command('load_sample_data')
        
        # Проверяем результат
        new_subjects_count = Subject.objects.count()
        new_tasks_count = Task.objects.count()
        
        self.stdout.write(f'📊 Новое состояние:')
        self.stdout.write(f'   Предметов: {new_subjects_count}')
        self.stdout.write(f'   Заданий: {new_tasks_count}')
        
        # Проверяем, что у заданий есть ответы
        tasks_with_answers = Task.objects.filter(answer__isnull=False).exclude(answer='').count()
        self.stdout.write(f'   Заданий с ответами: {tasks_with_answers}')
        
        if tasks_with_answers == 0:
            self.stdout.write(
                self.style.ERROR('❌ КРИТИЧЕСКАЯ ОШИБКА: Нет заданий с ответами!')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('🎉 Данные успешно перезагружены! Бот готов к работе.')
            )

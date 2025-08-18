"""
Команда для полного парсинга всех материалов ФИПИ
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
from core.models import Subject, Task
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Запускает полный парсинг всех материалов ФИПИ'

    def add_arguments(self, parser):
        parser.add_argument(
            '--quick',
            action='store_true',
            help='Быстрый парсинг (только основные предметы)',
        )
        parser.add_argument(
            '--with-voices',
            action='store_true',
            help='Генерировать голосовые подсказки после парсинга',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 ЗАПУСК ПОЛНОГО ПАРСИНГА МАТЕРИАЛОВ ФИПИ')
        )
        self.stdout.write('=' * 60)
        
        # Проверяем подключение к базе данных
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            self.stdout.write(self.style.SUCCESS('✅ Подключение к базе данных: OK'))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка подключения к БД: {str(e)}')
            )
            return
        
        # Показываем текущее состояние
        subjects_count = Subject.objects.count()
        tasks_count = Task.objects.count()
        
        self.stdout.write(f'📊 Текущее состояние:')
        self.stdout.write(f'   Предметов: {subjects_count}')
        self.stdout.write(f'   Заданий: {tasks_count}')
        self.stdout.write('')
        
        # Определяем список предметов для парсинга
        if options['quick']:
            subjects_groups = [
                ['математика', 'физика', 'русский_язык']
            ]
            self.stdout.write(
                self.style.WARNING('⚡ БЫСТРЫЙ РЕЖИМ: только основные предметы')
            )
        else:
            subjects_groups = [
                ['математика', 'физика', 'химия'],
                ['биология', 'история', 'обществознание'],
                ['русский_язык', 'информатика', 'литература'],
                ['география', 'английский_язык']
            ]
            self.stdout.write(
                self.style.SUCCESS('🔥 ПОЛНЫЙ РЕЖИМ: все предметы')
            )
        
        # Выполняем парсинг по группам
        total_new_subjects = 0
        total_new_tasks = 0
        
        for i, subjects_group in enumerate(subjects_groups, 1):
            self.stdout.write(f'\n📋 Группа {i}/{len(subjects_groups)}: {", ".join(subjects_group)}')
            
            try:
                # Запускаем парсинг группы предметов
                call_command(
                    'load_fipi_data',
                    subjects=subjects_group,
                    verbosity=1
                )
                
                # Проверяем результат
                new_subjects_count = Subject.objects.count()
                new_tasks_count = Task.objects.count()
                
                group_subjects = new_subjects_count - subjects_count
                group_tasks = new_tasks_count - tasks_count
                
                if group_subjects > 0 or group_tasks > 0:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Группа {i}: +{group_subjects} предметов, +{group_tasks} заданий')
                    )
                    total_new_subjects += group_subjects
                    total_new_tasks += group_tasks
                else:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️ Группа {i}: нет новых данных')
                    )
                
                subjects_count = new_subjects_count
                tasks_count = new_tasks_count
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Ошибка в группе {i}: {str(e)}')
                )
                continue
        
        # Генерация голосовых подсказок
        if options['with_voices'] and total_new_tasks > 0:
            self.stdout.write(f'\n🎤 Генерация голосовых подсказок...')
            try:
                call_command('generate_voices', limit=min(100, total_new_tasks))
                self.stdout.write(
                    self.style.SUCCESS('✅ Голосовые подсказки сгенерированы')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Ошибка генерации голоса: {str(e)}')
                )
        
        # Финальный отчет
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(
            self.style.SUCCESS('📊 ИТОГИ ПАРСИНГА:')
        )
        self.stdout.write(f'📚 Всего предметов: {Subject.objects.count()}')
        self.stdout.write(f'📝 Всего заданий: {Task.objects.count()}')
        self.stdout.write(f'✨ Новых предметов: +{total_new_subjects}')
        self.stdout.write(f'🎯 Новых заданий: +{total_new_tasks}')
        
        if total_new_subjects > 0 or total_new_tasks > 0:
            self.stdout.write(
                self.style.SUCCESS('\n🎉 ПАРСИНГ ЗАВЕРШЕН УСПЕШНО!')
            )
            self.stdout.write('🌐 Материалы ФИПИ загружены на сайт')
            self.stdout.write('🔗 Проверьте: https://examflow.ru')
        else:
            self.stdout.write(
                self.style.WARNING('\n⚠️ Новых материалов не найдено')
            )
            self.stdout.write('🔄 Возможно, данные уже актуальны')
        
        # Рекомендации
        self.stdout.write(f'\n💡 РЕКОМЕНДАЦИИ:')
        if not options['with_voices'] and total_new_tasks > 0:
            self.stdout.write('🎤 Запустите: python manage.py generate_voices --limit 50')
        
        self.stdout.write('🤖 Настройте webhook: python manage.py setup_webhook set')
        self.stdout.write('📱 Протестируйте бота через сайт')

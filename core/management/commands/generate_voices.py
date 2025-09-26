"""
Команда Django для генерации голосовых файлов
"""

from django.core.management.base import BaseCommand, CommandError
from core.voice_service import voice_service
from core.models import Task  # type: ignore
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Генерирует голосовые файлы для заданий'

    def add_arguments(self, parser):
        parser.add_argument(
            '--task-id',
            type=int,
            help='Сгенерировать аудио только для указанного задания',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Максимальное количество заданий для обработки (по умолчанию: 50)',
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Очистить старые аудиофайлы (старше 30 дней)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Принудительно перегенерировать существующие аудиофайлы',
        )

    def handle(self, *args, **options):
        if options['cleanup']:
            self.cleanup_old_files()
            return

        if options['task_id']:
            self.generate_single_task(options['task_id'])
        else:
            self.generate_multiple_tasks(options['limit'], options['force'])

    def generate_single_task(self, task_id):
        """Генерирует аудио для одного задания"""
        try:
            task = Task.objects.get(id=task_id)
            self.stdout.write('🎤 Генерация аудио для задания: {task.title}')

            result = voice_service.generate_task_audio(task)

            if result and result['task_audio']:
                self.stdout.write(
                    self.style.SUCCESS(
                        '✅ Аудио создано: {result["task_audio"]}')  # type: ignore
                )
                if result['solution_audio']:
                    self.stdout.write(
                        self.style.SUCCESS(
                            '✅ Аудио решения: {result["solution_audio"]}')  # type: ignore
                    )
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Ошибка создания аудио')  # type: ignore
                )

        except Task.DoesNotExist:
            raise CommandError('❌ Задание с ID {task_id} не найдено')
        except Exception:
            raise CommandError('❌ Ошибка: {str(e)}')

    def generate_multiple_tasks(self, limit, force):
        """Генерирует аудио для множества заданий"""
        self.stdout.write(
            self.style.SUCCESS(
                '🎤 Начинаем генерацию голосовых файлов...')  # type: ignore
        )

        # Выбираем задания
        if force:
            tasks = Task.objects.filter(is_active=True)[:limit]
            self.stdout.write('📋 Принудительная генерация для {tasks.count()} заданий')
        else:
            tasks = Task.objects.filter(is_active=True, audio_file__isnull=True)[:limit]
            self.stdout.write('📋 Генерация для {tasks.count()} заданий без аудио')

        if not tasks:
            self.stdout.write(
                self.style.WARNING('⚠️  Нет заданий для обработки')  # type: ignore
            )
            return

        generated_count = 0
        error_count = 0

        for i, task in enumerate(tasks, 1):
            try:
                self.stdout.write('[{i}/{len(tasks)}] Обработка: {task.title[:50]}...')

                result = voice_service.generate_task_audio(task)

                if result and result['task_audio']:
                    generated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            '  ✅ Создано: {result["task_audio"]}')  # type: ignore
                    )
                else:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR('  ❌ Ошибка создания аудио')  # type: ignore
                    )

                # Показываем прогресс каждые 10 заданий
                if i % 10 == 0:
                    self.stdout.write(
                        self.style.WARNING(
                            '📊 Прогресс: {i}/{len(tasks)} | Создано: {generated_count} | Ошибок: {error_count}')  # type: ignore
                    )

            except Exception:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR('  ❌ Ошибка: {str(e)}')  # type: ignore
                )
                continue

        self.stdout.write(
            self.style.SUCCESS(  # type: ignore
                '🎉 Генерация завершена!'  # type: ignore
            )
        )
        self.stdout.write(
            self.style.SUCCESS(  # type: ignore
                '📊 Создано файлов: {generated_count}'  # type: ignore
            )
        )
        if error_count > 0:
            self.stdout.write(
                self.style.WARNING(  # type: ignore
                    '⚠️  Ошибок: {error_count}'  # type: ignore
                )
            )

    def cleanup_old_files(self):
        """Очищает старые аудиофайлы"""
        self.stdout.write('🧹 Очистка старых аудиофайлов...')

        deleted_count = voice_service.cleanup_old_audio(days=30)

        self.stdout.write(
            self.style.SUCCESS(  # type: ignore
                '✅ Удалено файлов: {deleted_count}'  # type: ignore
            )
        )

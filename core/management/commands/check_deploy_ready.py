"""
Команда для проверки готовности ExamFlow 2.0 к деплою
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from django.db import connection
import os
import sys


class Command(BaseCommand):
    help = 'Проверяет готовность ExamFlow 2.0 к деплою на Render'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Подробный вывод',
        )

    def handle(self, *args, **options):
        verbose = options['verbose']

        self.stdout.write(
            self.style.SUCCESS(
                '🚀 Проверка готовности ExamFlow 2.0 к деплою')  # type: ignore
        )
        self.stdout.write('=' * 60)
        # Счетчики
        total_checks = 0
        passed_checks = 0
        failed_checks = 0

        # 1. Проверка Django конфигурации
        self.stdout.write('\n1️⃣ Проверка Django конфигурации...')
        total_checks += 1
        try:
            call_command('check', '--deploy', verbosity=0)
            self.stdout.write(
                self.style.SUCCESS('   ✅ Django конфигурация корректна')  # type: ignore
            )
            passed_checks += 1
        except Exception as e:
            self.stdout.write(
                # type: ignore
                self.style.ERROR(f'   ❌ Ошибка Django конфигурации: {e}')
            )
            failed_checks += 1

        # 2. Проверка базы данных
        self.stdout.write('\n2️⃣ Проверка базы данных...')
        total_checks += 1
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                self.stdout.write(
                    self.style.SUCCESS('   ✅ База данных доступна')  # type: ignore
                )
                passed_checks += 1
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'   ❌ Ошибка базы данных: {e}')  # type: ignore
            )
            failed_checks += 1

        # 3. Проверка миграций
        self.stdout.write('\n3️⃣ Проверка миграций...')
        total_checks += 1
        try:
            call_command('showmigrations', verbosity=0)
            self.stdout.write(
                self.style.SUCCESS('   ✅ Миграции в порядке')  # type: ignore
            )
            passed_checks += 1
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'   ❌ Ошибка миграций: {e}')  # type: ignore
            )
            failed_checks += 1

        # 4. Проверка статических файлов
        self.stdout.write('\n4️⃣ Проверка статических файлов...')
        total_checks += 1
        try:
            # Проверяем наличие статических файлов без интерактивного ввода
            static_root = getattr(settings, 'STATIC_ROOT', None)
            if static_root and os.path.exists(static_root):
                static_files = os.listdir(static_root)
                if len(static_files) > 0:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'   ✅ Статические файлы готовы ({len(static_files)} файлов)')  # type: ignore
                    )
                    passed_checks += 1
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            '   ⚠️  Папка статических файлов пуста')  # type: ignore
                    )
                    failed_checks += 1
            else:
                # Если STATIC_ROOT не настроен, проверяем STATICFILES_DIRS
                static_dirs = getattr(settings, 'STATICFILES_DIRS', [])
                if static_dirs:
                    self.stdout.write(
                        self.style.SUCCESS(
                            '   ✅ Статические файлы настроены через STATICFILES_DIRS')  # type: ignore
                    )
                    passed_checks += 1
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            '   ⚠️  Статические файлы не настроены')  # type: ignore
                    )
                    failed_checks += 1
        except Exception as e:
            self.stdout.write(
                # type: ignore
                self.style.ERROR(f'   ❌ Ошибка проверки статических файлов: {e}')
            )
            failed_checks += 1

        # 5. Проверка переменных окружения
        self.stdout.write('\n5️⃣ Проверка переменных окружения...')
        total_checks += 1
        env_checks = 0
        required_vars = [
            'SECRET_KEY',
            'GEMINI_API_KEY',
            'TELEGRAM_BOT_TOKEN',
        ]

        for var in required_vars:
            if os.getenv(var):
                env_checks += 1
                if verbose:
                    self.stdout.write(f'   ✅ {var}: установлен')
            else:
                if verbose:
                    self.stdout.write(f'   ⚠️  {var}: не установлен')

        if env_checks >= len(required_vars) * 0.8:  # 80% переменных
            self.stdout.write(
                self.style.SUCCESS(
                    '   ✅ Переменные окружения настроены')  # type: ignore
            )
            passed_checks += 1
        else:
            self.stdout.write(
                self.style.WARNING(
                    '   ⚠️  Не все переменные окружения установлены')  # type: ignore
            )
            failed_checks += 1

        # 6. Проверка файлов деплоя
        self.stdout.write('\n6️⃣ Проверка файлов деплоя...')
        total_checks += 1
        deploy_files = [
            'build.sh',
            'start.sh',
            'render.yaml',
            'requirements-prod.txt',
            'examflow_project/settings_prod.py',
        ]

        missing_files = []
        for file_path in deploy_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)

        if not missing_files:
            self.stdout.write(
                self.style.SUCCESS('   ✅ Все файлы деплоя присутствуют')  # type: ignore
            )
            passed_checks += 1
        else:
            self.stdout.write(
                # type: ignore
                self.style.ERROR(f'   ❌ Отсутствуют файлы: {", ".join(missing_files)}')
            )
            failed_checks += 1

        # 7. Проверка тестов
        self.stdout.write('\n7️⃣ Проверка тестов...')
        total_checks += 1
        try:
            call_command('test', '--keepdb', verbosity=0)
            self.stdout.write(
                self.style.SUCCESS('   ✅ Все тесты проходят')  # type: ignore
            )
            passed_checks += 1
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'   ❌ Ошибка тестов: {e}')  # type: ignore
            )
            failed_checks += 1

        # Итоги
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('📊 РЕЗУЛЬТАТЫ ПРОВЕРКИ:')
        self.stdout.write(f'   Всего проверок: {total_checks}')
        self.stdout.write(f'   Пройдено: {passed_checks}')
        self.stdout.write(f'   Провалено: {failed_checks}')

        if failed_checks == 0:
            self.stdout.write(
                self.style.SUCCESS('\n🎉 ExamFlow 2.0 ГОТОВ К ДЕПЛОЮ!')  # type: ignore
            )
            self.stdout.write('\n📝 Следующие шаги:')
            self.stdout.write('1. Создайте приложение на Render')
            self.stdout.write('2. Настройте переменные окружения')
            self.stdout.write('3. Подключите Git репозиторий')
            self.stdout.write('4. Запустите деплой')
        else:
            self.stdout.write(
                # type: ignore
                self.style.ERROR(f'\n⚠️  Найдено {failed_checks} проблем!')
            )
            self.stdout.write('Исправьте их перед деплоем.')
            sys.exit(1)

"""
Команда для полной инициализации ExamFlow 2.0
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):  # type: ignore
    help = "Полная инициализация ExamFlow 2.0: миграции, источники ФИПИ, настройка системы"

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-migrations',
            action='store_true',
            help='Пропустить выполнение миграций'
        )
        parser.add_argument(
            '--skip-sources',
            action='store_true',
            help='Пропустить инициализацию источников ФИПИ'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Инициализация ExamFlow 2.0...')  # type: ignore
        )

        try:
            # 1. Выполняем миграции
            if not options['skip_migrations']:
                self.stdout.write(
                    self.style.WARNING('📦 Выполняем миграции...')  # type: ignore
                )
                call_command('migrate', verbosity=0)
                self.stdout.write(
                    self.style.SUCCESS('✅ Миграции выполнены')  # type: ignore
                )

            # 2. Инициализируем источники ФИПИ
            if not options['skip_sources']:
                self.stdout.write(
                    self.style.WARNING( # type: ignore
                        '🗺️ Инициализируем источники ФИПИ...')  # type: ignore
                )
                call_command('init_fipi_source_map', verbosity=0)
                self.stdout.write(
                    self.style.SUCCESS( # type: ignore
                        '✅ Источники ФИПИ инициализированы')  # type: ignore
                )

            # 3. Создаем суперпользователя если не существует
            from django.conf import settings
            if not User.objects.filter(is_superuser=True).exists():  # type: ignore
                self.stdout.write(
                    self.style.WARNING('👤 Создаем суперпользователя...')  # type: ignore
                )
                User.objects.create_superuser(  # type: ignore
                    username='admin',
                    email='admin@examflow.ru',
                    password='admin123'
                )
                self.stdout.write(
                    self.style.SUCCESS( # type: ignore
                        '✅ Суперпользователь создан (admin/admin123)')  # type: ignore
                )

            # 4. Создаем тестовые предметы если не существуют
            from core.models import Subject
            if not Subject.objects.exists():  # type: ignore
                self.stdout.write(
                    self.style.WARNING('📚 Создаем тестовые предметы...')  # type: ignore
                )
                Subject.objects.create(  # type: ignore
                    name='Математика',
                    code='math',
                    exam_type='ege',
                    description='Математика (профильный уровень)',
                    icon='📐'
                )
                Subject.objects.create(  # type: ignore
                    name='Русский язык',
                    code='russian',
                    exam_type='ege',
                    description='Русский язык',
                    icon='📝'
                )
                self.stdout.write(
                    self.style.SUCCESS('✅ Тестовые предметы созданы')  # type: ignore
                )

            # 5. Проверяем настройки
            self.stdout.write(
                self.style.WARNING('⚙️ Проверяем настройки системы...')  # type: ignore
            )

            from django.conf import settings

            # Проверяем GEMINI_API_KEY
            if not getattr(settings, 'GEMINI_API_KEY', None):
                self.stdout.write(
                    self.style.ERROR('⚠️ GEMINI_API_KEY не настроен')  # type: ignore
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('✅ GEMINI_API_KEY настроен')  # type: ignore
                )

            # Проверяем TELEGRAM_BOT_TOKEN
            if not getattr(settings, 'TELEGRAM_BOT_TOKEN', None):
                self.stdout.write(
                    self.style.WARNING( # type: ignore
                        '⚠️ TELEGRAM_BOT_TOKEN не настроен (бот не будет работать)')  # type: ignore
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('✅ TELEGRAM_BOT_TOKEN настроен')  # type: ignore
                )

            # 6. Выводим информацию о доступных командах
            self.stdout.write('\n' + '=' * 60)
            self.stdout.write(
                self.style.SUCCESS( # type: ignore
                    '🎉 ExamFlow 2.0 успешно инициализирован!')  # type: ignore
            )
            self.stdout.write('\n📋 Доступные команды:')
            self.stdout.write('• python manage.py runserver - запуск сервера')
            self.stdout.write(
                '• python manage.py run_telegram_bot - запуск Telegram бота')
            self.stdout.write(
                '• python manage.py run_cdc_monitor --once - проверка обновлений ФИПИ')
            self.stdout.write(
                '• python manage.py init_fipi_source_map - инициализация источников')

            self.stdout.write('\n🌐 Доступные URL:')
            self.stdout.write('• http://localhost:8000/ - главная страница')
            self.stdout.write('• http://localhost:8000/docs/ - Swagger документация')
            self.stdout.write(
                '• http://localhost:8000/subscription/ - страница подписки')
            self.stdout.write('• http://localhost:8000/api/ai/ask/ - AI API')

            self.stdout.write('\n🔧 API эндпоинты:')
            self.stdout.write('• POST /api/ai/ask - AI-помощник')
            self.stdout.write('• GET /api/ai/subjects - список предметов')
            self.stdout.write('• GET /api/ai/user/profile - профиль пользователя')
            self.stdout.write('• POST /api/ai/problem/submit - отправка решения')
            self.stdout.write('• GET /api/fipi/search - поиск по ФИПИ')

            self.stdout.write('\n' + '=' * 60)

        except Exception as e:
            self.stdout.write(
                self.style.ERROR('❌ Ошибка при инициализации: {e}')  # type: ignore
            )
            raise

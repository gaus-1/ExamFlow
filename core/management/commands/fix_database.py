from django.core.management.base import BaseCommand
from django.db import connection
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Принудительно исправляет базу данных ExamFlow'

    def handle(self, *args, **options):
        self.stdout.write('🔧 ПРИНУДИТЕЛЬНОЕ ИСПРАВЛЕНИЕ БАЗЫ ДАННЫХ EXAMFLOW')
        self.stdout.write('=' * 60)

        try:
            # Шаг 1: Проверяем базу данных
            self.stdout.write('📊 Проверяем базу данных...')
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            self.stdout.write(self.style.SUCCESS(
                '✅ База данных доступна'))  # type: ignore

            # Шаг 2: Принудительно создаем недостающие поля
            self.stdout.write('🔄 Создаем недостающие поля...')
            self.create_missing_fields()

            # Шаг 3: Применяем миграции
            self.stdout.write('📦 Применяем миграции...')
            call_command('migrate', '--fake-initial')

            # Шаг 4: Проверяем статус
            self.stdout.write('✅ Проверяем статус миграций...')
            call_command('showmigrations')

            # Шаг 5: Загружаем данные
            self.stdout.write('📚 Загружаем образцы данных...')
            call_command('load_sample_data')

            self.stdout.write('=' * 60)
            self.stdout.write(self.style.SUCCESS(
                '🎉 БАЗА ДАННЫХ ИСПРАВЛЕНА!'))  # type: ignore

        except Exception as e:
            self.stdout.write(self.style.ERROR('❌ Ошибка: {e}'))  # type: ignore

    def create_missing_fields(self):
        """Принудительно создает недостающие поля"""
        with connection.cursor() as cursor:
            # Создаем поле exam_type в learning_subject
            try:
                cursor.execute("""
                    ALTER TABLE learning_subject
                    ADD COLUMN IF NOT EXISTS exam_type VARCHAR(3) DEFAULT 'ЕГЭ';
                """)
                self.stdout.write('✅ Поле exam_type добавлено в learning_subject')
            except Exception as e:
                self.stdout.write('⚠️ exam_type: {e}')

            # Создаем поле code в learning_topic
            try:
                cursor.execute("""
                    ALTER TABLE learning_topic
                    ADD COLUMN IF NOT EXISTS code VARCHAR(20) DEFAULT '';
                """)
                self.stdout.write('✅ Поле code добавлено в learning_topic')
            except Exception as e:
                self.stdout.write('⚠️ code: {e}')

            # Проверяем и создаем таблицы если их нет
            try:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS learning_subject (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        exam_type VARCHAR(3) DEFAULT 'ЕГЭ'
                    );
                """)
                self.stdout.write('✅ Таблица learning_subject проверена/создана')
            except Exception as e:
                self.stdout.write('⚠️ learning_subject: {e}')

            try:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS learning_task (
                        id SERIAL PRIMARY KEY,
                        title VARCHAR(200) NOT NULL,
                        description TEXT,
                        answer VARCHAR(500),
                        source VARCHAR(200),
                        difficulty INTEGER DEFAULT 1,
                        subject_id INTEGER REFERENCES learning_subject(id),
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                self.stdout.write('✅ Таблица learning_task проверена/создана')
            except Exception as e:
                self.stdout.write('⚠️ learning_task: {e}')

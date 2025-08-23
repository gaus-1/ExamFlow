from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import OperationalError
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Исправляет проблемы с миграциями и создает необходимые таблицы'

    def handle(self, *args, **options):
        self.stdout.write('🔧 ИСПРАВЛЕНИЕ МИГРАЦИЙ EXAMFLOW')
        self.stdout.write('=' * 50)
        
        try:
            # Шаг 1: Проверяем базу данных
            self.stdout.write('📊 Проверяем базу данных...')
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            self.stdout.write(self.style.SUCCESS('✅ База данных доступна'))  # type: ignore
            
            # Шаг 2: Создаем таблицы вручную если нужно
            self.stdout.write('🔄 Создаем таблицы вручную...')
            self.create_tables_manually()
            
            # Шаг 3: Применяем миграции
            self.stdout.write('📦 Применяем миграции...')
            call_command('migrate', '--fake-initial')
            
            # Шаг 4: Проверяем статус
            self.stdout.write('✅ Проверяем статус миграций...')
            call_command('showmigrations')
            self.stdout.write('=' * 50)
            self.stdout.write(self.style.SUCCESS('🎉 МИГРАЦИИ ИСПРАВЛЕНЫ!'))  # type: ignore
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Ошибка: {e}'))  # type: ignore

    def create_tables_manually(self):
        """Создает основные таблицы вручную"""
        with connection.cursor() as cursor:
            # Создаем таблицу learning_subject если её нет
            try:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS learning_subject (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        description TEXT,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                self.stdout.write('✅ Таблица learning_subject создана/проверена')
            except Exception as e:
                self.stdout.write(f'⚠️ learning_subject: {e}')
            
            # Создаем таблицу learning_task если её нет
            try:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS learning_task (
                        id SERIAL PRIMARY KEY,
                        title VARCHAR(200) NOT NULL,
                        content TEXT,
                        answer VARCHAR(500),
                        source VARCHAR(200),
                        difficulty INTEGER DEFAULT 1,
                        subject_id INTEGER REFERENCES learning_subject(id),
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                self.stdout.write('✅ Таблица learning_task создана/проверена')
            except Exception as e:
                self.stdout.write(f'⚠️ learning_task: {e}')
            
            # Создаем таблицу authentication_userprofile если её нет
            try:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS authentication_userprofile (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        current_task_id INTEGER,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                self.stdout.write('✅ Таблица authentication_userprofile создана/проверена')
            except Exception as e:
                self.stdout.write(f'⚠️ authentication_userprofile: {e}')

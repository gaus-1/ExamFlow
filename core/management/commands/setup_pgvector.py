"""
Команда для настройки pgvector расширения
"""

from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):  # type: ignore
    help = "Настраивает pgvector расширение и создает необходимые индексы"

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Принудительно пересоздать индексы'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔧 Настройка pgvector расширения...')  # type: ignore
        )

        try:
            with connection.cursor() as cursor:
                # Проверяем, установлено ли расширение
                cursor.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector';")
                if not cursor.fetchone():
                    self.stdout.write(
                        self.style.WARNING(
                            'Устанавливаем расширение pgvector...')  # type: ignore
                    )
                    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                    self.stdout.write(
                        self.style.SUCCESS(
                            '✅ Расширение pgvector установлено')  # type: ignore
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            '✅ Расширение pgvector уже установлено')  # type: ignore
                    )

                # Проверяем, существует ли таблица DataChunk
                cursor.execute("""
                    SELECT 1 FROM information_schema.tables
                    WHERE table_name = 'core_datachunk' AND table_schema = 'public';
                """)
                if not cursor.fetchone():
                    self.stdout.write(
                        # type: ignore
                        self.style.ERROR(
                            '❌ Таблица core_datachunk не найдена. Сначала выполните миграции.')
                    )
                    return

                # Проверяем, есть ли поле embedding_vector
                cursor.execute("""
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'core_datachunk' AND column_name = 'embedding_vector';
                """)
                if not cursor.fetchone():
                    self.stdout.write(
                        self.style.ERROR(
                            '❌ Поле embedding_vector не найдено. Выполните миграцию 0003_setup_pgvector.')  # type: ignore
                    )
                    return

                # Создаем индексы
                if options['force']:
                    self.stdout.write(
                        self.style.WARNING(
                            'Удаляем существующие индексы...')  # type: ignore
                    )
                    cursor.execute("DROP INDEX IF EXISTS datachunk_embedding_idx;")
                    cursor.execute("DROP INDEX IF EXISTS datachunk_subject_idx;")
                    cursor.execute("DROP INDEX IF EXISTS datachunk_document_type_idx;")

                # Создаем ivfflat индекс для векторного поиска
                self.stdout.write(
                    self.style.WARNING(
                        'Создаем ivfflat индекс для векторного поиска...')  # type: ignore
                )
                cursor.execute("""
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS datachunk_embedding_idx
                    ON core_datachunk USING ivfflat (embedding_vector vector_cosine_ops)
                    WITH (lists = 100);
                """)

                # Создаем индексы для фильтрации
                self.stdout.write(
                    self.style.WARNING(
                        'Создаем индексы для фильтрации...')  # type: ignore
                )
                cursor.execute("""
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS datachunk_subject_idx
                    ON core_datachunk (subject);
                """)
                cursor.execute("""
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS datachunk_document_type_idx
                    ON core_datachunk (document_type);
                """)

                self.stdout.write(
                    self.style.SUCCESS('✅ Все индексы созданы успешно')  # type: ignore
                )

                # Проверяем статистику
                cursor.execute("SELECT COUNT(*) FROM core_datachunk;")
                chunk_count = cursor.fetchone()[0]

                cursor.execute(
                    "SELECT COUNT(*) FROM core_datachunk WHERE embedding_vector IS NOT NULL;")
                vector_count = cursor.fetchone()[0]

                self.stdout.write(
                    self.style.SUCCESS(  # type: ignore
                        '📊 Статистика: {chunk_count} чанков, {vector_count} с векторами'
                    )
                )

        except Exception as e:
            self.stdout.write(
                # type: ignore
                self.style.ERROR('❌ Ошибка при настройке pgvector: {e}')
            )
            return

        self.stdout.write(
            self.style.SUCCESS('🎉 Настройка pgvector завершена!')  # type: ignore
        )

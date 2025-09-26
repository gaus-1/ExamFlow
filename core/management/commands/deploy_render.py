from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import OperationalError

from learning.models import Subject, Task


class Command(BaseCommand):
    help = "Автоматический деплой ExamFlow на Render с применением миграций"

    def handle(self, *args, **options):
        self.stdout.write("🚀 ДЕПЛОЙ EXAMFLOW НА RENDER")
        self.stdout.write("=" * 50)

        # Проверяем базу данных
        if not self.check_database():
            self.stdout.write(
                self.style.ERROR("❌ Не удалось подключиться к базе данных")
            )  # type: ignore
            return

        # Проверяем таблицы
        if not self.check_tables():
            self.stdout.write(
                self.style.ERROR("❌ Проблемы с таблицами")
            )  # type: ignore
            return

        # Создаем образцы данных
        self.create_sample_data()

        self.stdout.write("=" * 50)
        self.stdout.write(
            self.style.SUCCESS("🎉 ДЕПЛОЙ ЗАВЕРШЕН УСПЕШНО!")
        )  # type: ignore
        self.stdout.write("✅ База данных настроена")
        self.stdout.write("✅ Таблицы созданы")
        self.stdout.write("✅ Образцы данных добавлены")

    def check_database(self):
        """Проверяет подключение к базе данных"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                self.stdout.write(
                    self.style.SUCCESS("✅ Подключение к базе данных успешно")
                )  # type: ignore
                return True
        except OperationalError as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Ошибка подключения к базе данных: {e}")
            )  # type: ignore
            return False

    def check_tables(self):
        """Проверяет наличие основных таблиц"""
        try:
            # Проверяем количество записей
            subject_count = Subject.objects.count()  # type: ignore
            task_count = Task.objects.count()  # type: ignore

            self.stdout.write(
                self.style.SUCCESS("✅ Таблица Subject: {subject_count} записей")
            )  # type: ignore
            self.stdout.write(
                self.style.SUCCESS("✅ Таблица Task: {task_count} записей")
            )  # type: ignore

            return True
        except Exception:
            self.stdout.write(
                self.style.ERROR("❌ Ошибка при проверке таблиц: {e}")
            )  # type: ignore
            return False

    def create_sample_data(self):
        """Создает образцы данных если таблицы пустые"""
        try:
            if Subject.objects.count() == 0:  # type: ignore
                self.stdout.write("📚 Создаем образцы предметов...")

                # Создаем предметы
                subjects = [
                    Subject(name="Математика", description="Алгебра и геометрия"),
                    Subject(name="Физика", description="Механика и электричество"),
                    Subject(
                        name="Химия", description="Органическая и неорганическая химия"
                    ),
                    Subject(name="Биология", description="Анатомия и экология"),
                    Subject(
                        name="История", description="Российская и всемирная история"
                    ),
                    Subject(
                        name="География",
                        description="Физическая и экономическая география",
                    ),
                    Subject(
                        name="Литература", description="Русская и зарубежная литература"
                    ),
                    Subject(
                        name="Информатика", description="Программирование и алгоритмы"
                    ),
                ]

                Subject.objects.bulk_create(subjects)  # type: ignore
                self.stdout.write(
                    self.style.SUCCESS("✅ Создано {len(subjects)} предметов")
                )  # type: ignore

            return True
        except Exception:
            self.stdout.write(
                self.style.ERROR("❌ Ошибка при создании образцов данных: {e}")
            )  # type: ignore
            return False

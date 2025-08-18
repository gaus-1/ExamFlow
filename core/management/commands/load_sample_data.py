from django.core.management.base import BaseCommand
from core.models import Subject, Task


SUBJECTS_DATA = [
    ("Математика", "ЕГЭ"),
    ("Русский язык", "ЕГЭ"),
    ("Физика", "ЕГЭ"),
    ("Химия", "ЕГЭ"),
    ("Биология", "ЕГЭ"),
    ("История", "ЕГЭ"),
    ("Обществознание", "ЕГЭ"),
    ("Информатика", "ЕГЭ"),
]

SAMPLE_TASKS = [
    ("Математика", "Решение квадратного уравнения", "Решите уравнение: x² - 5x + 6 = 0", 2),
    ("Математика", "Площадь треугольника", "Найдите площадь треугольника со сторонами 3, 4, 5", 1),
    ("Математика", "Производная функции", "Найдите производную функции f(x) = x³ - 2x + 1", 3),
    ("Физика", "Закон Ома", "При напряжении 12 В сила тока равна 2 А. Найдите сопротивление", 1),
    ("Физика", "Кинематика", "Тело движется с ускорением 2 м/с². Какой путь пройдёт за 5 секунд?", 2),
    ("Русский язык", "Орфография", "Вставьте пропущенные буквы в слове: пр_красный", 1),
    ("Русский язык", "Синтаксис", "Определите тип сложного предложения", 2),
    ("Химия", "Периодическая система", "Определите валентность элемента в соединении", 2),
    ("История", "Древняя Русь", "В каком году произошло крещение Руси?", 1),
    ("Биология", "Клетка", "Назовите основные органоиды растительной клетки", 2),
]


class Command(BaseCommand):
    help = "Загружает демонстрационные предметы и задания"

    def handle(self, *args, **options):
        created_subjects = 0
        created_tasks = 0

        # Создаём предметы
        for name, exam_type in SUBJECTS_DATA:
            subject, created = Subject.objects.get_or_create(
                name=name,
                defaults={"exam_type": exam_type}
            )
            if created:
                created_subjects += 1
                self.stdout.write(f"✅ Создан предмет: {name}")

        # Создаём задания
        for subject_name, title, description, difficulty in SAMPLE_TASKS:
            try:
                subject = Subject.objects.get(name=subject_name)
                task, created = Task.objects.get_or_create(
                    title=title,
                    subject=subject,
                    defaults={
                        "description": description,
                        "difficulty": difficulty
                    }
                )
                if created:
                    created_tasks += 1
                    self.stdout.write(f"✅ Создано задание: {title}")
            except Subject.DoesNotExist:
                self.stdout.write(f"❌ Предмет {subject_name} не найден")

        self.stdout.write(
            self.style.SUCCESS(
                f"🎉 Готово! Создано предметов: {created_subjects}, заданий: {created_tasks}"
            )
        )
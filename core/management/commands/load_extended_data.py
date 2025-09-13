from django.core.management.base import BaseCommand
from core.models import Subject, Task
import random

class Command(BaseCommand):
    help = "Загружает расширенную базу заданий по всем предметам"

    def add_arguments(self, parser):
        parser.add_argument(
            '--subject',
            type=str,
            help='Загрузить задания только для указанного предмета'
        )
        parser.add_argument(
            '--count',
            type=int,
            default=50,
            help='Количество заданий для каждого предмета (по умолчанию 50)'
        )

    def handle(self, *args, **options):
        subject_filter = options.get('subject')
        tasks_per_subject = options.get('count', 50)

        # Математика - задания
        math_tasks = [
        ]

        # Физика - задания
        physics_tasks = [
        ]

        # Русский язык - задания
        russian_tasks = [
        ]

        # Химия - задания
        chemistry_tasks = [
        ]

        # Биология - задания
        biology_tasks = [
        ]

        # История - задания
        history_tasks = [
        ]

        # Обществознание - задания
        social_tasks = [
        ]

        # Информатика - задания
        informatics_tasks = [
        ]

        subjects_tasks = {
            'Математика': math_tasks,
            'Физика': physics_tasks,
            'Русский язык': russian_tasks,
            'Химия': chemistry_tasks,
            'Биология': biology_tasks,
            'История': history_tasks,
            'Обществознание': social_tasks,
            'Информатика': informatics_tasks,
        }

        total_created = 0

        for subject_name, base_tasks in subjects_tasks.items():
            if subject_filter and subject_name != subject_filter:
                continue

            try:
                subject = Subject.objects.get(name=subject_name)
            except Subject.DoesNotExist:
                self.stdout.write("❌ Предмет {subject_name} не найден")
                continue

            created_for_subject = 0

            # Создаём базовые задания
            for title, description, difficulty, answer in base_tasks:
                task, created = Task.objects.get_or_create(
                    title=title,
                    subject=subject,
                    defaults={
                        'description': description,
                        'difficulty': difficulty,
                        'answer': answer
                    }
                )
                if created:
                    created_for_subject += 1

            # Генерируем дополнительные задания
            additional_count = max(0, tasks_per_subject - len(base_tasks))
            for i in range(additional_count):
                base_task = random.choice(base_tasks)
                title = "{base_task[0]} - вариант {i+1}"
                description = "Дополнительное задание по теме: {base_task[0].lower()}"
                difficulty = random.choice([1, 2, 3])

                task, created = Task.objects.get_or_create(
                    title=title,
                    subject=subject,
                    defaults={
                        'description': description,
                        'difficulty': difficulty,
                        'answer': "Ответ к заданию {i+1}"
                    }
                )
                if created:
                    created_for_subject += 1

            total_created += created_for_subject
            self.stdout.write(
                "✅ {subject_name}: создано {created_for_subject} заданий")

        self.stdout.write(
            self.style.SUCCESS("🎉 Всего создано {total_created} заданий!")
        )

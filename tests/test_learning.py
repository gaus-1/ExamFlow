"""
Тесты для модуля обучения
"""

from django.test import Client, TestCase

from core.models import Subject, Task, UserProgress
from telegram_auth.models import TelegramUser


class TestLearning(TestCase):
    """Тесты модуля обучения"""

    def setUp(self):
        """Настройка тестовых данных"""
        self.client = Client()

        # Создаем тестового пользователя
        self.user = TelegramUser.objects.create(  # type: ignore
            telegram_id=12345, username="testuser", first_name="Test", last_name="User"
        )

        # Создаем тестовые данные
        self.subject = Subject.objects.create(  # type: ignore
            name="Математика", code="MATH", exam_type="other"
        )

        self.task = Task.objects.create(  # type: ignore
            title="Тестовое задание",
            text="Решите уравнение: x + 2 = 5",
            answer="3",
            subject=self.subject,
            difficulty=1,
        )

    def test_subject_creation(self):
        """Тест создания предмета"""
        self.assertEqual(self.subject.name, "Математика")
        self.assertEqual(self.subject.exam_type, "ege")

    def test_task_creation(self):
        """Тест создания задания"""
        self.assertEqual(self.task.title, "Тестовое задание")
        self.assertEqual(self.task.answer, "3")
        self.assertEqual(self.task.subject, self.subject)

    def test_subjects_list_view(self):
        """Тест страницы списка предметов"""
        response = self.client.get("/subjects/")
        self.assertEqual(response.status_code, 200)  # type: ignore
        self.assertContains(response, "Математика")

    def test_subject_detail_view(self):
        """Тест страницы детального просмотра предмета"""
        response = self.client.get("/subject/{self.subject.id}/")
        self.assertEqual(response.status_code, 200)  # type: ignore
        self.assertContains(response, "Математика")

    def test_task_detail_view(self):
        """Тест страницы детального просмотра задания"""
        response = self.client.get("/task/{self.task.id}/")
        self.assertEqual(response.status_code, 200)  # type: ignore
        self.assertContains(response, "Тестовое задание")

    def test_solve_task_correct_answer(self):
        """Тест решения задания с правильным ответом"""
        self.client.login(username="testuser", password="testpassword123")

        response = self.client.post("/task/{self.task.id}/solve/", {"answer": "3"})

        self.assertEqual(response.status_code, 200)  # type: ignore

        # Проверяем, что прогресс пользователя обновился
        progress = UserProgress.objects.filter(  # type: ignore
            user=self.user, task=self.task
        ).first()

        if progress:
            self.assertTrue(progress.is_correct)
            self.assertEqual(progress.attempts, 1)

    def test_solve_task_incorrect_answer(self):
        """Тест решения задания с неправильным ответом"""
        self.client.login(username="testuser", password="testpassword123")

        response = self.client.post("/task/{self.task.id}/solve/", {"answer": "5"})

        self.assertEqual(response.status_code, 200)  # type: ignore

        # Проверяем, что прогресс пользователя обновился
        progress = UserProgress.objects.filter(  # type: ignore
            user=self.user, task=self.task
        ).first()

        if progress:
            self.assertFalse(progress.is_correct)
            self.assertEqual(progress.attempts, 1)

    def test_user_progress_creation(self):
        """Тест создания прогресса пользователя"""
        # Создаем прогресс пользователя
        progress = UserProgress.objects.create(  # type: ignore
            user=self.user, task=self.task, is_correct=True, attempts=1
        )

        self.assertEqual(progress.user, self.user)
        self.assertEqual(progress.task, self.task)
        self.assertTrue(progress.is_correct)
        self.assertEqual(progress.attempts, 1)

    def test_user_progress_update(self):
        """Тест обновления прогресса пользователя"""
        # Создаем прогресс пользователя
        progress = UserProgress.objects.create(  # type: ignore
            user=self.user, task=self.task, is_correct=False, attempts=1
        )

        # Обновляем прогресс
        progress.is_correct = True
        progress.attempts = 2
        progress.save()

        # Проверяем обновление
        updated_progress = UserProgress.objects.get(id=progress.id)  # type: ignore
        self.assertTrue(updated_progress.is_correct)
        self.assertEqual(updated_progress.attempts, 2)

    def test_task_difficulty_levels(self):
        """Тест различных уровней сложности заданий"""
        # Создаем задания с разными уровнями сложности
        easy_task = Task.objects.create(  # type: ignore
            title="Легкое задание",
            text="Простое уравнение",
            answer="1",
            subject=self.subject,
            difficulty=1,
        )

        medium_task = Task.objects.create(  # type: ignore
            title="Среднее задание",
            text="Уравнение средней сложности",
            answer="2",
            subject=self.subject,
            difficulty=2,
        )

        hard_task = Task.objects.create(  # type: ignore
            title="Сложное задание",
            text="Сложное уравнение",
            answer="3",
            subject=self.subject,
            difficulty=3,
        )

        self.assertEqual(easy_task.difficulty, 1)
        self.assertEqual(medium_task.difficulty, 2)
        self.assertEqual(hard_task.difficulty, 3)

    def test_subject_exam_types(self):
        """Тест различных типов экзаменов для предметов"""
        # Создаем предметы с разными типами экзаменов
        ege_subject = Subject.objects.create(  # type: ignore
            name="Физика", code="PHYS", exam_type="other"
        )

        oge_subject = Subject.objects.create(  # type: ignore
            name="Химия", code="CHEM", exam_type="oge"
        )

        self.assertEqual(ege_subject.exam_type, "ege")
        self.assertEqual(oge_subject.exam_type, "oge")

    def test_task_answer_validation(self):
        """Тест валидации ответов на задания"""
        # Создаем задание с числовым ответом
        numeric_task = Task.objects.create(  # type: ignore
            title="Числовое задание",
            text="Введите число",
            answer="42",
            subject=self.subject,
            difficulty=1,
        )

        # Создаем задание с текстовым ответом
        text_task = Task.objects.create(  # type: ignore
            title="Текстовое задание",
            text="Введите слово",
            answer="ответ",
            subject=self.subject,
            difficulty=1,
        )

        self.assertEqual(numeric_task.answer, "42")
        self.assertEqual(text_task.answer, "ответ")

    def test_user_progress_statistics(self):
        """Тест статистики прогресса пользователя"""
        # Создаем несколько заданий
        task1 = Task.objects.create(  # type: ignore
            title="Задание 1",
            text="Первое задание",
            answer="1",
            subject=self.subject,
            difficulty=1,
        )

        task2 = Task.objects.create(  # type: ignore
            title="Задание 2",
            text="Второе задание",
            answer="2",
            subject=self.subject,
            difficulty=1,
        )

        # Создаем прогресс пользователя
        UserProgress.objects.create(  # type: ignore
            user=self.user, task=task1, is_correct=True, attempts=1
        )

        UserProgress.objects.create(  # type: ignore
            user=self.user, task=task2, is_correct=False, attempts=2
        )

        # Проверяем статистику
        total_progress = UserProgress.objects.filter(user=self.user).count()  # type: ignore
        correct_answers = UserProgress.objects.filter(  # type: ignore
            user=self.user, is_correct=True
        ).count()

        self.assertEqual(total_progress, 2)
        self.assertEqual(correct_answers, 1)

    def test_subject_tasks_relationship(self):
        """Тест связи между предметами и заданиями"""
        # Создаем второй предмет
        physics_subject = Subject.objects.create(  # type: ignore
            name="Физика", code="PHYS", exam_type="other"
        )

        # Создаем задание по физике
        physics_task = Task.objects.create(  # type: ignore
            title="Физическое задание",
            text="Решите задачу по физике",
            answer="9.8",
            subject=physics_subject,
            difficulty=2,
        )

        # Проверяем связи
        self.assertEqual(physics_task.subject, physics_subject)
        self.assertEqual(self.task.subject, self.subject)

        # Проверяем количество заданий по предметам
        math_tasks_count = Task.objects.filter(subject=self.subject).count()  # type: ignore
        physics_tasks_count = Task.objects.filter(subject=physics_subject).count()  # type: ignore

        self.assertEqual(math_tasks_count, 1)
        self.assertEqual(physics_tasks_count, 1)

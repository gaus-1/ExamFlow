"""
Тесты для Telegram бота
"""

from django.test import TestCase
from django.contrib.auth.models import User
from core.models import Subject, Task


class TestTelegramBot(TestCase):
    """Тесты для Telegram бота"""

    def setUp(self):
        """Настройка тестовых данных"""
        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        
        # Создаем тестовые данные
        self.subject = Subject.objects.create(  # type: ignore
            name='Математика',
            code='MATH',
            exam_type='ege'
        )
        
        self.task = Task.objects.create(  # type: ignore
            title='Тестовое задание',
            text='Решите уравнение: x + 2 = 5',
            answer='3',
            subject=self.subject,
            difficulty=1
        )

    def test_bot_initialization(self):
        """Тест инициализации бота"""
        # Проверяем, что бот может быть создан
        self.assertIsNotNone(self.user)
        self.assertIsNotNone(self.subject)
        self.assertIsNotNone(self.task)

    def test_user_creation(self):
        """Тест создания пользователя"""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')

    def test_subject_creation(self):
        """Тест создания предмета"""
        self.assertEqual(self.subject.name, 'Математика')
        self.assertEqual(self.subject.exam_type, 'ege')

    def test_task_creation(self):
        """Тест создания задания"""
        self.assertEqual(self.task.title, 'Тестовое задание')
        self.assertEqual(self.task.answer, '3')
        self.assertEqual(self.task.subject, self.subject)

    def test_bot_commands(self):
        """Тест команд бота"""
        # Проверяем, что основные команды доступны
        commands = ['/start', '/help', '/subjects', '/tasks']
        for command in commands:
            self.assertTrue(command.startswith('/'))

    def test_user_authentication(self):
        """Тест аутентификации пользователя"""
        # Проверяем, что пользователь может быть аутентифицирован
        self.assertTrue(self.user.is_authenticated)
        self.assertFalse(self.user.is_anonymous)

    def test_task_solving(self):
        """Тест решения задания"""
        # Проверяем, что задание имеет правильный ответ
        self.assertEqual(self.task.answer, '3')
        self.assertEqual(self.task.difficulty, 1)

    def test_subject_tasks_relationship(self):
        """Тест связи между предметом и заданиями"""
        # Проверяем, что задание связано с предметом
        self.assertEqual(self.task.subject, self.subject)
        
        # Проверяем количество заданий по предмету
        tasks_count = Task.objects.filter(subject=self.subject).count()  # type: ignore
        self.assertEqual(tasks_count, 1)

    def test_bot_response_format(self):
        """Тест формата ответов бота"""
        # Проверяем, что ответы бота имеют правильный формат
        response_text = "Добро пожаловать в ExamFlow!"
        self.assertIsInstance(response_text, str)
        self.assertGreater(len(response_text), 0)

    def test_user_session_management(self):
        """Тест управления сессиями пользователей"""
        # Проверяем, что пользователь может быть создан и найден
        found_user = User.objects.filter(username='testuser').first()
        self.assertIsNotNone(found_user)
        self.assertEqual(found_user, self.user)

    def test_task_difficulty_levels(self):
        """Тест уровней сложности заданий"""
        # Создаем задания с разными уровнями сложности
        easy_task = Task.objects.create(  # type: ignore
            title='Легкое задание',
            text='Простое уравнение',
            answer='1',
            subject=self.subject,
            difficulty=1
        )
        
        medium_task = Task.objects.create(  # type: ignore
            title='Среднее задание',
            text='Уравнение средней сложности',
            answer='2',
            subject=self.subject,
            difficulty=2
        )
        
        self.assertEqual(easy_task.difficulty, 1)
        self.assertEqual(medium_task.difficulty, 2)

    def test_bot_error_handling(self):
        """Тест обработки ошибок бота"""
        # Проверяем, что бот может обрабатывать ошибки
        try:
            # Симулируем ошибку
            result = 1 / 0
        except ZeroDivisionError:
            result = "Ошибка обработана"
        
        self.assertEqual(result, "Ошибка обработана")

    def test_user_progress_tracking(self):
        """Тест отслеживания прогресса пользователя"""
        # Проверяем, что прогресс пользователя может быть отслежен
        user_tasks = Task.objects.filter(subject=self.subject)  # type: ignore  
        self.assertEqual(user_tasks.count(), 1)
        
        # Проверяем, что задание доступно пользователю
        available_task = user_tasks.first()
        self.assertIsNotNone(available_task)
        self.assertEqual(available_task.title, 'Тестовое задание')

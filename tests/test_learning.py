"""
Тесты для модуля обучения
"""

import pytest
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from core.models import Subject, Topic, Task, UserProgress, ExamType


class TestLearning(TestCase):
    """Тесты модуля обучения"""

    def setUp(self):
        """Настройка тестовых данных"""
        self.client = Client()
        
        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        
        # Создаем тестовые данные
        self.exam_type = ExamType.objects.create(
            name='ЕГЭ',
            description='Единый государственный экзамен'
        )
        
        self.subject = Subject.objects.create(
            name='Математика',
            exam_type=self.exam_type,
            description='Базовая и профильная математика'
        )
        
        self.topic = Topic.objects.create(
            name='Алгебра',
            subject=self.subject,
            description='Основы алгебры'
        )
        
        self.task = Task.objects.create(
            title='Тестовое задание',
            content='Решите уравнение: x + 2 = 5',
            answer='3',
            topic=self.topic,
            explanation='x = 5 - 2 = 3'
        )

    def test_subject_creation(self):
        """Тест создания предмета"""
        self.assertEqual(self.subject.name, 'Математика')
        self.assertEqual(self.subject.exam_type, self.exam_type)

    def test_topic_creation(self):
        """Тест создания темы"""
        self.assertEqual(self.topic.name, 'Алгебра')
        self.assertEqual(self.topic.subject, self.subject)

    def test_task_creation(self):
        """Тест создания задания"""
        self.assertEqual(self.task.title, 'Тестовое задание')
        self.assertEqual(self.task.answer, '3')
        self.assertEqual(self.task.topic, self.topic)

    def test_task_check_answer_correct(self):
        """Тест проверки правильного ответа"""
        self.assertTrue(self.task.check_answer('3'))
        self.assertTrue(self.task.check_answer(' 3 '))  # С пробелами

    def test_task_check_answer_incorrect(self):
        """Тест проверки неправильного ответа"""
        self.assertFalse(self.task.check_answer('5'))
        self.assertFalse(self.task.check_answer(''))

    def test_subjects_list_view(self):
        """Тест страницы списка предметов"""
        response = self.client.get('/subjects/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Математика')

    def test_subject_detail_view(self):
        """Тест страницы детального просмотра предмета"""
        response = self.client.get(f'/subject/{self.subject.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Математика')

    def test_topic_detail_view(self):
        """Тест страницы детального просмотра темы"""
        response = self.client.get(f'/topic/{self.topic.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Алгебра')

    def test_task_detail_view(self):
        """Тест страницы детального просмотра задания"""
        response = self.client.get(f'/task/{self.task.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Тестовое задание')

    def test_solve_task_correct_answer(self):
        """Тест решения задания с правильным ответом"""
        self.client.login(username='testuser', password='testpassword123')
        
        response = self.client.post(f'/task/{self.task.id}/solve/', {
            'answer': '3'
        })
        
        self.assertEqual(response.status_code, 200)
        
        # Проверяем создание записи прогресса
        progress = UserProgress.objects.get(user=self.user, task=self.task)
        self.assertTrue(progress.is_correct)
        self.assertEqual(progress.user_answer, '3')

    def test_solve_task_incorrect_answer(self):
        """Тест решения задания с неправильным ответом"""
        self.client.login(username='testuser', password='testpassword123')
        
        response = self.client.post(f'/task/{self.task.id}/solve/', {
            'answer': '5'
        })
        
        self.assertEqual(response.status_code, 200)
        
        # Проверяем создание записи прогресса
        progress = UserProgress.objects.get(user=self.user, task=self.task)
        self.assertFalse(progress.is_correct)
        self.assertEqual(progress.user_answer, '5')

    def test_solve_task_unauthorized(self):
        """Тест решения задания неавторизованным пользователем"""
        response = self.client.post(f'/task/{self.task.id}/solve/', {
            'answer': '3'
        })
        
        # Должен быть редирект на страницу входа
        self.assertEqual(response.status_code, 302)

    def test_random_task_view(self):
        """Тест страницы случайного задания"""
        response = self.client.get('/random/')
        self.assertEqual(response.status_code, 302)  # Редирект на конкретное задание

    def test_user_progress_tracking(self):
        """Тест отслеживания прогресса пользователя"""
        # Создаем прогресс
        progress = UserProgress.objects.create(
            user=self.user,
            task=self.task,
            user_answer='3',
            is_correct=True
        )
        
        self.assertEqual(progress.user, self.user)
        self.assertEqual(progress.task, self.task)
        self.assertTrue(progress.is_correct)

    def test_subject_with_multiple_topics(self):
        """Тест предмета с несколькими темами"""
        topic2 = Topic.objects.create(
            name='Геометрия',
            subject=self.subject,
            description='Основы геометрии'
        )
        
        # Проверяем связь
        topics = Topic.objects.filter(subject=self.subject)
        self.assertEqual(topics.count(), 2)
        self.assertIn(self.topic, topics)
        self.assertIn(topic2, topics)

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
        self.user = User.objects.create_user(  # type: ignore
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        
        # Создаем тестовые данные
        self.exam_type = ExamType.objects.create(  # type: ignore
            name='ЕГЭ',
            code='EGE'
        )
        
        self.subject = Subject.objects.create(  # type: ignore
            name='Математика',
            exam_type='ЕГЭ'
        )
        
        self.topic = Topic.objects.create(  # type: ignore
            name='Алгебра',
            subject=self.subject,
            code='ALG'
        )
        
        self.task = Task.objects.create(  # type: ignore
            title='Тестовое задание',
            description='Решите уравнение: x + 2 = 5',
            answer='3',
            subject=self.subject,
            difficulty=1
        )

    def test_subject_creation(self):
        """Тест создания предмета"""
        self.assertEqual(self.subject.name, 'Математика')
        self.assertEqual(self.subject.exam_type, 'ЕГЭ')

    def test_topic_creation(self):
        """Тест создания темы"""
        self.assertEqual(self.topic.name, 'Алгебра')
        self.assertEqual(self.topic.subject, self.subject)

    def test_task_creation(self):
        """Тест создания задания"""
        self.assertEqual(self.task.title, 'Тестовое задание')
        self.assertEqual(self.task.answer, '3')
        self.assertEqual(self.task.subject, self.subject)

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
        progress = UserProgress.objects.get(user=self.user, task=self.task)  # type: ignore
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
        progress = UserProgress.objects.get(user=self.user, task=self.task)  # type: ignore
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
        progress = UserProgress.objects.create(  # type: ignore
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
        topic2 = Topic.objects.create(  # type: ignore
            name='Геометрия',
            subject=self.subject,
            code='GEO'
        )
        
        # Проверяем связь
        topics = Topic.objects.filter(subject=self.subject)  # type: ignore
        self.assertEqual(topics.count(), 2)  # type: ignore
        self.assertIn(self.topic, topics)
        self.assertIn(topic2, topics)

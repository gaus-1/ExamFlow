"""
Тесты для моделей learning приложения
"""

import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError


@pytest.mark.unit
@pytest.mark.django_db
class TestLearningModels(TestCase):
    """Тесты моделей learning"""
    
    def setUp(self):
        """Настройка тестовых данных"""
        from learning.models import Subject, Task, UserProgress
        from telegram_auth.models import TelegramUser
        
        # Создаем пользователя
        self.user = TelegramUser.objects.create_user(
            telegram_id=123456789,
            telegram_username='testuser'
        )
        
        # Создаем предмет
        self.subject = Subject.objects.create( # type: ignore
            name='Математика',
            description='Математика для ЕГЭ'
        )
        
        # Создаем задание
        self.task = Task.objects.create( # type: ignore
            title='Тестовое задание',
            description='Решите уравнение x + 1 = 2',
            subject=self.subject,
            difficulty=1
        )
    
    def test_subject_creation(self):
        """Тест создания предмета"""
        from learning.models import Subject
        
        subject = Subject.objects.create( # type: ignore
            name='Русский язык',
            description='Русский язык для ЕГЭ'
        )
        
        assert subject.name == 'Русский язык'
        assert subject.description == 'Русский язык для ЕГЭ'
        assert str(subject) == 'Русский язык'
    
    def test_task_creation(self):
        """Тест создания задания"""
        from learning.models import Task
        
        task = Task.objects.create( # type: ignore
            title='Новое задание',
            content='Решите систему уравнений',
            subject=self.subject,
            difficulty=2
        )
        
        assert task.title == 'Новое задание'
        assert task.description == 'Решите систему уравнений'
        assert task.subject == self.subject
        assert task.difficulty == 2
        assert str(task) == 'Новое задание'
    
    def test_user_progress_creation(self):
        """Тест создания прогресса пользователя"""
        from learning.models import UserProgress
        
        progress = UserProgress.objects.create( # type: ignore
            user=self.user,
            task=self.task,
            is_completed=True,
            score=85
        )
        
        assert progress.user == self.user
        assert progress.task == self.task
        assert progress.is_completed is True
        assert progress.score == 85
        assert str(progress) == f'Прогресс пользователя {self.user.telegram_id} по заданию {self.task.title}'
    
    def test_task_subject_relationship(self):
        """Тест связи задания с предметом"""
        assert self.task.subject == self.subject
        assert self.task in self.subject.task_set.all()
    
    def test_user_progress_user_relationship(self):
        """Тест связи прогресса с пользователем"""
        from learning.models import UserProgress
        
        progress = UserProgress.objects.create( # type: ignore
            user=self.user,
            task=self.task,
            is_completed=False
        )
        
        assert progress.user == self.user
        assert progress in self.user.userprogress_set.all()
    
    def test_subject_str_method(self):
        """Тест метода __str__ для Subject"""
        assert str(self.subject) == 'Математика'
    
    def test_task_str_method(self):
        """Тест метода __str__ для Task"""
        assert str(self.task) == 'Тестовое задание'
    
    def test_user_progress_str_method(self):
        """Тест метода __str__ для UserProgress"""
        from learning.models import UserProgress
        
        progress = UserProgress.objects.create( # type: ignore
            user=self.user,
            task=self.task,
            is_completed=True
        )
        
        expected_str = f'Прогресс пользователя {self.user.telegram_id} по заданию {self.task.title}'
        assert str(progress) == expected_str

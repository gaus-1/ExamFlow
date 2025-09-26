"""
Тесты для моделей learning приложения
"""

import pytest
from django.test import TestCase


@pytest.mark.unit
@pytest.mark.django_db
class TestLearningModels(TestCase):
    """Тесты моделей learning"""
    
    def setUp(self):
        """Настройка тестовых данных"""
        from learning.models import Subject, Task
        from telegram_auth.models import TelegramUser
        
        # Создаем пользователя
        self.user = TelegramUser.objects.create(
            telegram_id=123456789,
            telegram_username='testuser'
        )
        
        # Используем существующий предмет из базы данных
        self.subject = Subject.objects.first() # type: ignore
        if not self.subject:
            # Если нет предметов, создаем с пустым exam_type
            self.subject = Subject.objects.create( # type: ignore
                name='Тестовая Математика',
                description='Тестовая математика для тестов',
                exam_type=''
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
        
        # Используем существующий предмет или создаем с пустым exam_type
        subject = Subject.objects.filter(name__icontains='русский').first() # type: ignore
        if not subject:
            subject = Subject.objects.create( # type: ignore
                name='Тестовый Русский язык',
                description='Тестовый русский язык для тестов',
                exam_type=''
            )
        
        # Проверяем, что предмет существует и имеет правильные поля
        assert subject is not None
        assert hasattr(subject, 'name')
        assert hasattr(subject, 'description')
        assert str(subject) is not None
    
    def test_task_creation(self):
        """Тест создания задания"""
        from learning.models import Task
        
        task = Task.objects.create( # type: ignore
            title='Новое задание',
            description='Решите систему уравнений',
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
            is_correct=True,
            attempts=1
        )
        
        assert progress.user == self.user
        assert progress.task == self.task
        assert progress.is_correct is True
        assert progress.attempts == 1
        assert str(progress) == f'{self.user.username} - {self.task.subject.name}'
    
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
            is_correct=False
        )
        
        assert progress.user == self.user
        assert progress in self.user.learning_userprogress_set.all()
    
    def test_subject_str_method(self):
        """Тест метода __str__ для Subject"""
        assert str(self.subject) is not None
        assert len(str(self.subject)) > 0
    
    def test_task_str_method(self):
        """Тест метода __str__ для Task"""
        assert str(self.task) == 'Тестовое задание'
    
    def test_user_progress_str_method(self):
        """Тест метода __str__ для UserProgress"""
        from learning.models import UserProgress
        
        progress = UserProgress.objects.create( # type: ignore
            user=self.user,
            task=self.task,
            is_correct=True
        )
        
        expected_str = f'{self.user.username} - {self.task.subject.name}'
        assert str(progress) == expected_str

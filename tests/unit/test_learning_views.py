#!/usr/bin/env python
"""
Тесты для представлений learning приложения
"""

from django.test import TestCase, RequestFactory
from telegram_auth.models import TelegramUser
from unittest.mock import patch
import json

from learning.views import (
    home, subjects_list, subject_detail, 
    random_task, task_detail, solve_task
)
from learning.models import Subject, Task
from core.models import UserProgress


class TestLearningViews(TestCase):
    """Тесты для представлений learning"""
    
    def setUp(self):
        """Настройка тестовых данных"""
        self.factory = RequestFactory()
        self.user = TelegramUser.objects.create(
            telegram_id=123456789,
            telegram_username='testuser'
        )
        
        self.subject = Subject.objects.first() # type: ignore
        if not self.subject:
            self.subject = Subject.objects.create( # type: ignore
                name='Тестовая Математика',
                description='Тестовая математика для тестов'
            )
        
        self.task = Task.objects.create( # type: ignore
            title='Тестовое задание',
            description='Решите уравнение x + 1 = 2',
            subject=self.subject,
            difficulty=1,
            answer='1'
        )
    
    def test_home_view_success(self):
        """Тест успешной загрузки главной страницы"""
        request = self.factory.get('/')
        response = home(request)
        
        assert response.status_code == 200
        assert 'subjects_count' in response.context
        assert 'tasks_count' in response.context
        assert 'qr_code' in response.context
    
    def test_home_view_database_error(self):
        """Тест главной страницы при ошибке базы данных"""
        request = self.factory.get('/')
        
        with patch('learning.views.Subject.objects.filter') as mock_subjects:
            mock_subjects.side_effect = Exception('Database error')
            
            response = home(request)
            
            assert response.status_code == 200
            assert response.context['subjects_count'] == 0
            assert response.context['tasks_count'] == 0
    
    def test_subjects_list_view_success(self):
        """Тест успешной загрузки списка предметов"""
        request = self.factory.get('/subjects/')
        response = subjects_list(request)
        
        assert response.status_code == 200
        assert 'subjects' in response.context
    
    def test_subjects_list_view_database_error(self):
        """Тест списка предметов при ошибке базы данных"""
        request = self.factory.get('/subjects/')
        
        with patch('learning.views.Subject.objects.filter') as mock_subjects:
            mock_subjects.side_effect = Exception('Database error')
            
            response = subjects_list(request)
            
            assert response.status_code == 200
            # Должны использоваться fallback данные
            assert len(response.context['subjects']) > 0
    
    def test_subject_detail_view_success(self):
        """Тест успешной загрузки детальной страницы предмета"""
        request = self.factory.get(f'/subjects/{self.subject.id}/')
        response = subject_detail(request, subject_id=self.subject.id)
        
        assert response.status_code == 200
        assert 'subject' in response.context
        assert 'topics' in response.context
        assert 'tasks' in response.context
    
    def test_subject_detail_view_not_found(self):
        """Тест детальной страницы предмета - предмет не найден"""
        request = self.factory.get('/subjects/99999/')
        response = subject_detail(request, subject_id=99999)
        
        assert response.status_code == 404
    
    def test_subject_detail_view_database_error(self):
        """Тест детальной страницы предмета при ошибке базы данных"""
        request = self.factory.get(f'/subjects/{self.subject.id}/')
        
        with patch('learning.views.get_object_or_404') as mock_get_object:
            mock_get_object.side_effect = Exception('Database error')
            
            response = subject_detail(request, subject_id=self.subject.id)
            
            assert response.status_code == 200
            # Должны использоваться fallback данные
    
    def test_random_task_view_success(self):
        """Тест успешной загрузки случайного задания"""
        request = self.factory.get('/random-task/')
        response = random_task(request)
        
        assert response.status_code == 200
        assert 'task' in response.context
        assert 'subject' in response.context
    
    def test_random_task_view_with_subject_filter(self):
        """Тест случайного задания с фильтром по предмету"""
        request = self.factory.get(f'/random-task/?subject={self.subject.id}')
        response = random_task(request)
        
        assert response.status_code == 200
        assert 'task' in response.context
        assert response.context['subject'] == self.subject
    
    def test_random_task_view_no_tasks(self):
        """Тест случайного задания когда нет доступных заданий"""
        request = self.factory.get('/random-task/')
        
        with patch('learning.views.Task.objects.filter') as mock_tasks:
            mock_tasks.return_value.count.return_value = 0
            
            response = random_task(request)
            
            assert response.status_code == 200
            assert response.context['task'] is None
    
    def test_task_detail_view_success(self):
        """Тест успешной загрузки детальной страницы задания"""
        request = self.factory.get(f'/tasks/{self.task.id}/')
        response = task_detail(request, task_id=self.task.id)
        
        assert response.status_code == 200
        assert 'task' in response.context
        assert 'subject' in response.context
        assert 'user_progress' in response.context
    
    def test_task_detail_view_not_found(self):
        """Тест детальной страницы задания - задание не найдено"""
        request = self.factory.get('/tasks/99999/')
        response = task_detail(request, task_id=99999)
        
        assert response.status_code == 404
    
    def test_submit_answer_view_correct_answer(self):
        """Тест отправки правильного ответа"""
        request = self.factory.post('/submit-answer/', data={
            'task_id': self.task.id,
            'answer': '1'
        }, content_type='application/json')
        request.user = self.user
        
        response = solve_task(request, task_id=self.task.id)
        
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['correct'] is True
        assert 'message' in data
    
    def test_submit_answer_view_incorrect_answer(self):
        """Тест отправки неправильного ответа"""
        request = self.factory.post('/submit-answer/', data={
            'task_id': self.task.id,
            'answer': '2'
        }, content_type='application/json')
        request.user = self.user
        
        response = solve_task(request, task_id=self.task.id)
        
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['correct'] is False
        assert 'message' in data
    
    def test_submit_answer_view_missing_task_id(self):
        """Тест отправки ответа без task_id"""
        request = self.factory.post('/submit-answer/', data={
            'answer': '1'
        }, content_type='application/json')
        request.user = self.user
        
        response = solve_task(request, task_id=self.task.id)
        
        assert response.status_code == 400
        data = json.loads(response.content)
        assert 'error' in data
    
    def test_submit_answer_view_task_not_found(self):
        """Тест отправки ответа для несуществующего задания"""
        request = self.factory.post('/submit-answer/', data={
            'task_id': 99999,
            'answer': '1'
        }, content_type='application/json')
        request.user = self.user
        
        response = solve_task(request, task_id=self.task.id)
        
        assert response.status_code == 404
        data = json.loads(response.content)
        assert 'error' in data
    
    def test_submit_answer_view_invalid_json(self):
        """Тест отправки некорректного JSON"""
        request = self.factory.post('/submit-answer/', data='invalid json', content_type='application/json')
        request.user = self.user
        
        response = solve_task(request, task_id=self.task.id)
        
        assert response.status_code == 400
        data = json.loads(response.content)
        assert 'error' in data
    
    def test_submit_answer_view_creates_progress(self):
        """Тест создания записи прогресса при отправке ответа"""
        request = self.factory.post('/submit-answer/', data={
            'task_id': self.task.id,
            'answer': '1'
        }, content_type='application/json')
        request.user = self.user
        
        # Проверяем, что до отправки нет прогресса
        initial_count = UserProgress.objects.filter(user=self.user, task=self.task).count()
        
        response = solve_task(request, task_id=self.task.id)
        
        # Проверяем, что после отправки создался прогресс
        final_count = UserProgress.objects.filter(user=self.user, task=self.task).count()
        assert final_count > initial_count
        
        progress = UserProgress.objects.filter(user=self.user, task=self.task).first()
        assert progress is not None
        assert progress.user_answer == '1'
        assert progress.is_correct is True
    
    def test_submit_answer_view_updates_existing_progress(self):
        """Тест обновления существующего прогресса"""
        # Создаем существующий прогресс
        progress = UserProgress.objects.create(
            user=self.user,
            task=self.task,
            user_answer='2',
            is_correct=False,
            attempts=1
        )
        
        request = self.factory.post('/submit-answer/', data={
            'task_id': self.task.id,
            'answer': '1'
        }, content_type='application/json')
        request.user = self.user
        
        response = solve_task(request, task_id=self.task.id)
        
        # Проверяем, что прогресс обновился
        progress.refresh_from_db()
        assert progress.user_answer == '1'
        assert progress.is_correct is True
        assert progress.attempts == 2
    
    def test_random_task_view_database_error(self):
        """Тест случайного задания при ошибке базы данных"""
        request = self.factory.get('/random-task/')
        
        with patch('learning.views.Task.objects.filter') as mock_tasks:
            mock_tasks.side_effect = Exception('Database error')
            
            response = random_task(request)
            
            assert response.status_code == 200
            # Должен обработать ошибку gracefully
    
    def test_subjects_list_view_with_search(self):
        """Тест списка предметов с поиском"""
        request = self.factory.get('/subjects/?search=математика')
        response = subjects_list(request)
        
        assert response.status_code == 200
        assert 'subjects' in response.context
    
    def test_subjects_list_view_empty_search(self):
        """Тест списка предметов с пустым поиском"""
        request = self.factory.get('/subjects/?search=')
        response = subjects_list(request)
        
        assert response.status_code == 200
        assert 'subjects' in response.context

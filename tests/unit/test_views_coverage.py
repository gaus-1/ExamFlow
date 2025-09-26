#!/usr/bin/env python
"""
Простые тесты для покрытия views
"""

from django.test import TestCase, RequestFactory
from unittest.mock import Mock, patch

from learning.views import home, subjects_list
from core.views import personalization_dashboard


class TestViewsCoverage(TestCase):
    """Простые тесты для views"""
    
    def setUp(self):
        """Настройка тестовых данных"""
        self.factory = RequestFactory()
    
    def test_home_view(self):
        """Тест главной страницы"""
        request = self.factory.get('/')
        
        with patch('learning.views.Subject') as mock_subject, \
             patch('learning.views.Task') as mock_task:
            mock_subject.objects.count.return_value = 5
            mock_task.objects.count.return_value = 100
            
            response = home(request)
            
            self.assertEqual(response.status_code, 200)
            self.assertIn('subjects_count', response.context)
            self.assertIn('tasks_count', response.context)
    
    def test_subjects_list_view(self):
        """Тест списка предметов"""
        request = self.factory.get('/subjects/')
        
        with patch('learning.views.Subject') as mock_subject:
            mock_subject.objects.all.return_value = []
            
            response = subjects_list(request)
            
            self.assertEqual(response.status_code, 200)
            self.assertIn('subjects', response.context)
    
    def test_subjects_list_view_error(self):
        """Тест списка предметов с ошибкой"""
        request = self.factory.get('/subjects/')
        
        with patch('learning.views.Subject') as mock_subject:
            mock_subject.objects.all.side_effect = Exception('DB Error')
            
            response = subjects_list(request)
            
            self.assertEqual(response.status_code, 200)
            self.assertIn('subjects', response.context)
    
    def test_personalization_dashboard(self):
        """Тест дашборда персонализации"""
        request = self.factory.get('/personalization/')
        request.user = Mock()
        request.user.is_authenticated = True
        
        with patch('core.views.render') as mock_render:
            mock_render.return_value = Mock()
            
            response = personalization_dashboard(request)
            
            self.assertIsNotNone(response)
            mock_render.assert_called_once()

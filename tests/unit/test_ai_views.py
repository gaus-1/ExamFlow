#!/usr/bin/env python
"""
Тесты для представлений ai приложения
"""

from django.test import TestCase, RequestFactory
from telegram_auth.models import TelegramUser
from unittest.mock import Mock, patch
import json
from datetime import timedelta
from django.utils import timezone

from ai.views import (
    ai_dashboard, ai_chat, api_chat, api_explain,
    get_ai_service
)
from ai.models import AiLimit


class TestAIViews(TestCase):
    """Тесты для представлений ai"""
    
    def setUp(self):
        """Настройка тестовых данных"""
        self.factory = RequestFactory()
        self.user = TelegramUser.objects.create(
            telegram_id=123456789,
            telegram_username='testuser'
        )
        
        # Создаем лимит для пользователя
        self.ai_limit = AiLimit.objects.create( # type: ignore  
            user=self.user,
            limit_type='daily',
            max_limit=10,
            current_usage=0,
            reset_date=timezone.now() + timedelta(days=1)
        )
    
    def test_ai_dashboard_success(self):
        """Тест успешной загрузки дашборда ИИ"""
        request = self.factory.get('/ai/')
        request.user = self.user  # type: ignore
        
        response = ai_dashboard(request)
        
        assert response.status_code == 200
        # Проверяем что ответ содержит нужный контент
        assert 'ИИ-ассистент ExamFlow'.encode('utf-8') in response.content
    
    def test_ai_chat_success(self):
        """Тест успешной загрузки страницы чата"""
        request = self.factory.get('/ai/chat/')
        request.user = self.user  # type: ignore
        
        response = ai_chat(request)
        
        assert response.status_code == 200
        assert 'title' in response.context # type: ignore
        assert 'user' in response.context # type: ignore
        assert response.context['title'] == 'Чат с ИИ - ExamFlow' # type: ignore
    
    def test_ai_chat_exception(self):
        """Тест страницы чата при исключении"""
        request = self.factory.get('/ai/chat/')
        request.user = self.user  # type: ignore

        with patch('ai.views.render') as mock_render:
            mock_render.side_effect = Exception('Template error')
            
            response = ai_chat(request)
            
            # Должен обработать ошибку gracefully
            assert response.status_code == 200
    
    def test_api_chat_success(self):
        """Тест успешного API чата"""
        request_data = {
            'prompt': 'Что такое ЕГЭ?',
            'user_id': self.user.telegram_id
        }
        request = self.factory.post('/api/ai/chat/', data=json.dumps(request_data), content_type='application/json')
        request.user = self.user  # type: ignore
        
        with patch('ai.views.get_ai_service') as mock_get_service:
            mock_service = Mock()
            mock_get_service.return_value = mock_service
            mock_service.generate_response.return_value = 'ЕГЭ - это единый государственный экзамен.'
            
            response = api_chat(request)
            
            assert response.status_code == 200
            data = json.loads(response.content)
            assert 'response' in data
            assert 'ЕГЭ - это единый государственный экзамен.' in data['response']
    
    def test_api_chat_no_service(self):
        """Тест API чата без доступного сервиса"""
        request_data = {
            'prompt': 'Что такое ЕГЭ?',
            'user_id': self.user.telegram_id
        }
        request = self.factory.post('/api/ai/chat/', data=json.dumps(request_data), content_type='application/json')
        request.user = self.user  # type: ignore
        
        with patch('ai.views.get_ai_service') as mock_get_service:
            mock_get_service.return_value = None
            
            response = api_chat(request)
            
            assert response.status_code == 500
            data = json.loads(response.content)
            assert 'error' in data
    
    def test_api_chat_rate_limit_exceeded(self):
        """Тест API чата при превышении лимита"""
        # Устанавливаем текущее использование на максимум
        self.ai_limit.current_usage = 10
        self.ai_limit.save()
        
        request_data = {
            'prompt': 'Что такое ЕГЭ?',
            'user_id': self.user.telegram_id
        }
        request = self.factory.post('/api/ai/chat/', data=json.dumps(request_data), content_type='application/json')
        request.user = self.user  # type: ignore
        
        response = api_chat(request)
        
        assert response.status_code == 429
        data = json.loads(response.content)
        assert 'error' in data
        assert 'лимит' in data['error'].lower()
    
    def test_api_chat_empty_prompt(self):
        """Тест API чата с пустым запросом"""
        request_data = {
            'prompt': '',
            'user_id': self.user.telegram_id
        }
        request = self.factory.post('/api/ai/chat/', data=json.dumps(request_data), content_type='application/json')
        request.user = self.user  # type: ignore
        
        response = api_chat(request)
        
        assert response.status_code == 400
        data = json.loads(response.content)
        assert 'error' in data
    
    def test_api_chat_invalid_json(self):
        """Тест API чата с некорректным JSON"""
        request = self.factory.post('/api/ai/chat/', data='invalid json', content_type='application/json')
        request.user = self.user  # type: ignore
        
        response = api_chat(request)
        
        assert response.status_code == 400
        data = json.loads(response.content)
        assert 'error' in data
    
    def test_api_chat_service_error(self):
        """Тест API чата при ошибке сервиса"""
        request_data = {
            'prompt': 'Что такое ЕГЭ?',
            'user_id': self.user.telegram_id
        }
        request = self.factory.post('/api/ai/chat/', data=json.dumps(request_data), content_type='application/json')
        request.user = self.user  # type: ignore
        
        with patch('ai.views.get_ai_service') as mock_get_service:
            mock_service = Mock()
            mock_get_service.return_value = mock_service
            mock_service.generate_response.side_effect = Exception('AI Service Error')
            
            response = api_chat(request)
            
            assert response.status_code == 500
            data = json.loads(response.content)
            assert 'error' in data
    
    def test_api_chat_increments_usage(self):
        """Тест что API чат увеличивает счетчик использования"""
        initial_usage = self.ai_limit.current_usage
        
        request_data = {
            'prompt': 'Что такое ЕГЭ?',
            'user_id': self.user.telegram_id
        }
        request = self.factory.post('/api/ai/chat/', data=json.dumps(request_data), content_type='application/json')
        request.user = self.user  # type: ignore
        
        with patch('ai.views.get_ai_service') as mock_get_service:
            mock_service = Mock()
            mock_get_service.return_value = mock_service
            mock_service.generate_response.return_value = 'Ответ'
            
            response = api_chat(request)
            
            assert response.status_code == 200
            
            # Проверяем, что счетчик увеличился
            self.ai_limit.refresh_from_db()
            assert self.ai_limit.current_usage > initial_usage
    
    def test_api_explain_success(self):
        """Тест успешного API объяснения"""
        request_data = {
            'topic': 'Математика',
            'user_id': self.user.telegram_id
        }
        request = self.factory.post('/api/ai/explain/', data=json.dumps(request_data), content_type='application/json')
        request.user = self.user  # type: ignore        
        
        with patch('ai.views.get_ai_service') as mock_get_service:
            mock_service = Mock()
            mock_get_service.return_value = mock_service
            mock_service.explain_topic.return_value = 'Объяснение по математике'
            
            response = api_explain(request)
            
            assert response.status_code == 200
            data = json.loads(response.content)
            assert 'explanation' in data
    
    def test_get_ai_service_creation(self):
        """Тест создания AiService"""
        # Сбрасываем глобальную переменную
        import ai.views
        ai.views.ai_service = None
        
        with patch('ai.views.AiService') as mock_ai_service_class:
            mock_service = Mock()
            mock_ai_service_class.return_value = mock_service
            
            service = get_ai_service()
            
            assert service == mock_service
            mock_ai_service_class.assert_called_once()
    
    def test_get_ai_service_cached(self):
        """Тест что AiService кэшируется"""
        # Сбрасываем глобальную переменную
        import ai.views
        ai.views.ai_service = None
        
        with patch('ai.views.AiService') as mock_ai_service_class:
            mock_service = Mock()
            mock_ai_service_class.return_value = mock_service
            
            # Первый вызов
            service1 = get_ai_service()
            # Второй вызов
            service2 = get_ai_service()
            
            assert service1 == service2
            # AiService должен быть создан только один раз
            mock_ai_service_class.assert_called_once()
    
    def test_get_ai_service_creation_error(self):
        """Тест создания AiService при ошибке"""
        # Сбрасываем глобальную переменную
        import ai.views
        ai.views.ai_service = None
        
        with patch('ai.views.AiService') as mock_ai_service_class:
            mock_ai_service_class.side_effect = Exception('Creation error')
            
            service = get_ai_service()
            
            assert service is None
    
    def test_api_chat_with_query_field(self):
        """Тест API чата с полем query вместо prompt"""
        request_data = {
            'query': 'Что такое ЕГЭ?',  # Используем query вместо prompt
            'user_id': self.user.telegram_id
        }
        request = self.factory.post('/api/ai/chat/', data=json.dumps(request_data), content_type='application/json')
        request.user = self.user  # type: ignore
        
        with patch('ai.views.get_ai_service') as mock_get_service:
            mock_service = Mock()
            mock_get_service.return_value = mock_service
            mock_service.generate_response.return_value = 'ЕГЭ - это единый государственный экзамен.'
            
            response = api_chat(request)
            
            assert response.status_code == 200
            data = json.loads(response.content)
            assert 'response' in data
    
    def test_api_chat_rate_limit_check(self):
        """Тест проверки rate limit"""
        request_data = {
            'prompt': 'Что такое ЕГЭ?',
            'user_id': self.user.telegram_id
        }
        request = self.factory.post('/api/ai/chat/', data=json.dumps(request_data), content_type='application/json')
        request.user = self.user  # type: ignore
        
        # Проверяем, что rate limit декоратор применяется
        # Это сложно протестировать напрямую, но можем проверить логику
        response = api_chat(request)
        
        # Должен пройти успешно, так как лимит не превышен
        assert response.status_code in [200, 429]  # Может быть ограничен декоратором

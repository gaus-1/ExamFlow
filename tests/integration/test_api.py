"""
Integration тесты для API ExamFlow
"""

import pytest
import json
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.django_db
class TestAIAPI:
    """Тесты AI API"""
    
    def test_ai_api_get_method_not_allowed(self, client):
        """Тест что GET метод не разрешен для AI API"""
        response = client.get('/ai/api/')
        
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    
    def test_ai_api_post_success(self, authenticated_client, user, mock_ai_service):
        """Тест успешного POST запроса к AI API"""
        data = {
            'prompt': 'Решите уравнение 2x + 3 = 7',
            'subject': 'Математика',
            'user_id': user.id
        }
        
        response = authenticated_client.post(
            '/ai/api/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert 'answer' in response_data
        assert 'sources' in response_data
        assert response_data['answer'] == 'Тестовый ответ от AI'
    
    def test_ai_api_post_without_authentication(self, client):
        """Тест POST запроса без аутентификации"""
        data = {
            'prompt': 'Тестовый запрос',
            'subject': 'Математика'
        }
        
        response = client.post(
            '/ai/api/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Может быть 401 или 403 в зависимости от настроек
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
    
    def test_ai_api_invalid_json(self, authenticated_client):
        """Тест с невалидным JSON"""
        response = authenticated_client.post(
            '/ai/api/',
            data='invalid json',
            content_type='application/json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_ai_api_missing_prompt(self, authenticated_client):
        """Тест без обязательного поля prompt"""
        data = {
            'subject': 'Математика'
        }
        
        response = authenticated_client.post(
            '/ai/api/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_ai_api_with_rag_context(self, authenticated_client, user, mock_rag_system):
        """Тест AI API с RAG контекстом"""
        data = {
            'prompt': 'Помогите с уравнением',
            'subject': 'Математика',
            'user_id': user.id,
            'use_context': True
        }
        
        response = authenticated_client.post(
            '/ai/api/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert 'context_sources' in response_data or 'sources' in response_data


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.django_db
class TestSubjectsAPI:
    """Тесты API предметов"""
    
    def test_subjects_list_api(self, client, math_subject, russian_subject):
        """Тест получения списка предметов через API"""
        response = client.get('/api/subjects/')
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 2
        
        subject_names = [subject['name'] for subject in data]
        assert 'Математика (профильная)' in subject_names
        assert 'Русский язык' in subject_names
    
    def test_subject_detail_api(self, client, math_subject):
        """Тест получения детальной информации о предмете"""
        response = client.get(f'/api/subjects/{math_subject.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['name'] == 'Математика (профильная)'
        assert data['code'] == 'MATH_PRO'
        assert data['exam_type'] == 'ЕГЭ'
    
    def test_subject_tasks_api(self, client, math_subject, math_task):
        """Тест получения заданий по предмету"""
        response = client.get(f'/api/subjects/{math_subject.id}/tasks/')
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
        
        task_titles = [task['title'] for task in data]
        assert 'Решите уравнение' in task_titles


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.django_db
class TestTasksAPI:
    """Тесты API заданий"""
    
    def test_tasks_list_api(self, client, math_task, russian_task):
        """Тест получения списка заданий через API"""
        response = client.get('/api/tasks/')
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 2
    
    def test_task_detail_api(self, client, math_task):
        """Тест получения детальной информации о задании"""
        response = client.get(f'/api/tasks/{math_task.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['title'] == 'Решите уравнение'
        assert data['content'] == 'Решите уравнение: 2x + 5 = 13'
        assert data['subject'] == math_task.subject.id
    
    def test_task_solve_correct_answer(self, authenticated_client, user, math_task):
        """Тест решения задания с правильным ответом"""
        data = {
            'answer': '4',
            'user_id': user.id
        }
        
        response = authenticated_client.post(
            f'/api/tasks/{math_task.id}/solve/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['is_correct'] is True
    
    def test_task_solve_incorrect_answer(self, authenticated_client, user, math_task):
        """Тест решения задания с неправильным ответом"""
        data = {
            'answer': '5',
            'user_id': user.id
        }
        
        response = authenticated_client.post(
            f'/api/tasks/{math_task.id}/solve/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['is_correct'] is False
    
    def test_task_solve_without_authentication(self, client, math_task):
        """Тест решения задания без аутентификации"""
        data = {
            'answer': '4'
        }
        
        response = client.post(
            f'/api/tasks/{math_task.id}/solve/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.django_db
class TestUserProgressAPI:
    """Тесты API прогресса пользователя"""
    
    def test_user_progress_api(self, authenticated_client, user, math_task):
        """Тест получения прогресса пользователя"""
        response = authenticated_client.get(f'/api/users/{user.id}/progress/')
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'total_tasks' in data
        assert 'completed_tasks' in data
        assert 'success_rate' in data
    
    def test_user_progress_statistics(self, authenticated_client, user, math_task, russian_task):
        """Тест статистики прогресса пользователя"""
        # Решаем задания
        authenticated_client.post(
            f'/api/tasks/{math_task.id}/solve/',
            data=json.dumps({'answer': '4', 'user_id': user.id}),
            content_type='application/json'
        )
        
        authenticated_client.post(
            f'/api/tasks/{russian_task.id}/solve/',
            data=json.dumps({'answer': 'о', 'user_id': user.id}),
            content_type='application/json'
        )
        
        response = authenticated_client.get(f'/api/users/{user.id}/progress/')
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['completed_tasks'] >= 2


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.django_db
class TestTelegramWebhookAPI:
    """Тесты API Telegram webhook"""
    
    def test_telegram_webhook_post(self, client, telegram_webhook_data):
        """Тест POST запроса к Telegram webhook"""
        response = client.post(
            '/bot/webhook/',
            data=json.dumps(telegram_webhook_data),
            content_type='application/json'
        )
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_telegram_webhook_get(self, client):
        """Тест GET запроса к Telegram webhook"""
        response = client.get('/bot/webhook/')
        
        # Может возвращать информацию о webhook или 405
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_405_METHOD_NOT_ALLOWED]
    
    def test_telegram_webhook_invalid_data(self, client):
        """Тест webhook с невалидными данными"""
        invalid_data = {'invalid': 'data'}
        
        response = client.post(
            '/bot/webhook/',
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        
        # Должен обрабатывать невалидные данные корректно
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.django_db
class TestRateLimiting:
    """Тесты ограничения скорости запросов"""
    
    def test_ai_api_rate_limiting(self, authenticated_client, user):
        """Тест ограничения скорости для AI API"""
        data = {
            'prompt': 'Тестовый запрос',
            'subject': 'Математика',
            'user_id': user.id
        }
        
        # Делаем много запросов подряд
        responses = []
        for i in range(10):
            response = authenticated_client.post(
                '/ai/api/',
                data=json.dumps(data),
                content_type='application/json'
            )
            responses.append(response)
        
        # Проверяем что не все запросы были заблокированы
        successful_responses = [r for r in responses if r.status_code == status.HTTP_200_OK]
        assert len(successful_responses) > 0
    
    def test_task_solve_rate_limiting(self, authenticated_client, user, math_task):
        """Тест ограничения скорости для решения заданий"""
        data = {
            'answer': '4',
            'user_id': user.id
        }
        
        # Делаем много запросов подряд
        responses = []
        for i in range(5):
            response = authenticated_client.post(
                f'/api/tasks/{math_task.id}/solve/',
                data=json.dumps(data),
                content_type='application/json'
            )
            responses.append(response)
        
        # Проверяем что не все запросы были заблокированы
        successful_responses = [r for r in responses if r.status_code == status.HTTP_200_OK]
        assert len(successful_responses) > 0


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.django_db
class TestCORS:
    """Тесты CORS заголовков"""
    
    def test_cors_headers_present(self, client):
        """Тест наличия CORS заголовков"""
        response = client.options('/api/subjects/')
        
        assert response.status_code == status.HTTP_200_OK
        # Проверяем что CORS заголовки присутствуют
        assert 'Access-Control-Allow-Origin' in response or 'Access-Control-Allow-Methods' in response
    
    def test_cors_preflight_request(self, client):
        """Тест preflight запроса"""
        response = client.options(
            '/api/subjects/',
            HTTP_ACCESS_CONTROL_REQUEST_METHOD='GET',
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS='Content-Type'
        )
        
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.django_db
class TestAPIDocumentation:
    """Тесты API документации"""
    
    def test_swagger_ui_available(self, client):
        """Тест доступности Swagger UI"""
        response = client.get('/api/schema/swagger-ui/')
        
        # Может быть 200 или редирект
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_302_FOUND]
    
    def test_openapi_schema_available(self, client):
        """Тест доступности OpenAPI схемы"""
        response = client.get('/api/schema/')
        
        assert response.status_code == status.HTTP_200_OK
        # Проверяем что это JSON схема
        data = response.json()
        assert 'openapi' in data or 'swagger' in data
    
    def test_redoc_available(self, client):
        """Тест доступности ReDoc"""
        response = client.get('/api/schema/redoc/')
        
        # Может быть 200 или редирект
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_302_FOUND]


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.django_db
class TestAPIErrorHandling:
    """Тесты обработки ошибок API"""
    
    def test_404_not_found(self, client):
        """Тест 404 ошибки"""
        response = client.get('/api/subjects/999999/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_400_bad_request(self, authenticated_client):
        """Тест 400 ошибки"""
        response = authenticated_client.post(
            '/ai/api/',
            data='invalid json',
            content_type='application/json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_500_internal_server_error_handling(self, authenticated_client, user):
        """Тест обработки 500 ошибки"""
        # Мокаем ошибку в AI сервисе
        with pytest.MonkeyPatch().context() as m:
            m.setattr('core.container.Container.ai_orchestrator', lambda: Mock(side_effect=Exception('Test error'))) # type: ignore
            
            data = {
                'prompt': 'Тестовый запрос',
                'subject': 'Математика',
                'user_id': user.id
            }
            
            response = authenticated_client.post(
                '/ai/api/',
                data=json.dumps(data),
                content_type='application/json'
            )
            
            # Должен обрабатывать ошибку корректно
            assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]

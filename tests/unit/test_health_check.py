"""
Тесты для health check модуля
"""

import pytest
from django.test import RequestFactory
from unittest.mock import patch, Mock


@pytest.mark.unit
@pytest.mark.django_db
class TestHealthCheck:
    """Тесты health check функций"""
    
    def test_health_check_view_success(self):
        """Тест успешного health check"""
        from core.health_check import health_check_view
        from django.http import JsonResponse
        
        factory = RequestFactory()
        request = factory.get('/health/')
        
        with patch('django.db.connection.cursor') as mock_cursor, \
             patch('django.core.cache.cache') as mock_cache:
            
            # Настраиваем успешные моки
            mock_cursor.return_value.__enter__.return_value.execute = Mock()
            mock_cache.set.return_value = True
            mock_cache.get.return_value = 'test_value'
            
            response = health_check_view(request)
            
            assert isinstance(response, JsonResponse)
            assert response.status_code == 200
            
            data = response.json()
            assert data['status'] == 'ok'
            assert 'timestamp' in data
            assert data['database'] == 'ok'
            assert data['cache'] == 'ok'
    
    def test_health_check_view_database_error(self):
        """Тест health check с ошибкой базы данных"""
        from core.health_check import health_check_view
        
        factory = RequestFactory()
        request = factory.get('/health/')
        
        with patch('django.db.connection.cursor', side_effect=Exception('DB Error')), \
             patch('django.core.cache.cache') as mock_cache:
            
            mock_cache.set.return_value = True
            mock_cache.get.return_value = 'test_value'
            
            response = health_check_view(request)
            
            assert response.status_code == 500
            
            data = response.json()
            assert data['status'] == 'degraded'
            assert 'error: DB Error' in data['database']
            assert data['cache'] == 'ok'
    
    def test_health_check_view_cache_error(self):
        """Тест health check с ошибкой кэша"""
        from core.health_check import health_check_view
        
        factory = RequestFactory()
        request = factory.get('/health/')
        
        with patch('django.db.connection.cursor') as mock_cursor, \
             patch('django.core.cache.cache', side_effect=Exception('Cache Error')):
            
            mock_cursor.return_value.__enter__.return_value.execute = Mock()
            
            response = health_check_view(request)
            
            assert response.status_code == 500
            
            data = response.json()
            assert data['status'] == 'degraded'
            assert data['database'] == 'ok'
            assert 'error: Cache Error' in data['cache']
    
    def test_simple_health_check(self):
        """Тест простого health check"""
        from core.health_check import simple_health_check
        from django.http import JsonResponse
        
        factory = RequestFactory()
        request = factory.get('/health/simple/')
        
        response = simple_health_check(request)
        
        assert isinstance(response, JsonResponse)
        assert response.status_code == 200
        
        data = response.json()
        assert data['status'] == 'ok'
        assert 'timestamp' in data

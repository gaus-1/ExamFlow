#!/usr/bin/env python
"""
Простые тесты для увеличения покрытия кода
"""

from django.test import TestCase
from django.http import HttpRequest
from unittest.mock import patch
import json

from core.health_check import health_check_view
from core.utils import generate_qr_code
from core.fallback_views import FallbackAIView, fallback_subjects_view


class TestSimpleCoverage(TestCase):
    """Простые тесты для покрытия"""
    
    def test_health_check_view_success(self):
        """Тест успешного health check"""
        request = HttpRequest()
        request.method = 'GET' # type: ignore
        
        with patch('core.health_check.connection.cursor') as mock_cursor:
            mock_cursor.return_value.__enter__.return_value.execute.return_value = None
            with patch('core.health_check.cache') as mock_cache:
                mock_cache.set.return_value = None
                mock_cache.get.return_value = 'ok'
                
                response = health_check_view(request)
                
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.content)
                self.assertEqual(data['status'], 'healthy')
                self.assertEqual(data['database'], 'connected')
                self.assertEqual(data['cache'], 'connected')
    
    def test_health_check_view_database_error(self):
        """Тест health check с ошибкой БД"""
        request = HttpRequest()
        request.method = 'GET' # type: ignore
        
        with patch('core.health_check.connection.cursor') as mock_cursor:
            mock_cursor.return_value.__enter__.side_effect = Exception('DB Error')
            with patch('core.health_check.cache') as mock_cache:
                mock_cache.set.return_value = None
                mock_cache.get.return_value = 'ok'
                
                response = health_check_view(request)
                
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.content)
                self.assertEqual(data['status'], 'unhealthy')
                self.assertEqual(data['database'], 'error')
                self.assertEqual(data['cache'], 'connected')
    
    def test_health_check_view_cache_error(self):
        """Тест health check с ошибкой кэша"""
        request = HttpRequest()
        request.method = 'GET' # type: ignore
        
        with patch('core.health_check.connection.cursor') as mock_cursor:
            mock_cursor.return_value.__enter__.return_value.execute.return_value = None
            with patch('core.health_check.cache') as mock_cache:
                mock_cache.set.side_effect = Exception('Cache Error')
                
                response = health_check_view(request)
                
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.content)
                self.assertEqual(data['status'], 'healthy')
                self.assertEqual(data['database'], 'connected')
                self.assertEqual(data['cache'], 'error')
    
    def test_generate_qr_code_success(self):
        """Тест успешной генерации QR кода"""
        url = "https://t.me/examflow_bot"
        result = generate_qr_code(url)
        
        self.assertTrue(result.startswith("data:image/png;base64,"))
        self.assertGreater(len(result), 50)
    
    def test_generate_qr_code_error(self):
        """Тест генерации QR кода с ошибкой"""
        with patch('qrcode.QRCode') as mock_qr:
            mock_qr.side_effect = Exception("QR generation error")
            
            url = "https://example.com"
            result = generate_qr_code(url)
            
            self.assertTrue(result.startswith("data:text/plain;base64,"))
    
    def test_fallback_ai_view_get(self):
        """Тест FallbackAIView GET запроса"""
        request = HttpRequest()
        request.method = 'GET' # type: ignore
        
        view = FallbackAIView()
        response = view.get(request) # type: ignore
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('answer', data)
        self.assertIn('status', data)
    
    def test_fallback_ai_view_post(self):
        """Тест FallbackAIView POST запроса"""
        request = HttpRequest()
        request.method = 'POST' # type: ignore
        request.body = json.dumps({'query': 'test'}).encode() # type: ignore

        view = FallbackAIView()
        response = view.post(request) # type: ignore
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('answer', data)
        self.assertIn('status', data)
    
    def test_fallback_subjects_view(self):
        """Тест fallback_subjects_view"""
        request = HttpRequest()
        
        response = fallback_subjects_view(request)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('subjects', data)
        self.assertIsInstance(data['subjects'], list)
        self.assertGreater(len(data['subjects']), 0)

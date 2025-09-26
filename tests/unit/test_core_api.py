#!/usr/bin/env python
"""
Тесты для API core приложения
"""

from django.test import TestCase, RequestFactory
from unittest.mock import Mock, patch
import json
import os

from core.api import AIQueryView, SearchView, VectorStoreStatsView


class TestCoreAPI(TestCase):
    """Тесты для API core"""
    
    def setUp(self):
        """Настройка тестовых данных"""
        self.factory = RequestFactory()
        self.ai_view = AIQueryView()
        # Исправлено: используем правильные имена классов, импортируемые из core.api
        self.search_view = SearchView()
        self.vector_view = VectorStoreStatsView()
    
    def test_ai_query_empty_request(self):
        """Тест AI запроса с пустым телом"""
        request = self.factory.post('/api/ai/', data='{}', content_type='application/json')
        response = self.ai_view.post(request)
        
        assert response.status_code == 400
        data = json.loads(response.content)
        assert 'error' in data
        assert 'answer' in data
    
    def test_ai_query_empty_query(self):
        """Тест AI запроса с пустым запросом"""
        request_data = {'query': '', 'user_id': 123}
        request = self.factory.post('/api/ai/', data=json.dumps(request_data), content_type='application/json')
        response = self.ai_view.post(request)
        
        assert response.status_code == 400
        data = json.loads(response.content)
        assert 'error' in data
        assert 'Пустой запрос' in data['error']
    
    def test_ai_query_whitespace_query(self):
        """Тест AI запроса с запросом из пробелов"""
        request_data = {'query': '   ', 'user_id': 123}
        request = self.factory.post('/api/ai/', data=json.dumps(request_data), content_type='application/json')
        response = self.ai_view.post(request)
        
        assert response.status_code == 400
        data = json.loads(response.content)
        assert 'error' in data
    
    def test_ai_query_valid_request_fallback_mode(self):
        """Тест AI запроса в fallback режиме"""
        with patch.dict(os.environ, {'FALLBACK_MODE': 'true'}):
            request_data = {'query': 'Что такое ЕГЭ?', 'user_id': 123}
            request = self.factory.post('/api/ai/', data=json.dumps(request_data), content_type='application/json')
            
            with patch('core.api.google.generativeai') as mock_gemini:
                mock_model = Mock()
                mock_response = Mock()
                mock_response.text = 'ЕГЭ - это единый государственный экзамен.'
                mock_model.generate_content.return_value = mock_response
                mock_gemini.GenerativeModel.return_value = mock_model
                mock_gemini.configure.return_value = None
                
                response = self.ai_view.post(request)
                
                assert response.status_code == 200
                data = json.loads(response.content)
                assert 'answer' in data
                assert 'ЕГЭ - это единый государственный экзамен.' in data['answer']
    
    def test_ai_query_valid_request_normal_mode(self):
        """Тест AI запроса в обычном режиме"""
        with patch.dict(os.environ, {'FALLBACK_MODE': 'false'}):
            request_data = {'query': 'Что такое ЕГЭ?', 'user_id': 123}
            request = self.factory.post('/api/ai/', data=json.dumps(request_data), content_type='application/json')
            
            with patch('core.api.RAGOrchestrator') as mock_orchestrator_class:
                mock_orchestrator = Mock()
                mock_orchestrator_class.return_value = mock_orchestrator
                mock_orchestrator.process_query.return_value = 'ЕГЭ - это единый государственный экзамен.'
                
                response = self.ai_view.post(request)
                
                assert response.status_code == 200
                data = json.loads(response.content)
                assert 'answer' in data
                assert 'ЕГЭ - это единый государственный экзамен.' in data['answer']
    
    def test_ai_query_gemini_api_error(self):
        """Тест AI запроса с ошибкой Gemini API"""
        with patch.dict(os.environ, {'FALLBACK_MODE': 'true'}):
            request_data = {'query': 'Что такое ЕГЭ?', 'user_id': 123}
            request = self.factory.post('/api/ai/', data=json.dumps(request_data), content_type='application/json')
            
            with patch('core.api.google.generativeai') as mock_gemini:
                mock_gemini.configure.side_effect = Exception('API Error')
                
                response = self.ai_view.post(request)
                
                assert response.status_code == 200
                data = json.loads(response.content)
                assert 'answer' in data
                assert 'Извините, произошла ошибка' in data['answer']
    
    def test_ai_query_rag_error(self):
        """Тест AI запроса с ошибкой RAG системы"""
        with patch.dict(os.environ, {'FALLBACK_MODE': 'false'}):
            request_data = {'query': 'Что такое ЕГЭ?', 'user_id': 123}
            request = self.factory.post('/api/ai/', data=json.dumps(request_data), content_type='application/json')
            
            with patch('core.api.RAGOrchestrator') as mock_orchestrator_class:
                mock_orchestrator = Mock()
                mock_orchestrator_class.return_value = mock_orchestrator
                mock_orchestrator.process_query.side_effect = Exception('RAG Error')
                
                response = self.ai_view.post(request)
                
                assert response.status_code == 200
                data = json.loads(response.content)
                assert 'answer' in data
                assert 'Извините, произошла ошибка' in data['answer']
    
    def test_ai_query_json_decode_error(self):
        """Тест AI запроса с некорректным JSON"""
        request = self.factory.post('/api/ai/', data='invalid json', content_type='application/json')
        response = self.ai_view.post(request)
        
        assert response.status_code == 200
        data = json.loads(response.content)
        assert 'answer' in data
        assert 'Извините, произошла ошибка' in data['answer']
    
    def test_search_api_empty_query(self):
        """Тест Search API с пустым запросом"""
        request = self.factory.get('/api/search/?query=')
        response = self.search_view.get(request) # type: ignore
        
        assert response.status_code == 400
        data = json.loads(response.content)
        assert 'error' in data
    
    def test_search_api_valid_query(self):
        """Тест Search API с валидным запросом"""
        request = self.factory.get('/api/search/?query=математика')
        
        with patch('core.api.VectorStore') as mock_vector_store_class:
            mock_vector_store = Mock()
            mock_vector_store_class.return_value = mock_vector_store
            mock_vector_store.search.return_value = [
                {'id': 1, 'title': 'Задача по математике', 'content': 'Описание задачи'},
                {'id': 2, 'title': 'Еще одна задача', 'content': 'Описание'}
            ]
            
            response = self.search_view.get(request) # type: ignore
            
            assert response.status_code == 200
            data = json.loads(response.content)
            assert 'results' in data
            assert len(data['results']) == 2
    
    def test_search_api_vector_store_error(self):
        """Тест Search API с ошибкой VectorStore"""
        request = self.factory.get('/api/search/?query=математика')
        
        with patch('core.api.VectorStore') as mock_vector_store_class:
            mock_vector_store = Mock()
            mock_vector_store_class.return_value = mock_vector_store
            mock_vector_store.search.side_effect = Exception('Vector Store Error')
            
            response = self.search_view.get(request) # type: ignore
            
            assert response.status_code == 500
            data = json.loads(response.content)
            assert 'error' in data
    
    def test_vector_store_api_add_document(self):
        """Тест VectorStore API для добавления документа"""
        request_data = {
            'title': 'Тестовый документ',
            'content': 'Содержимое документа',
            'metadata': {'subject': 'math'}
        }
        request = self.factory.post('/api/vector/', data=json.dumps(request_data), content_type='application/json')
        
        with patch('core.api.VectorStore') as mock_vector_store_class:
            mock_vector_store = Mock()
            mock_vector_store_class.return_value = mock_vector_store
            mock_vector_store.add_document.return_value = 'doc_id_123'
            
            response = self.vector_view.post(request) # type: ignore
            
            assert response.status_code == 200
            data = json.loads(response.content)
            assert 'document_id' in data
            assert data['document_id'] == 'doc_id_123'
    
    def test_vector_store_api_delete_document(self):
        """Тест VectorStore API для удаления документа"""
        request = self.factory.delete('/api/vector/doc_id_123/')
        
        with patch('core.api.VectorStore') as mock_vector_store_class:
            mock_vector_store = Mock()
            mock_vector_store_class.return_value = mock_vector_store
            mock_vector_store.delete_document.return_value = True
            
            response = self.vector_view.delete(request, document_id='doc_id_123') # type: ignore
            
            assert response.status_code == 200
            data = json.loads(response.content)
            assert 'success' in data
            assert data['success'] is True
    
    def test_vector_store_api_get_document(self):
        """Тест VectorStore API для получения документа"""
        request = self.factory.get('/api/vector/doc_id_123/')
        
        with patch('core.api.VectorStore') as mock_vector_store_class:
            mock_vector_store = Mock()
            mock_vector_store_class.return_value = mock_vector_store
            mock_vector_store.get_document.return_value = {
                'id': 'doc_id_123',
                'title': 'Тестовый документ',
                'content': 'Содержимое'
            }
            
            response = self.vector_view.get(request, document_id='doc_id_123') # type: ignore
            
            assert response.status_code == 200
            data = json.loads(response.content)
            assert 'document' in data
            assert data['document']['id'] == 'doc_id_123'
    
    def test_vector_store_api_document_not_found(self):
        """Тест VectorStore API для несуществующего документа"""
        request = self.factory.get('/api/vector/nonexistent/')
        
        with patch('core.api.VectorStore') as mock_vector_store_class:
            mock_vector_store = Mock()
            mock_vector_store_class.return_value = mock_vector_store
            mock_vector_store.get_document.return_value = None
            
            response = self.vector_view.get(request, document_id='nonexistent') # type: ignore
            
            assert response.status_code == 404
            data = json.loads(response.content)
            assert 'error' in data
    
    def test_vector_store_api_invalid_json(self):
        """Тест VectorStore API с некорректным JSON"""
        request = self.factory.post('/api/vector/', data='invalid json', content_type='application/json')
        response = self.vector_view.post(request) # type: ignore
        
        assert response.status_code == 400
        data = json.loads(response.content)
        assert 'error' in data
    
    def test_vector_store_api_missing_fields(self):
        """Тест VectorStore API с отсутствующими полями"""
        request_data = {'title': 'Только заголовок'}  # Отсутствует content
        request = self.factory.post('/api/vector/', data=json.dumps(request_data), content_type='application/json')
        response = self.vector_view.post(request) # type: ignore    
        
        assert response.status_code == 400
        data = json.loads(response.content)
        assert 'error' in data

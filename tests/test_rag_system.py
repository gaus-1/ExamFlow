"""
Unit тесты для RAG системы
"""

from django.test import TestCase
from unittest.mock import patch, MagicMock
from core.rag_system.orchestrator import RAGOrchestrator
from core.rag_system.vector_store import VectorStore


class TestRAGOrchestrator(TestCase):
    """Тесты для AI Orchestrator"""
    
    def setUp(self):
        """Настройка тестов"""
        self.orchestrator = RAGOrchestrator()
    
    @patch('core.rag_system.orchestrator.VectorStore')
    def test_process_query_success(self, mock_vector_store):
        """Тест успешной обработки запроса"""
        # Мокаем векторный поиск
        mock_vector_store.return_value.search.return_value = [
            {
                'text': 'Тестовый контекст',
                'similarity': 0.85,
                'subject': 'mathematics',
                'source': 'fipi.ru'
            }
        ]
        
        # Мокаем AI ответ
        with patch.object(self.orchestrator, 'get_ai_response') as mock_ai:
            mock_ai.return_value = "Тестовый ответ от AI"
            
            result = self.orchestrator.process_query("Тестовый вопрос")
            
            self.assertIn('answer', result)
            self.assertIn('sources', result)
            self.assertIn('practice', result)
    
    def test_get_user_context_empty(self):
        """Тест получения контекста пользователя (пустой)"""
        context = self.orchestrator.get_user_context(999)  # Несуществующий пользователь # type: ignore
        self.assertEqual(context, {})
    
    def test_build_context_with_results(self):
        """Тест построения контекста с результатами"""
        search_results = [
            {
                'text': 'Контекст 1',
                'similarity': 0.9,
                'subject': 'mathematics',
                'source': 'fipi.ru'
            },
            {
                'text': 'Контекст 2', 
                'similarity': 0.8,
                'subject': 'physics',
                'source': 'fipi.ru'
            }
        ]
        
        context = self.orchestrator.build_context(search_results, {})  # type: ignore
        
        self.assertIn('Контекст 1', context)
        self.assertIn('Контекст 2', context)
        self.assertIn('Релевантность: 0.90', context)
        self.assertIn('Релевантность: 0.80', context)
    
    def test_build_context_empty(self):
        """Тест построения контекста без результатов"""
        context = self.orchestrator.build_context([], {})  # type: ignore
        self.assertEqual(context, "Релевантная информация не найдена.")
    
    def test_generate_prompt_optimized(self):
        """Тест оптимизированной генерации промпта"""
        query = "Как решить квадратное уравнение?"
        context = "Квадратное уравнение решается по формуле..."
        user_context = {
            'level': 2,
            'total_problems_solved': 15,
            'streak': 3
        }
        
        prompt = self.orchestrator.generate_prompt(query, context, user_context)  # type: ignore
        
        self.assertIn(query, prompt)
        self.assertIn(context, prompt)
        self.assertIn('уровень 2', prompt)
        self.assertIn('решено 15 задач', prompt)
        self.assertIn('серия 3', prompt)
        self.assertIn('Требования к ответу:', prompt)
    
    def test_generate_prompt_no_user_context(self):
        """Тест генерации промпта без контекста пользователя"""
        query = "Тестовый вопрос"
        context = "Тестовый контекст"
        
        prompt = self.orchestrator.generate_prompt(query, context, {})  # type: ignore  
        
        self.assertIn(query, prompt)
        self.assertIn(context, prompt)
        self.assertNotIn('Пользователь:', prompt)
    
    @patch('core.rag_system.orchestrator.genai')
    def test_get_ai_response_success(self, mock_genai):
        """Тест получения ответа от AI"""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Ответ от Gemini"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        # Пересоздаем orchestrator с мокнутой моделью
        orchestrator = RAGOrchestrator()
        orchestrator.model = mock_model  # type: ignore
        
        response = orchestrator.get_ai_response("Тестовый промпт")  # type: ignore
        
        self.assertEqual(response, "Ответ от Gemini")
        mock_model.generate_content.assert_called_once()
    
    def test_get_fallback_response(self):
        """Тест fallback ответа"""
        response = self.orchestrator.get_fallback_response("Тестовый вопрос", "Ошибка")  # type: ignore
        
        self.assertIn('Извините', response['answer'])
        self.assertIn('Тестовый вопрос', response['answer'])
        self.assertIn('sources', response)
        self.assertIn('practice', response)


class TestVectorStore(TestCase):
    """Тесты для Vector Store"""
    
    def setUp(self):
        """Настройка тестов"""
        self.vector_store = VectorStore()
    
    @patch('core.rag_system.vector_store.genai')
    def test_create_embedding_success(self, mock_genai):
        """Тест создания эмбеддинга"""
        mock_genai.embed_content.return_value = {
            'embedding': [0.1, 0.2, 0.3, 0.4, 0.5]
        }
        
        embedding = self.vector_store.create_embedding("Тестовый текст")  # type: ignore
        
        self.assertEqual(len(embedding), 5)
        self.assertEqual(embedding, [0.1, 0.2, 0.3, 0.4, 0.5])
        mock_genai.embed_content.assert_called_once()
    
    def test_cosine_similarity(self):
        """Тест вычисления косинусного сходства"""
        vec1 = [1, 0, 0]
        vec2 = [1, 0, 0]
        vec3 = [0, 1, 0]
        
        # Идентичные векторы
        similarity1 = self.vector_store.cosine_similarity(vec1, vec2) # type: ignore
        self.assertAlmostEqual(similarity1, 1.0, places=5)
        
        # Перпендикулярные векторы
        similarity2 = self.vector_store.cosine_similarity(vec1, vec3) # type: ignore
        self.assertAlmostEqual(similarity2, 0.0, places=5)
    
    def test_find_similar_chunks(self):
        """Тест поиска похожих чанков"""
        # Мокаем данные
        query_embedding = [1, 0, 0]
        chunks = [
            {'embedding': [1, 0, 0], 'text': 'Текст 1'},
            {'embedding': [0, 1, 0], 'text': 'Текст 2'},
            {'embedding': [0.9, 0.1, 0], 'text': 'Текст 3'}
        ]
        
        similar = self.vector_store.find_similar_chunks(query_embedding, chunks, limit=2) # type: ignore
        
        self.assertEqual(len(similar), 2)
        self.assertEqual(similar[0]['text'], 'Текст 1')  # Наиболее похожий
        self.assertEqual(similar[1]['text'], 'Текст 3')  # Второй по похожести
    
    @patch('core.rag_system.vector_store.genai')
    def test_search_success(self, mock_genai):
        """Тест поиска в векторном хранилище"""
        mock_genai.embed_content.return_value = {
            'embedding': [1, 0, 0]
        }
        
        # Мокаем поиск в БД
        with patch('core.rag_system.vector_store.DataChunk') as mock_chunk:
            mock_chunk.objects.all.return_value = [
                MagicMock(
                    embedding=[1, 0, 0],
                    text="Найденный текст",
                    subject="mathematics",
                    source="fipi.ru"
                )
            ]
            
            results = self.vector_store.search("тестовый запрос", limit=5)  # type: ignore
            
            self.assertIsInstance(results, list)
            if results:  # Если есть результаты
                self.assertIn('text', results[0])
                self.assertIn('similarity', results[0])
                self.assertIn('subject', results[0])
                self.assertIn('source', results[0])


class TestIntegration(TestCase):
    """Интеграционные тесты"""
    
    def setUp(self):
        """Настройка тестов"""
        self.orchestrator = RAGOrchestrator()
    
    @patch('core.rag_system.orchestrator.VectorStore')
    @patch('core.rag_system.orchestrator.genai')
    def test_full_pipeline(self, mock_genai, mock_vector_store):
        """Тест полного пайплайна обработки запроса"""
        # Настраиваем моки
        mock_vector_store.return_value.search.return_value = [
            {
                'text': 'Контекст о математике',
                'similarity': 0.9,
                'subject': 'mathematics',
                'source': 'fipi.ru'
            }
        ]
        
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Ответ на вопрос о математике"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        # Выполняем полный пайплайн
        result = self.orchestrator.process_query("Как решить уравнение?")
        
        # Проверяем результат
        self.assertIn('answer', result)
        self.assertIn('sources', result)
        self.assertIn('practice', result)
        self.assertEqual(result['answer'], "Ответ на вопрос о математике")
        
        # Проверяем, что все методы были вызваны
        mock_vector_store.return_value.search.assert_called_once()
        mock_model.generate_content.assert_called_once()

"""
Расширенные тесты для RAG системы с кэшированием.
"""

from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase

from core.rag_system.orchestrator import RAGOrchestrator


class TestRAGOrchestratorCaching(TestCase):
    """Тесты кэширования RAG системы."""

    def setUp(self):
        """Настройка тестов."""
        self.orchestrator = RAGOrchestrator()
        cache.clear()

    def test_cache_key_generation(self):
        """Тест генерации ключей кэша."""
        query = "тест запрос"
        subject = "математика"
        document_type = "задание"

        key1 = self.orchestrator._generate_cache_key(
            query, subject, document_type, "query"
        )
        key2 = self.orchestrator._generate_cache_key(
            query, subject, document_type, "search"
        )
        key3 = self.orchestrator._generate_cache_key(
            query, subject, document_type, "ai_response"
        )

        # Ключи должны быть разными для разных типов
        self.assertNotEqual(key1, key2)
        self.assertNotEqual(key2, key3)
        self.assertNotEqual(key1, key3)

        # Одинаковые параметры должны давать одинаковые ключи
        key1_dup = self.orchestrator._generate_cache_key(
            query, subject, document_type, "query"
        )
        self.assertEqual(key1, key1_dup)

    def test_search_results_caching(self):
        """Тест кэширования результатов поиска."""
        query = "тест запрос"
        subject = "математика"
        document_type = "задание"

        # Мокаем результаты поиска
        mock_results = []

        # Сохраняем в кэш
        self.orchestrator._cache_search_results(
            query, subject, document_type, mock_results
        )

        # Получаем из кэша
        cached_results = self.orchestrator._get_cached_search_results(
            query, subject, document_type
        )

        self.assertEqual(cached_results, mock_results)

    def test_ai_response_caching(self):
        """Тест кэширования ответов AI."""
        query = "тест запрос"
        subject = "математика"
        document_type = "задание"

        # Мокаем ответ AI
        mock_response = {
            "answer": "тест ответ",
            "sources": ["источник 1"],
            "context_chunks": 2,
            "processing_time": 0.5,
            "cached": False,
        }

        # Сохраняем в кэш
        self.orchestrator._cache_ai_response(
            query, subject, document_type, mock_response
        )

        # Получаем из кэша
        cached_response = self.orchestrator._get_cached_ai_response(
            query, subject, document_type
        )

        self.assertEqual(cached_response, mock_response)

    @patch("core.rag_system.vector_store.VectorStore")
    def test_process_query_with_caching(self, mock_vector_store):
        """Тест обработки запроса с кэшированием."""
        # Настраиваем мок
        mock_vector_store.return_value.semantic_search.return_value = []

        # Мокаем генерацию ответа
        with patch.object(
            self.orchestrator, "_generate_answer", return_value="тест ответ"
        ):
            with patch.object(
                self.orchestrator, "_format_sources", return_value=["источник"]
            ):
                # Первый запрос - должен выполнить поиск и генерацию
                result1 = self.orchestrator.process_query(
                    query="тест запрос", subject="математика", document_type="задание"
                )

                # Второй запрос - должен взять из кэша
                result2 = self.orchestrator.process_query(
                    query="тест запрос", subject="математика", document_type="задание"
                )

                # Проверяем, что второй запрос был из кэша
                self.assertTrue(result2.get("cached", False))

                # Проверяем, что semantic_search был вызван только один раз
                self.assertEqual(
                    mock_vector_store.return_value.semantic_search.call_count, 1
                )

    def test_cache_ttl_configuration(self):
        """Тест конфигурации TTL кэша."""
        # Проверяем, что TTL берется из настроек
        self.assertEqual(self.orchestrator.cache_ttl, 600)  # 10 минут по умолчанию

        # Проверяем, что результаты поиска кэшируются на двойное время
        query = "тест"
        subject = "математика"
        document_type = "задание"

        mock_results = [{"text": "тест", "source": "источник"}]

        with patch("django.core.cache.cache.set") as mock_cache_set:
            self.orchestrator._cache_search_results(
                query, subject, document_type, mock_results
            )

            # Проверяем, что TTL для поиска в 2 раза больше
            mock_cache_set.assert_called_once()
            call_args = mock_cache_set.call_args
            self.assertEqual(call_args[1]["timeout"], self.orchestrator.cache_ttl * 2)


class TestRAGOrchestratorIntegration(TestCase):
    """Интеграционные тесты RAG системы."""

    def setUp(self):
        """Настройка тестов."""
        self.orchestrator = RAGOrchestrator()
        cache.clear()

    def test_configuration_loading(self):
        """Тест загрузки конфигурации из настроек."""
        # Проверяем, что настройки загружаются корректно
        self.assertIsNotNone(self.orchestrator.max_context_tokens)
        self.assertIsNotNone(self.orchestrator.cache_ttl)
        self.assertIsNotNone(self.orchestrator.top_k_chunks)
        self.assertIsNotNone(self.orchestrator.similarity_threshold)

    def test_error_handling(self):
        """Тест обработки ошибок."""
        # Тест с пустым запросом
        result = self.orchestrator.process_query("")
        self.assertIn("error", result)

        # Тест с некорректными параметрами
        result = self.orchestrator.process_query(
            query="тест",
            subject="несуществующий_предмет",
            document_type="несуществующий_тип",
        )
        # Должен вернуть результат, даже если ничего не найдено
        self.assertIn("answer", result)

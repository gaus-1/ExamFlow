"""
Unit тесты для RAG системы ExamFlow
"""

from unittest.mock import Mock, patch

import pytest


@pytest.mark.unit
@pytest.mark.django_db
class TestRAGOrchestrator:
    """Тесты RAG оркестратора"""

    def test_initialization(self):
        """Тест инициализации RAG оркестратора"""
        from core.rag_system.orchestrator import RAGOrchestrator

        orchestrator = RAGOrchestrator()

        assert orchestrator.initialized is True

    @patch("core.rag_system.orchestrator.logger")
    def test_process_query_success(self, mock_logger):
        """Тест успешной обработки запроса"""
        from core.rag_system.orchestrator import RAGOrchestrator

        orchestrator = RAGOrchestrator()

        with (
            patch.object(orchestrator, "_find_relevant_sources") as mock_find,
            patch.object(orchestrator, "_build_context") as mock_build,
        ):

            mock_find.return_value = [
                {
                    "title": "Задание 1",
                    "content": "Содержание 1",
                    "subject": "Математика",
                }
            ]
            mock_build.return_value = "Контекст из найденных источников"

            result = orchestrator.process_query("Решите уравнение", "Математика")

            assert "context" in result
            assert "sources" in result
            assert "context_chunks" in result
            assert "subject" in result
            assert result["context"] == "Контекст из найденных источников"
            assert len(result["sources"]) == 1
            assert result["context_chunks"] == 1
            assert result["subject"] == "Математика"

    @patch("core.rag_system.orchestrator.logger")
    def test_process_query_exception(self, mock_logger):
        """Тест обработки запроса с исключением"""
        from core.rag_system.orchestrator import RAGOrchestrator

        orchestrator = RAGOrchestrator()

        with patch.object(
            orchestrator, "_find_relevant_sources", side_effect=Exception("Test error")
        ):
            result = orchestrator.process_query("Тестовый запрос")

            assert result["context"] == ""
            assert result["sources"] == []
            assert result["context_chunks"] == 0
            mock_logger.error.assert_called_once()

    def test_find_relevant_sources_by_subject(self):
        """Тест поиска источников по предмету"""
        from core.rag_system.orchestrator import RAGOrchestrator

        orchestrator = RAGOrchestrator()

        with (
            patch("learning.models.Subject.objects.filter") as mock_subject_filter,
            patch("learning.models.Task.objects.filter") as mock_task_filter,
        ):

            # Мокаем предмет
            mock_subject = Mock()
            mock_subject_filter.return_value.first.return_value = mock_subject

            # Мокаем задания
            mock_task1 = Mock()
            mock_task1.title = "Уравнение"
            mock_task1.content = "Решите уравнение 2x + 3 = 7"
            mock_task1.id = 1

            mock_task2 = Mock()
            mock_task2.title = "Неравенство"
            mock_task2.content = "Решите неравенство x > 5"
            mock_task2.id = 2

            mock_task_filter.return_value.__getitem__.return_value = [
                mock_task1,
                mock_task2,
            ]

            sources = orchestrator._find_relevant_sources("уравнение", "Математика", 5)

            assert len(sources) >= 1
            assert sources[0]["title"] == "Уравнение"
            assert sources[0]["subject"] == "Математика"

    def test_find_relevant_sources_no_subject(self):
        """Тест поиска источников без указания предмета"""
        from core.rag_system.orchestrator import RAGOrchestrator

        orchestrator = RAGOrchestrator()

        # Тест без мока - просто проверяем что метод работает
        # В реальной базе данных могут быть или не быть задания
        sources = orchestrator._find_relevant_sources("задача", "", 5)

        # Проверяем что метод возвращает список (может быть пустой)
        assert isinstance(sources, list)

        # Если есть источники, проверяем их структуру
        if sources:
            assert "title" in sources[0]
            assert "content" in sources[0]
            assert "subject" in sources[0]
            assert "type" in sources[0]
            assert "id" in sources[0]

    def test_is_relevant_positive(self):
        """Тест определения релевантности - положительный случай"""
        from core.rag_system.orchestrator import RAGOrchestrator

        orchestrator = RAGOrchestrator()

        result = orchestrator._is_relevant(
            "уравнение", "Решите уравнение", "Найдите корень уравнения"
        )

        assert result is True

    def test_is_relevant_negative(self):
        """Тест определения релевантности - отрицательный случай"""
        from core.rag_system.orchestrator import RAGOrchestrator

        orchestrator = RAGOrchestrator()

        result = orchestrator._is_relevant(
            "физика", "Математическое задание", "Алгебра и геометрия"
        )

        assert result is False

    def test_build_context(self):
        """Тест построения контекста"""
        from core.rag_system.orchestrator import RAGOrchestrator

        orchestrator = RAGOrchestrator()

        sources = [
            {
                "title": "Задание 1",
                "content": "Краткое содержание",
                "subject": "Математика",
            },
            {
                "title": "Задание 2",
                "content": "Очень длинное содержание задания которое должно быть обрезано если превышает лимит символов в двести символов и даже больше чтобы точно проверить что обрезка работает корректно и добавляются три точки в конце текста когда он слишком длинный",
                "subject": "Русский",
            },
        ]

        context = orchestrator._build_context(sources, "Тестовый запрос")

        assert "[Математика] Задание 1" in context
        assert "[Русский] Задание 2" in context
        assert "Краткое содержание" in context
        # Проверяем что длинное содержание обрезается
        assert "..." in context

    def test_build_context_empty_sources(self):
        """Тест построения контекста из пустых источников"""
        from core.rag_system.orchestrator import RAGOrchestrator

        orchestrator = RAGOrchestrator()

        context = orchestrator._build_context([], "Тестовый запрос")

        assert context == ""

    def test_search_similar_content_compatibility(self):
        """Тест обратной совместимости search_similar_content"""
        from core.rag_system.orchestrator import RAGOrchestrator

        orchestrator = RAGOrchestrator()

        with patch.object(orchestrator, "process_query") as mock_process:
            mock_process.return_value = {
                "sources": [{"title": "Test", "content": "Test content"}]
            }

            result = orchestrator.search_similar_content("тест", limit=3)

            assert len(result) == 1
            assert result[0]["title"] == "Test"
            mock_process.assert_called_once_with("тест", limit=3)

    def test_get_context_for_query_compatibility(self):
        """Тест обратной совместимости get_context_for_query"""
        from core.rag_system.orchestrator import RAGOrchestrator

        orchestrator = RAGOrchestrator()

        with patch.object(orchestrator, "process_query") as mock_process:
            mock_process.return_value = {"context": "Тестовый контекст"}

            result = orchestrator.get_context_for_query("тест")

            assert result == "Тестовый контекст"
            mock_process.assert_called_once_with("тест")


@pytest.mark.unit
@pytest.mark.django_db
class TestVectorStore:
    """Тесты векторного хранилища"""

    def test_initialization(self):
        """Тест инициализации векторного хранилища"""
        from core.rag_system.vector_store import VectorStore

        store = VectorStore()

        assert store.documents == []
        assert store.index == {}

    @patch("core.rag_system.vector_store.logger")
    def test_initialize_with_existing_tasks(self, mock_logger):
        """Тест инициализации с загрузкой существующих заданий"""
        from core.rag_system.vector_store import VectorStore

        store = VectorStore()

        with patch.object(store, "_load_existing_tasks") as mock_load:
            store.initialize()

            mock_load.assert_called_once()
            mock_logger.info.assert_called()

    def test_add_document(self):
        """Тест добавления документа"""
        from core.rag_system.vector_store import VectorStore

        store = VectorStore()

        store.add_document(
            "Тестовое содержимое документа",
            {"type": "task", "subject": "Математика", "id": 1},
        )

        assert len(store.documents) == 1
        assert store.documents[0]["content"] == "Тестовое содержимое документа"
        assert store.documents[0]["metadata"]["type"] == "task"
        assert store.documents[0]["metadata"]["subject"] == "Математика"
        assert len(store.documents[0]["tokens"]) > 0

    def test_add_document_empty_content(self):
        """Тест добавления документа с пустым содержимым"""
        from core.rag_system.vector_store import VectorStore

        store = VectorStore()

        store.add_document("", {"type": "task"})

        assert len(store.documents) == 0

    def test_search_relevant_documents(self):
        """Тест поиска релевантных документов"""
        from core.rag_system.vector_store import VectorStore

        store = VectorStore()

        # Добавляем документы
        store.add_document(
            "Математическое уравнение 2x + 3 = 7", {"subject": "Математика"}
        )
        store.add_document("Русский язык орфография правила", {"subject": "Русский"})
        store.add_document("Геометрия треугольник площадь", {"subject": "Математика"})

        # Ищем релевантные документы
        results = store.search("уравнение математика", limit=2)

        assert len(results) >= 1
        assert results[0]["score"] > 0
        assert "уравнение" in results[0]["content"].lower()

    def test_search_empty_query(self):
        """Тест поиска с пустым запросом"""
        from core.rag_system.vector_store import VectorStore

        store = VectorStore()
        store.add_document("Тестовое содержимое", {"subject": "Тест"})

        results = store.search("", limit=5)

        assert len(results) == 0

    def test_search_no_documents(self):
        """Тест поиска в пустом хранилище"""
        from core.rag_system.vector_store import VectorStore

        store = VectorStore()

        results = store.search("тест", limit=5)

        assert len(results) == 0

    def test_search_by_subject(self):
        """Тест поиска по предмету"""
        from core.rag_system.vector_store import VectorStore

        store = VectorStore()

        # Добавляем документы по разным предметам
        store.add_document("Математика алгебра уравнения", {"subject": "Математика"})
        store.add_document("Русский язык грамматика", {"subject": "Русский"})
        store.add_document(
            "Математика геометрия треугольники", {"subject": "Математика"}
        )

        # Ищем только по математике
        results = store.search_by_subject("математика", "Математика", limit=5)

        assert len(results) >= 1
        for result in results:
            assert "математика" in result["metadata"]["subject"].lower()

    def test_tokenize_text(self):
        """Тест токенизации текста"""
        from core.rag_system.vector_store import VectorStore

        store = VectorStore()

        tokens = store._tokenize("Решите уравнение: 2x + 3 = 7")

        assert "решите" in tokens
        assert "уравнение" in tokens
        # Токены короче 2 символов удаляются
        assert "2x" not in tokens  # Удаляется как короткий токен
        assert "3" not in tokens  # Удаляется как короткий токен
        assert "7" not in tokens  # Удаляется как короткий токен
        # Стоп-слова должны быть удалены
        assert "и" not in tokens
        assert "в" not in tokens

    def test_calculate_similarity(self):
        """Тест вычисления сходства"""
        from core.rag_system.vector_store import VectorStore

        store = VectorStore()

        query_tokens = ["математика", "уравнение", "решить"]
        doc_tokens = ["математика", "уравнение", "алгебра", "задача"]

        similarity = store._calculate_similarity(query_tokens, doc_tokens)

        assert similarity > 0
        assert similarity <= 1

    def test_calculate_similarity_no_common_tokens(self):
        """Тест вычисления сходства без общих токенов"""
        from core.rag_system.vector_store import VectorStore

        store = VectorStore()

        query_tokens = ["математика", "уравнение"]
        doc_tokens = ["физика", "механика"]

        similarity = store._calculate_similarity(query_tokens, doc_tokens)

        assert similarity == 0.0

    def test_calculate_similarity_empty_tokens(self):
        """Тест вычисления сходства с пустыми токенами"""
        from core.rag_system.vector_store import VectorStore

        store = VectorStore()

        similarity = store._calculate_similarity([], [])
        assert similarity == 0.0

        similarity = store._calculate_similarity(["математика"], [])
        assert similarity == 0.0

        similarity = store._calculate_similarity([], ["математика"])
        assert similarity == 0.0

    def test_update_index(self):
        """Тест обновления индекса"""
        from core.rag_system.vector_store import VectorStore

        store = VectorStore()

        document = {"id": 0, "tokens": ["математика", "уравнение", "алгебра"]}

        store._update_index(document)

        assert "математика" in store.index
        assert "уравнение" in store.index
        assert "алгебра" in store.index
        assert 0 in store.index["математика"]

    def test_get_documents_by_metadata(self):
        """Тест получения документов по метаданным"""
        from core.rag_system.vector_store import VectorStore

        store = VectorStore()

        # Добавляем документы с разными метаданными
        store.add_document(
            "Математика 1", {"subject": "Математика", "difficulty": "easy"}
        )
        store.add_document(
            "Математика 2", {"subject": "Математика", "difficulty": "hard"}
        )
        store.add_document("Физика 1", {"subject": "Физика", "difficulty": "easy"})

        # Получаем документы по предмету
        math_docs = store.get_documents_by_metadata("subject", "Математика")
        assert len(math_docs) == 2

        # Получаем документы по сложности
        easy_docs = store.get_documents_by_metadata("difficulty", "easy")
        assert len(easy_docs) == 2

    def test_get_stats(self):
        """Тест получения статистики хранилища"""
        from core.rag_system.vector_store import VectorStore

        store = VectorStore()

        # Добавляем документы
        store.add_document("Математика 1", {"subject": "Математика"})
        store.add_document("Математика 2", {"subject": "Математика"})
        store.add_document("Русский 1", {"subject": "Русский"})

        stats = store.get_stats()

        assert stats["total_documents"] == 3
        assert stats["subjects"]["Математика"] == 2
        assert stats["subjects"]["Русский"] == 1
        assert stats["index_size"] > 0

    @patch("learning.models.Task.objects.select_related")
    def test_load_existing_tasks(self, mock_tasks):
        """Тест загрузки существующих заданий"""
        from core.rag_system.vector_store import VectorStore

        store = VectorStore()

        # Мокаем задания
        mock_task1 = Mock()
        mock_task1.title = "Задание 1"
        mock_task1.content = "Содержание задания 1"
        mock_task1.subject.name = "Математика"
        mock_task1.id = 1

        mock_task2 = Mock()
        mock_task2.title = "Задание 2"
        mock_task2.content = "Содержание задания 2"
        mock_task2.subject.name = "Русский"
        mock_task2.id = 2

        mock_tasks.return_value.all.return_value = [mock_task1, mock_task2]

        store._load_existing_tasks()

        assert len(store.documents) == 2
        assert store.documents[0]["metadata"]["subject"] == "Математика"
        assert store.documents[1]["metadata"]["subject"] == "Русский"

    @patch(
        "learning.models.Task.objects.select_related", side_effect=Exception("DB Error")
    )
    @patch("core.rag_system.vector_store.logger")
    def test_load_existing_tasks_error(self, mock_logger, mock_tasks):
        """Тест загрузки заданий с ошибкой"""
        from core.rag_system.vector_store import VectorStore

        store = VectorStore()

        store._load_existing_tasks()

        mock_logger.error.assert_called_once()
        assert len(store.documents) == 0

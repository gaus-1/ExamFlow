"""
Unit тесты для сервисов ExamFlow
"""

from unittest.mock import Mock, patch

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.unit
@pytest.mark.django_db
class TestUnifiedProfileService:
    """Тесты сервиса унифицированных профилей"""

    def test_get_or_create_profile_existing(self, user):
        """Тест получения существующего профиля"""
        from core.models import UserProfile
        from core.services.unified_profile import UnifiedProfileService

        # Создаем существующий профиль
        existing_profile = UserProfile.objects.create(
            user=user, telegram_id=123456789, telegram_username="existing_user"
        )

        # Получаем профиль
        profile = UnifiedProfileService.get_or_create_profile(
            telegram_id=123456789, telegram_username="existing_user"
        )

        assert profile == existing_profile
        assert profile.telegram_id == 123456789

    def test_get_or_create_profile_new(self):
        """Тест создания нового профиля"""
        from core.services.unified_profile import UnifiedProfileService

        profile = UnifiedProfileService.get_or_create_profile(
            telegram_id=999888777, telegram_username="new_user"
        )

        assert profile.telegram_id == 999888777
        assert profile.telegram_username == "new_user"

    def test_get_or_create_profile_with_user(self, user):
        """Тест создания профиля с существующим пользователем"""
        from core.services.unified_profile import UnifiedProfileService

        profile = UnifiedProfileService.get_or_create_profile(
            telegram_id=111222333, telegram_username="user_with_django", user=user
        )

        assert profile.telegram_id == 111222333
        assert profile.user == user

    def test_update_profile_activity(self, user_profile):
        """Тест обновления активности профиля"""
        from core.services.unified_profile import UnifiedProfileService

        # Мокаем метод save
        with patch.object(user_profile, "save") as mock_save:
            UnifiedProfileService.update_profile_activity(
                user_profile, activity_type="message"
            )
            mock_save.assert_called_once()

    def test_get_profile_progress(self, user):
        """Тест получения прогресса профиля"""
        from core.models import UserProfile
        from core.services.unified_profile import UnifiedProfileService
        from learning.models import UserProgress

        # Создаем профиль
        profile = UserProfile.objects.create(
            user=user, telegram_id=123456789, telegram_username="testuser"
        )

        # Создаем прогресс
        UserProgress.objects.create(
            user=user, task=Mock(), is_correct=True, attempts=1  # Мокаем задание
        )

        progress = UnifiedProfileService.get_profile_progress(profile)

        assert "total_tasks" in progress
        assert "completed_tasks" in progress
        assert "success_rate" in progress
        assert "current_streak" in progress


@pytest.mark.unit
@pytest.mark.django_db
class TestChatSessionService:
    """Тесты сервиса чат-сессий"""

    def test_create_session(self, user):
        """Тест создания чат-сессии"""
        from core.services.chat_session import ChatSessionService

        session = ChatSessionService.create_session(
            user_id=user.id, subject="Математика"
        )

        assert session is not None
        assert hasattr(session, "user_id")
        assert hasattr(session, "subject")

    def test_get_session(self, user):
        """Тест получения чат-сессии"""
        from core.services.chat_session import ChatSessionService

        # Создаем сессию
        created_session = ChatSessionService.create_session(
            user_id=user.id, subject="Русский язык"
        )

        # Получаем сессию
        retrieved_session = ChatSessionService.get_session(user.id)

        assert retrieved_session is not None

    def test_update_session(self, user):
        """Тест обновления чат-сессии"""
        from core.services.chat_session import ChatSessionService

        session = ChatSessionService.create_session(
            user_id=user.id, subject="Математика"
        )

        # Обновляем сессию
        updated_session = ChatSessionService.update_session(
            user.id, context={"last_message": "Привет!"}
        )

        assert updated_session is not None

    def test_delete_session(self, user):
        """Тест удаления чат-сессии"""
        from core.services.chat_session import ChatSessionService

        # Создаем сессию
        session = ChatSessionService.create_session(
            user_id=user.id, subject="Математика"
        )

        # Удаляем сессию
        result = ChatSessionService.delete_session(user.id)

        assert result is True


@pytest.mark.unit
class TestContainerService:
    """Тесты контейнера зависимостей"""

    def test_ai_orchestrator_singleton(self):
        """Тест синглтона AI оркестратора"""
        from core.container import Container

        # Получаем первый экземпляр
        ai1 = Container.ai_orchestrator()

        # Получаем второй экземпляр
        ai2 = Container.ai_orchestrator()

        # Должны быть одним и тем же объектом
        assert ai1 is ai2

    def test_cache_singleton(self):
        """Тест синглтона кэша"""
        from core.container import Container

        cache1 = Container.cache()
        cache2 = Container.cache()

        assert cache1 is cache2

    def test_notifier_singleton(self):
        """Тест синглтона уведомлений"""
        from core.container import Container

        notifier1 = Container.notifier()
        notifier2 = Container.notifier()

        assert notifier1 is notifier2

    @patch("core.container.AiService")
    def test_ai_orchestrator_with_ai_service(self, mock_ai_service):
        """Тест AI оркестратора с AiService"""
        from core.container import Container

        # Сбрасываем синглтон
        Container._ai_orchestrator_instance = None

        mock_instance = Mock()
        mock_ai_service.return_value = mock_instance

        ai = Container.ai_orchestrator()

        assert ai == mock_instance
        mock_ai_service.assert_called_once()

    @patch("core.container.AiService", side_effect=ImportError)
    def test_ai_orchestrator_fallback(self, mock_ai_service):
        """Тест fallback AI оркестратора"""
        from core.container import Container, SimpleAIOrchestrator

        # Сбрасываем синглтон
        Container._ai_orchestrator_instance = None

        ai = Container.ai_orchestrator()

        assert isinstance(ai, SimpleAIOrchestrator)

    @patch("django.core.cache.cache")
    def test_cache_with_django_cache(self, mock_cache):
        """Тест кэша с Django cache"""
        from core.container import Container

        # Сбрасываем синглтон
        Container._cache_instance = None

        cache = Container.cache()

        assert cache == mock_cache

    @patch("django.core.cache.cache", side_effect=Exception)
    def test_cache_fallback(self, mock_cache):
        """Тест fallback кэша"""
        from core.container import Container, DummyCache

        # Сбрасываем синглтон
        Container._cache_instance = None

        cache = Container.cache()

        assert isinstance(cache, DummyCache)


@pytest.mark.unit
class TestSimpleAIOrchestrator:
    """Тесты простого AI оркестратора"""

    def test_ask_with_valid_api_key(self):
        """Тест запроса с валидным API ключом"""
        from core.container import SimpleAIOrchestrator

        orchestrator = SimpleAIOrchestrator()

        with (
            patch("google.generativeai.configure") as mock_configure,
            patch("google.generativeai.GenerativeModel") as mock_model,
            patch("django.conf.settings.GEMINI_API_KEY", "test_key"),
        ):

            mock_model_instance = Mock()
            mock_model_instance.generate_content.return_value.text = "Тестовый ответ"
            mock_model.return_value = mock_model_instance

            result = orchestrator.ask("Тестовый вопрос")

            assert "answer" in result
            assert "sources" in result
            assert result["answer"] == "Тестовый ответ"
            mock_configure.assert_called_once_with(api_key="test_key")

    def test_ask_without_api_key(self):
        """Тест запроса без API ключа"""
        from core.container import SimpleAIOrchestrator

        orchestrator = SimpleAIOrchestrator()

        with patch("django.conf.settings.GEMINI_API_KEY", ""):
            result = orchestrator.ask("Тестовый вопрос")

            assert "error" in result
            assert "API key not configured" in result["error"]

    def test_ask_with_exception(self):
        """Тест запроса с исключением"""
        from core.container import SimpleAIOrchestrator

        orchestrator = SimpleAIOrchestrator()

        with patch("google.generativeai.configure", side_effect=Exception("API Error")):
            result = orchestrator.ask("Тестовый вопрос")

            assert "error" in result
            assert "API Error" in result["error"]

    def test_ask_empty_response(self):
        """Тест запроса с пустым ответом"""
        from core.container import SimpleAIOrchestrator

        orchestrator = SimpleAIOrchestrator()

        with (
            patch("google.generativeai.configure"),
            patch("google.generativeai.GenerativeModel") as mock_model,
            patch("django.conf.settings.GEMINI_API_KEY", "test_key"),
        ):

            mock_model_instance = Mock()
            mock_model_instance.generate_content.return_value.text = None
            mock_model.return_value = mock_model_instance

            result = orchestrator.ask("Тестовый вопрос")

            assert "error" in result
            assert "Empty response" in result["error"]

    def test_ask_long_response_truncation(self):
        """Тест обрезания длинного ответа"""
        from core.container import SimpleAIOrchestrator

        orchestrator = SimpleAIOrchestrator()

        long_response = "A" * 5000  # Очень длинный ответ

        with (
            patch("google.generativeai.configure"),
            patch("google.generativeai.GenerativeModel") as mock_model,
            patch("django.conf.settings.GEMINI_API_KEY", "test_key"),
        ):

            mock_model_instance = Mock()
            mock_model_instance.generate_content.return_value.text = long_response
            mock_model.return_value = mock_model_instance

            result = orchestrator.ask("Тестовый вопрос")

            assert len(result["answer"]) <= 4000
            assert result["answer"].endswith("...")


@pytest.mark.unit
class TestDummyCache:
    """Тесты заглушки кэша"""

    def test_get_default_value(self):
        """Тест получения значения по умолчанию"""
        from core.container import DummyCache

        cache = DummyCache()

        result = cache.get("nonexistent_key", "default_value")
        assert result == "default_value"

    def test_set_no_error(self):
        """Тест установки значения без ошибок"""
        from core.container import DummyCache

        cache = DummyCache()

        # Не должно вызывать исключений
        cache.set("key", "value")
        cache.set("key", "value", timeout=3600)

    def test_delete_no_error(self):
        """Тест удаления значения без ошибок"""
        from core.container import DummyCache

        cache = DummyCache()

        # Не должно вызывать исключений
        cache.delete("key")


@pytest.mark.unit
class TestSimpleNotifier:
    """Тесты простого уведомления"""

    def test_send_notification(self):
        """Тест отправки уведомления"""
        from core.container import SimpleNotifier

        notifier = SimpleNotifier()

        result = notifier.send_notification("Тестовое уведомление", user_id=123)

        assert result is True

    def test_send_email(self):
        """Тест отправки email"""
        from core.container import SimpleNotifier

        notifier = SimpleNotifier()

        result = notifier.send_email(
            "Тестовая тема", "Тестовое сообщение", "test@examflow.ru"
        )

        assert result is True

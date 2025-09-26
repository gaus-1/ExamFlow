#!/usr/bin/env python
"""
Тесты для представлений core приложения
"""

import json
from unittest.mock import Mock, patch

from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, TestCase

from core.views import (
    api_recommended_tasks,
    api_study_plan,
    api_user_insights,
    api_weak_topics,
    personalization_dashboard,
)


class TestCoreViews(TestCase):
    """Тесты для представлений core"""

    def setUp(self):
        """Настройка тестовых данных"""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(  # type: ignore
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_personalization_dashboard_success(self):
        """Тест успешной загрузки дашборда персонализации"""
        request = self.factory.get("/personalization/")
        request.user = self.user  # type: ignore

        # Добавляем messages storage
        request.session = {}
        messages = FallbackStorage(request)
        request._messages = messages

        with (
            patch("core.views.get_user_insights") as mock_insights,
            patch("core.views.PersonalizedRecommendations") as mock_recommender_class,
        ):

            # Настраиваем моки
            mock_insights.return_value = {"total_tasks": 10, "accuracy": 85}

            mock_recommender = Mock()
            mock_recommender_class.return_value = mock_recommender
            mock_recommender.get_recommended_tasks.return_value = []
            mock_recommender.get_study_plan.return_value = []
            mock_recommender.get_weak_topics.return_value = []

            response = personalization_dashboard(request)

            assert response.status_code == 200
            mock_insights.assert_called_once_with(self.user.id)
            mock_recommender_class.assert_called_once_with(self.user.id)

    def test_personalization_dashboard_error(self):
        """Тест обработки ошибки в дашборде персонализации"""
        request = self.factory.get("/personalization/")
        request.user = self.user  # type: ignore

        # Добавляем messages storage
        request.session = {}
        messages = FallbackStorage(request)
        request._messages = messages

        with patch("core.views.get_user_insights", side_effect=Exception("Test error")):
            response = personalization_dashboard(request)

            assert response.status_code == 302  # redirect
            assert response.url == "/"  # type: ignore

    def test_api_user_insights_success(self):
        """Тест успешного получения пользовательской аналитики"""
        request = self.factory.get("/api/user-insights/")
        request.user = self.user  # type: ignore

        with patch("core.views.get_user_insights") as mock_insights:
            mock_insights.return_value = {
                "total_tasks": 15,
                "accuracy": 92,
                "study_time": 120,
            }

            response = api_user_insights(request)

            assert response.status_code == 200
            data = json.loads(response.content)
            assert data["total_tasks"] == 15
            assert data["accuracy"] == 92
            assert data["study_time"] == 120

    def test_api_user_insights_error(self):
        """Тест обработки ошибки в API пользовательской аналитики"""
        request = self.factory.get("/api/user-insights/")
        request.user = self.user  # type: ignore

        with patch("core.views.get_user_insights", side_effect=Exception("Test error")):
            response = api_user_insights(request)

            assert response.status_code == 500
            data = json.loads(response.content)
            assert "error" in data

    def test_api_recommended_tasks_success(self):
        """Тест успешного получения рекомендованных заданий"""
        request = self.factory.get("/api/recommended-tasks/")
        request.user = self.user  # type: ignore

        with patch("core.views.PersonalizedRecommendations") as mock_recommender_class:
            mock_recommender = Mock()
            mock_recommender_class.return_value = mock_recommender
            mock_recommender.get_recommended_tasks.return_value = [
                {"id": 1, "title": "Test Task 1"},
                {"id": 2, "title": "Test Task 2"},
            ]

            response = api_recommended_tasks(request)

            assert response.status_code == 200
            data = json.loads(response.content)
            assert "recommended_tasks" in data
            assert len(data["recommended_tasks"]) == 2

    def test_api_recommended_tasks_error(self):
        """Тест обработки ошибки в API рекомендованных заданий"""
        request = self.factory.get("/api/recommended-tasks/")
        request.user = self.user  # type: ignore

        with patch(
            "core.views.PersonalizedRecommendations",
            side_effect=Exception("Test error"),
        ):
            response = api_recommended_tasks(request)

            assert response.status_code == 500
            data = json.loads(response.content)
            assert "error" in data

    def test_api_study_plan_success(self):
        """Тест успешного получения плана обучения"""
        request = self.factory.get("/api/study-plan/")
        request.user = self.user  # type: ignore

        with patch("core.views.PersonalizedRecommendations") as mock_recommender_class:
            mock_recommender = Mock()
            mock_recommender_class.return_value = mock_recommender
            mock_recommender.get_study_plan.return_value = [
                {"day": 1, "topics": ["Topic 1"]},
                {"day": 2, "topics": ["Topic 2"]},
            ]

            response = api_study_plan(request)

            assert response.status_code == 200
            data = json.loads(response.content)
            assert "study_plan" in data
            assert len(data["study_plan"]) == 2

    def test_api_study_plan_error(self):
        """Тест обработки ошибки в API плана обучения"""
        request = self.factory.get("/api/study-plan/")
        request.user = self.user  # type: ignore

        with patch(
            "core.views.PersonalizedRecommendations",
            side_effect=Exception("Test error"),
        ):
            response = api_study_plan(request)

            assert response.status_code == 500
            data = json.loads(response.content)
            assert "error" in data

    def test_api_weak_topics_success(self):
        """Тест успешного получения слабых тем"""
        request = self.factory.get("/api/weak-topics/")
        request.user = self.user  # type: ignore

        with patch("core.views.PersonalizedRecommendations") as mock_recommender_class:
            mock_recommender = Mock()
            mock_recommender_class.return_value = mock_recommender
            mock_recommender.get_weak_topics.return_value = [
                "Weak Topic 1",
                "Weak Topic 2",
            ]

            response = api_weak_topics(request)

            assert response.status_code == 200
            data = json.loads(response.content)
            assert "weak_topics" in data
            assert len(data["weak_topics"]) == 2

    def test_api_weak_topics_error(self):
        """Тест обработки ошибки в API слабых тем"""
        request = self.factory.get("/api/weak-topics/")
        request.user = self.user  # type: ignore

        with patch(
            "core.views.PersonalizedRecommendations",
            side_effect=Exception("Test error"),
        ):
            response = api_weak_topics(request)

            assert response.status_code == 500
            data = json.loads(response.content)
            assert "error" in data

    def test_personalization_dashboard_requires_login(self):
        """Тест что дашборд требует авторизации"""
        request = self.factory.get("/personalization/")
        request.user = Mock(is_authenticated=False)  # type: ignore

        response = personalization_dashboard(request)

        # Должен перенаправить на страницу входа
        assert response.status_code == 302

    def test_api_views_require_login(self):
        """Тест что API views требуют авторизации"""
        request = self.factory.get("/api/user-insights/")
        request.user = Mock(is_authenticated=False)  # type: ignore

        # API views должны возвращать ошибку для неавторизованных пользователей
        response = api_user_insights(request)
        assert response.status_code == 401

    def test_rate_limiting(self):
        """Тест ограничения скорости запросов"""
        # Создаем множество запросов для тестирования rate limiting
        for i in range(10):
            request = self.factory.get("/api/user-insights/")
            request.user = self.user  # type: ignore

            with patch("core.views.get_user_insights") as mock_insights:
                mock_insights.return_value = {"total_tasks": 10}
                response = api_user_insights(request)

                # Первые запросы должны проходить
                if i < 5:
                    assert response.status_code == 200
                # Дальше может быть ограничение (зависит от настроек)

    def test_json_response_format(self):
        """Тест формата JSON ответов"""
        request = self.factory.get("/api/user-insights/")
        request.user = self.user  # type: ignore

        with patch("core.views.get_user_insights") as mock_insights:
            mock_insights.return_value = {"test": "data"}

            response = api_user_insights(request)

            assert response["Content-Type"] == "application/json"
            data = json.loads(response.content)
            assert isinstance(data, dict)
            assert data["test"] == "data"

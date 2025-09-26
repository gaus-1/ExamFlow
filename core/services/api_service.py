"""
Сервис для API операций
Применяет принцип Dependency Inversion Principle (DIP)
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

from django.contrib.auth.models import User
from django.http import JsonResponse

logger = logging.getLogger(__name__)


class APIResponseBuilder(ABC):
    """Абстрактный класс для построения API ответов"""

    @abstractmethod
    def build_success_response(self, data: Any) -> JsonResponse:
        """Построить успешный ответ"""
        pass

    @abstractmethod
    def build_error_response(
        self, message: str, status_code: int = 400
    ) -> JsonResponse:
        """Построить ответ с ошибкой"""
        pass


class StandardAPIResponseBuilder(APIResponseBuilder):
    """Стандартная реализация построителя API ответов"""

    def build_success_response(self, data: Any) -> JsonResponse:
        """Построить успешный ответ"""
        return JsonResponse(
            {"success": True, "data": data, "message": "Операция выполнена успешно"}
        )

    def build_error_response(
        self, message: str, status_code: int = 400
    ) -> JsonResponse:
        """Построить ответ с ошибкой"""
        return JsonResponse(
            {"success": False, "error": message, "data": None}, status=status_code
        )


class APIService:
    """Сервис для обработки API запросов"""

    def __init__(self, response_builder: APIResponseBuilder):
        self.response_builder = response_builder

    def handle_user_insights_request(self, user: User) -> JsonResponse:
        """Обработать запрос аналитики пользователя"""
        try:
            from .dashboard_service import DashboardService

            dashboard_service = DashboardService(user)
            insights = dashboard_service.get_user_insights()

            return self.response_builder.build_success_response(insights)

        except Exception as e:
            logger.error(f"Ошибка получения аналитики пользователя {user.id}: {e}")
            return self.response_builder.build_error_response(
                "Не удалось получить аналитику пользователя"
            )

    def handle_recommendations_request(
        self, user: User, limit: int = 6
    ) -> JsonResponse:
        """Обработать запрос рекомендаций"""
        try:
            from .dashboard_service import DashboardService

            dashboard_service = DashboardService(user)
            recommendations = dashboard_service.get_recommended_tasks(limit)

            return self.response_builder.build_success_response(recommendations)

        except Exception as e:
            logger.error(
                f"Ошибка получения рекомендаций для пользователя {user.id}: {e}"
            )
            return self.response_builder.build_error_response(
                "Не удалось получить рекомендации"
            )

    def handle_study_plan_request(self, user: User) -> JsonResponse:
        """Обработать запрос плана обучения"""
        try:
            from .dashboard_service import DashboardService

            dashboard_service = DashboardService(user)
            study_plan = dashboard_service.get_study_plan()

            return self.response_builder.build_success_response(study_plan)

        except Exception as e:
            logger.error(
                f"Ошибка получения плана обучения для пользователя {user.id}: {e}"
            )
            return self.response_builder.build_error_response(
                "Не удалось получить план обучения"
            )

    def handle_weak_topics_request(self, user: User) -> JsonResponse:
        """Обработать запрос слабых тем"""
        try:
            from .dashboard_service import DashboardService

            dashboard_service = DashboardService(user)
            weak_topics = dashboard_service.get_weak_topics()

            return self.response_builder.build_success_response(weak_topics)

        except Exception as e:
            logger.error(f"Ошибка получения слабых тем для пользователя {user.id}: {e}")
            return self.response_builder.build_error_response(
                "Не удалось получить слабые темы"
            )

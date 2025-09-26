"""
Сервисные классы для приложения core
Применяют принципы SOLID для улучшения архитектуры
"""

from .api_service import APIService, StandardAPIResponseBuilder
from .dashboard_service import DashboardService

__all__ = ["DashboardService", "APIService", "StandardAPIResponseBuilder"]

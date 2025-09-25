"""
Сервисные классы для приложения core
Применяют принципы SOLID для улучшения архитектуры
"""

from .dashboard_service import DashboardService
from .api_service import APIService, StandardAPIResponseBuilder

__all__ = [
    'DashboardService',
    'APIService', 
    'StandardAPIResponseBuilder'
]
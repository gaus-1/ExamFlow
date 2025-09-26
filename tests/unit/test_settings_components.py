"""
Тесты для settings components
"""

import pytest


@pytest.mark.unit
class TestSettingsComponents:
    """Тесты компонентов настроек"""

    def test_base_settings(self):
        """Тест базовых настроек"""
        from examflow_project.settings_components import base

        # Проверяем что модуль импортируется
        assert base is not None

    def test_csp_settings(self):
        """Тест CSP настроек"""
        from examflow_project.settings_components import csp

        # Проверяем что модуль импортируется
        assert csp is not None

    def test_logging_settings(self):
        """Тест настроек логирования"""
        from examflow_project.settings_components import logging

        # Проверяем что модуль импортируется
        assert logging is not None

    def test_rest_framework_settings(self):
        """Тест настроек REST Framework"""
        from examflow_project.settings_components import rest_framework

        # Проверяем что модуль импортируется
        assert rest_framework is not None

    def test_spectacular_settings(self):
        """Тест настроек Spectacular"""
        from examflow_project.settings_components import spectacular

        # Проверяем что модуль импортируется
        assert spectacular is not None

    def test_settings_imports(self):
        """Тест импортов настроек"""
        from examflow_project.settings_components import __init__

        # Проверяем что модуль импортируется
        assert __init__ is not None

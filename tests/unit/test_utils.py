"""
Тесты для utils модуля
"""

import pytest


@pytest.mark.unit
class TestUtils:
    """Тесты утилит"""
    
    def test_import_utils(self):
        """Тест импорта utils модуля"""
        from core import utils
        
        # Проверяем что модуль импортируется без ошибок
        assert utils is not None
    
    def test_utils_module_structure(self):
        """Тест структуры utils модуля"""
        from core import utils
        
        # Проверяем что модуль имеет ожидаемые атрибуты
        assert hasattr(utils, '__name__')
        assert utils.__name__ == 'core.utils'

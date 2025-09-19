"""
Простой тест для демонстрации работы тестовой инфраструктуры
"""

import pytest
from datetime import datetime


class TestSimpleFunctionality:
    """Тесты простой функциональности"""
    
    def test_basic_math(self):
        """Тест базовой математики"""
        assert 2 + 2 == 4
        assert 3 * 3 == 9
        assert 10 / 2 == 5
    
    def test_string_operations(self):
        """Тест операций со строками"""
        text = "ExamFlow"
        assert len(text) == 8
        assert text.lower() == "examflow"
        assert "Exam" in text
    
    def test_datetime_functionality(self):
        """Тест работы с датой и временем"""
        now = datetime.now()
        assert now.year >= 2024
        assert now.month >= 1
        assert now.day >= 1
    
    @pytest.mark.parametrize("input_value,expected", [
        (1, 1),
        (2, 4),
        (3, 9),
        (4, 16),
    ])
    def test_square_function(self, input_value, expected):
        """Параметризованный тест функции возведения в квадрат"""
        result = input_value ** 2
        assert result == expected
    
    def test_list_operations(self):
        """Тест операций со списками"""
        items = [1, 2, 3, 4, 5]
        assert len(items) == 5
        assert sum(items) == 15
        assert max(items) == 5
        assert min(items) == 1
    
    def test_dictionary_operations(self):
        """Тест операций со словарями"""
        data = {
            'name': 'ExamFlow',
            'version': '1.0',
            'status': 'active'
        }
        assert data['name'] == 'ExamFlow'
        assert len(data) == 3
        assert 'version' in data
    
    def test_exception_handling(self):
        """Тест обработки исключений"""
        with pytest.raises(ZeroDivisionError):
            _ = 1 / 0
        
        with pytest.raises(KeyError):
            _ = {}['missing_key']


class TestExamFlowSpecific:
    """Тесты специфичной для ExamFlow функциональности"""
    
    def test_math_subject_validation(self):
        """Тест валидации предмета математика"""
        math_subjects = ['математика', 'Математика', 'МАТЕМАТИКА']
        for subject in math_subjects:
            assert 'мат' in subject.lower()
    
    def test_russian_subject_validation(self):
        """Тест валидации предмета русский язык"""
        russian_subjects = ['русский', 'Русский язык', 'РУССКИЙ']
        for subject in russian_subjects:
            assert 'русск' in subject.lower()
    
    def test_ege_format_validation(self):
        """Тест валидации формата ЕГЭ"""
        ege_formats = ['ЕГЭ', 'егэ', 'Единый государственный экзамен']
        for format_name in ege_formats:
            assert 'ег' in format_name.lower() or 'единый' in format_name.lower()
    
    def test_oge_format_validation(self):
        """Тест валидации формата ОГЭ"""
        oge_formats = ['ОГЭ', 'огэ', 'Основной государственный экзамен']
        for format_name in oge_formats:
            assert 'ог' in format_name.lower() or 'основной' in format_name.lower()
    
    def test_telegram_id_validation(self):
        """Тест валидации Telegram ID"""
        valid_telegram_ids = [123456789, 987654321, 555666777]
        for telegram_id in valid_telegram_ids:
            assert isinstance(telegram_id, int)
            assert telegram_id > 0
            assert len(str(telegram_id)) >= 6


@pytest.mark.slow
class TestSlowOperations:
    """Тесты медленных операций"""
    
    def test_slow_calculation(self):
        """Тест медленного вычисления"""
        import time
        time.sleep(0.1)  # Имитация медленной операции
        result = sum(range(1000))
        assert result == 499500
    
    def test_large_data_processing(self):
        """Тест обработки больших данных"""
        large_list = list(range(10000))
        result = sum(large_list)
        assert result == 49995000

#!/usr/bin/env python
"""
Простые тесты для утилит без зависимости от БД
"""

import unittest
from unittest.mock import patch

from core.utils import generate_qr_code


class TestSimpleUtils(unittest.TestCase):
    """Простые тесты для утилит"""
    
    def test_generate_qr_code_success(self):
        """Тест успешной генерации QR кода"""
        url = "https://t.me/examflow_bot"
        result = generate_qr_code(url)
        
        self.assertTrue(result.startswith("data:image/png;base64,"))
        self.assertGreater(len(result), 50)
    
    def test_generate_qr_code_error(self):
        """Тест генерации QR кода с ошибкой"""
        with patch('qrcode.QRCode') as mock_qr:
            mock_qr.side_effect = Exception("QR generation error")
            
            url = "https://example.com"
            result = generate_qr_code(url)
            
            self.assertTrue(result.startswith("data:text/plain;base64,"))
    
    def test_generate_qr_code_empty_url(self):
        """Тест генерации QR кода с пустым URL"""
        result = generate_qr_code("")
        self.assertTrue(result.startswith("data:image/png;base64,") or 
                       result.startswith("data:text/plain;base64,"))
    
    def test_generate_qr_code_long_url(self):
        """Тест генерации QR кода с длинным URL"""
        long_url = "https://example.com/" + "a" * 1000
        result = generate_qr_code(long_url)
        self.assertTrue(result.startswith("data:image/png;base64,") or 
                       result.startswith("data:text/plain;base64,"))


if __name__ == '__main__':
    unittest.main()


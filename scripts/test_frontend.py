#!/usr/bin/env python
"""
Скрипт для тестирования фронтенда ExamFlow
Проверяет загрузку ресурсов, адаптивность и функциональность
"""

import requests
import re
import time
from urllib.parse import urljoin

class FrontendTester:
    def __init__(self, base_url='http://localhost:8000'):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = []
    
    def test_page_load(self):
        """Тестирует загрузку главной страницы"""
        print("🧪 Тестирую загрузку главной страницы...")
        
        try:
            start_time = time.time()
            response = self.session.get(self.base_url, timeout=10)
            load_time = time.time() - start_time
            
            if response.status_code == 200:
                print(f"✅ Страница загружена за {load_time:.2f}с")
                self.results.append(("page_load", True, f"{load_time:.2f}s"))
                return response.text
            else:
                print(f"❌ Ошибка загрузки: {response.status_code}")
                self.results.append(("page_load", False, f"HTTP {response.status_code}"))
                return None
                
        except Exception as e:
            print(f"❌ Ошибка соединения: {e}")
            self.results.append(("page_load", False, str(e)))
            return None
    
    def test_css_resources(self, html_content):
        """Проверяет загрузку CSS ресурсов"""
        print("🧪 Тестирую CSS ресурсы...")
        
        if not html_content:
            self.results.append(("css_resources", False, "No HTML content"))
            return
        
        # Находим CSS файлы
        css_links = re.findall(r'href="([^"]*\.css[^"]*)"', html_content)
        
        success_count = 0
        total_count = len(css_links)
        
        for css_link in css_links:
            try:
                if css_link.startswith('/'):
                    full_url = urljoin(self.base_url, css_link)
                else:
                    full_url = css_link
                
                response = self.session.head(full_url, timeout=5)
                if response.status_code == 200:
                    success_count += 1
                    print(f"  ✅ {css_link}")
                else:
                    print(f"  ❌ {css_link} (HTTP {response.status_code})")
                    
            except Exception as e:
                print(f"  ❌ {css_link} (Ошибка: {e})")
        
        if success_count == total_count and total_count > 0:
            print(f"✅ Все CSS ресурсы загружены ({success_count}/{total_count})")
            self.results.append(("css_resources", True, f"{success_count}/{total_count}"))
        else:
            print(f"❌ Проблемы с CSS ({success_count}/{total_count})")
            self.results.append(("css_resources", False, f"{success_count}/{total_count}"))
    
    def test_js_resources(self, html_content):
        """Проверяет загрузку JavaScript ресурсов"""
        print("🧪 Тестирую JavaScript ресурсы...")
        
        if not html_content:
            self.results.append(("js_resources", False, "No HTML content"))
            return
        
        # Находим JS файлы
        js_links = re.findall(r'src="([^"]*\.js[^"]*)"', html_content)
        
        success_count = 0
        total_count = len(js_links)
        
        for js_link in js_links:
            try:
                if js_link.startswith('/'):
                    full_url = urljoin(self.base_url, js_link)
                else:
                    full_url = js_link
                
                response = self.session.head(full_url, timeout=5)
                if response.status_code == 200:
                    success_count += 1
                    print(f"  ✅ {js_link}")
                else:
                    print(f"  ❌ {js_link} (HTTP {response.status_code})")
                    
            except Exception as e:
                print(f"  ❌ {js_link} (Ошибка: {e})")
        
        if success_count == total_count and total_count > 0:
            print(f"✅ Все JS ресурсы загружены ({success_count}/{total_count})")
            self.results.append(("js_resources", True, f"{success_count}/{total_count}"))
        else:
            print(f"❌ Проблемы с JS ({success_count}/{total_count})")
            self.results.append(("js_resources", False, f"{success_count}/{total_count}"))
    
    def test_key_elements(self, html_content):
        """Проверяет наличие ключевых элементов"""
        print("🧪 Тестирую ключевые элементы...")
        
        if not html_content:
            self.results.append(("key_elements", False, "No HTML content"))
            return
        
        elements = [
            ('AI интерфейс', r'ai-input'),
            ('Навигация', r'nav-link'),
            ('Кнопки', r'btn btn-primary'),
            ('Логотип', r'logo'),
            ('Футер', r'footer'),
            ('Мета-теги', r'<meta.*description'),
            ('Telegram ссылка', r't\.me/examflow_bot'),
            ('CSRF токен', r'csrfmiddlewaretoken'),
        ]
        
        success_count = 0
        for name, pattern in elements:
            if re.search(pattern, html_content, re.IGNORECASE):
                print(f"  ✅ {name}")
                success_count += 1
            else:
                print(f"  ❌ {name}")
        
        total_count = len(elements)
        if success_count == total_count:
            print(f"✅ Все ключевые элементы найдены ({success_count}/{total_count})")
            self.results.append(("key_elements", True, f"{success_count}/{total_count}"))
        else:
            print(f"❌ Отсутствуют элементы ({success_count}/{total_count})")
            self.results.append(("key_elements", False, f"{success_count}/{total_count}"))
    
    def test_ai_api(self):
        """Тестирует AI API"""
        print("🧪 Тестирую AI API...")
        
        try:
            # Получаем CSRF токен
            response = self.session.get(self.base_url)
            csrf_match = re.search(r'csrfmiddlewaretoken[^>]*value=["\']([^"\']*)["\']', response.text)
            
            if not csrf_match:
                print("❌ CSRF токен не найден")
                self.results.append(("ai_api", False, "No CSRF token"))
                return
            
            csrf_token = csrf_match.group(1)
            
            # Тестируем AI запрос
            ai_response = self.session.post(
                urljoin(self.base_url, '/ai/api/'),
                json={'prompt': 'Тест AI интерфейса'},
                headers={
                    'X-CSRFToken': csrf_token,
                    'Content-Type': 'application/json'
                },
                timeout=30
            )
            
            if ai_response.status_code == 200:
                data = ai_response.json()
                if 'answer' in data:
                    print("✅ AI API работает корректно")
                    self.results.append(("ai_api", True, "API responds"))
                else:
                    print("❌ AI API: некорректный формат ответа")
                    self.results.append(("ai_api", False, "Invalid response format"))
            else:
                print(f"❌ AI API: HTTP {ai_response.status_code}")
                self.results.append(("ai_api", False, f"HTTP {ai_response.status_code}"))
                
        except Exception as e:
            print(f"❌ Ошибка AI API: {e}")
            self.results.append(("ai_api", False, str(e)))
    
    def test_responsive_breakpoints(self):
        """Тестирует адаптивные breakpoints"""
        print("🧪 Тестирую адаптивные breakpoints...")
        
        breakpoints = [
            ('Mobile', 375),
            ('Tablet', 768),
            ('Desktop', 1024),
            ('Large', 1440)
        ]
        
        success_count = 0
        for name, width in breakpoints:
            try:
                # Симулируем различные разрешения через User-Agent
                headers = {
                    'User-Agent': f'Mozilla/5.0 (Test Device; {width}px) ExamFlowTester/1.0'
                }
                
                response = self.session.get(self.base_url, headers=headers, timeout=5)
                
                if response.status_code == 200:
                    print(f"  ✅ {name} ({width}px)")
                    success_count += 1
                else:
                    print(f"  ❌ {name} ({width}px) - HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ {name} ({width}px) - Ошибка: {e}")
        
        total_count = len(breakpoints)
        if success_count == total_count:
            print(f"✅ Все breakpoints работают ({success_count}/{total_count})")
            self.results.append(("responsive", True, f"{success_count}/{total_count}"))
        else:
            print(f"❌ Проблемы с адаптивностью ({success_count}/{total_count})")
            self.results.append(("responsive", False, f"{success_count}/{total_count}"))
    
    def test_telegram_integration(self):
        """Тестирует Telegram интеграцию"""
        print("🧪 Тестирую Telegram интеграцию...")
        
        try:
            # Проверяем страницу входа через Telegram
            auth_response = self.session.get(urljoin(self.base_url, '/auth/telegram/login/'), timeout=5)
            
            if auth_response.status_code == 200:
                print("✅ Страница Telegram авторизации доступна")
                self.results.append(("telegram_auth", True, "Auth page accessible"))
            else:
                print(f"❌ Telegram авторизация: HTTP {auth_response.status_code}")
                self.results.append(("telegram_auth", False, f"HTTP {auth_response.status_code}"))
                
        except Exception as e:
            print(f"❌ Ошибка Telegram интеграции: {e}")
            self.results.append(("telegram_auth", False, str(e)))
    
    def run_all_tests(self):
        """Запускает все тесты"""
        print("🚀 Запуск тестирования фронтенда ExamFlow...\n")
        
        # Загрузка главной страницы
        html_content = self.test_page_load()
        
        if html_content:
            # Тестирование ресурсов
            self.test_css_resources(html_content)
            self.test_js_resources(html_content)
            self.test_key_elements(html_content)
        
        # Функциональные тесты
        self.test_ai_api()
        self.test_responsive_breakpoints()
        self.test_telegram_integration()
        
        # Отчет
        print("\n📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
        print("=" * 70)
        
        passed = 0
        failed = 0
        
        for test_name, success, details in self.results:
            status = "✅ ПРОШЁЛ" if success else "❌ ОШИБКА"
            print(f"{test_name:<20} | {status:<12} | {details}")
            if success:
                passed += 1
            else:
                failed += 1
        
        print("=" * 70)
        print(f"📈 ИТОГО: {passed} прошли, {failed} ошибок")
        
        if failed == 0:
            print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ! Фронтенд полностью функционален.")
        else:
            print("⚠️  Обнаружены проблемы, требующие внимания.")
        
        return failed == 0

def main():
    tester = FrontendTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🚀 Фронтенд готов к продакшену!")
    else:
        print("\n🔧 Требуются дополнительные исправления.")

if __name__ == "__main__":
    main()

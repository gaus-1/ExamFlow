#!/usr/bin/env python3
"""
Скрипт для проверки безопасности ExamFlow
Проверяет заголовки, SSL, зависимости и настройки
"""

import requests
import subprocess
import sys
from pathlib import Path

# Цвета для вывода
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_status(message, status="INFO"):
    """Выводит сообщение с цветом в зависимости от статуса"""
    if status == "SUCCESS":
        print(f"{Colors.GREEN}✅ {message}{Colors.ENDC}")
    elif status == "ERROR":
        print(f"{Colors.RED}❌ {message}{Colors.ENDC}")
    elif status == "WARNING":
        print(f"{Colors.YELLOW}⚠️  {message}{Colors.ENDC}")
    elif status == "INFO":
        print(f"{Colors.BLUE}ℹ️  {message}{Colors.ENDC}")
    else:
        print(f"{message}")

def check_ssl_certificate(url):
    """Проверяет SSL сертификат"""
    try:
        response = requests.get(url, timeout=10, verify=True)
        if response.status_code == 200:
            print_status(f"SSL сертификат валиден для {url}", "SUCCESS")
            return True
        else:
            print_status(f"SSL работает, но статус {response.status_code}", "WARNING")
            return True
    except requests.exceptions.SSLError:
        print_status(f"SSL ошибка для {url}", "ERROR")
        return False
    except Exception as e:
        print_status(f"Ошибка проверки SSL: {e}", "ERROR")
        return False

def check_security_headers(url):
    """Проверяет заголовки безопасности"""
    try:
        response = requests.get(url, timeout=10)
        headers = response.headers
        
        security_headers = {
            'Strict-Transport-Security': 'HSTS',
            'Content-Security-Policy': 'CSP',
            'X-Content-Type-Options': 'X-Content-Type-Options',
            'X-Frame-Options': 'X-Frame-Options',
            'X-XSS-Protection': 'X-XSS-Protection',
            'Referrer-Policy': 'Referrer-Policy',
            'Permissions-Policy': 'Permissions-Policy',
            'Cross-Origin-Opener-Policy': 'COOP',
            'Cross-Origin-Embedder-Policy': 'COEP'
        }
        
        print_status("Проверка заголовков безопасности:", "INFO")
        for header, description in security_headers.items():
            if header in headers:
                print_status(f"  {description}: {headers[header]}", "SUCCESS")
            else:
                print_status(f"  {description}: отсутствует", "WARNING")
        
        return True
    except Exception as e:
        print_status(f"Ошибка проверки заголовков: {e}", "ERROR")
        return False

def check_dependencies():
    """Проверяет зависимости на уязвимости"""
    try:
        print_status("Проверка зависимостей на уязвимости:", "INFO")
        
        # Проверяем наличие safety
        try:
            subprocess.run([sys.executable, "-m", "safety", "check"], 
                         capture_output=True, text=True, check=True)
            print_status("  Safety: проверка завершена", "SUCCESS")
        except subprocess.CalledProcessError:
            print_status("  Safety: найдены уязвимости", "WARNING")
        except FileNotFoundError:
            print_status("  Safety: не установлен (pip install safety)", "WARNING")
        
        # Проверяем requirements.txt
        requirements_file = Path("requirements.txt")
        if requirements_file.exists():
            print_status("  requirements.txt: найден", "SUCCESS")
        else:
            print_status("  requirements.txt: не найден", "ERROR")
        
        return True
    except Exception as e:
        print_status(f"Ошибка проверки зависимостей: {e}", "ERROR")
        return False

def check_django_settings():
    """Проверяет настройки Django на безопасность"""
    try:
        print_status("Проверка настроек Django:", "INFO")
        
        # Проверяем наличие middleware безопасности
        middleware_file = Path("examflow_project/middleware.py")
        if middleware_file.exists():
            print_status("  SecurityHeadersMiddleware: найден", "SUCCESS")
        else:
            print_status("  SecurityHeadersMiddleware: не найден", "ERROR")
        
        # Проверяем настройки в settings.py
        settings_file = Path("examflow_project/settings.py")
        if settings_file.exists():
            content = settings_file.read_text()
            
            security_settings = [
                'PERMISSIONS_POLICY',
                'SECURE_REFERRER_POLICY',
                'SECURE_CROSS_ORIGIN_OPENER_POLICY',
                'SECURE_CROSS_ORIGIN_EMBEDDER_POLICY',
                'SECURE_CONTENT_TYPE_NOSNIFF',
                'SECURE_BROWSER_XSS_FILTER',
                'X_FRAME_OPTIONS'
            ]
            
            for setting in security_settings:
                if setting in content:
                    print_status(f"  {setting}: настроен", "SUCCESS")
                else:
                    print_status(f"  {setting}: не настроен", "WARNING")
        
        return True
    except Exception as e:
        print_status(f"Ошибка проверки настроек Django: {e}", "ERROR")
        return False

def check_telegram_bot():
    """Проверяет безопасность Telegram бота"""
    try:
        print_status("Проверка безопасности Telegram бота:", "INFO")
        
        bot_files = [
            "telegram_bot/bot_main.py",
            "telegram_bot/views.py",
            "telegram_bot/bot_handlers.py"
        ]
        
        for file_path in bot_files:
            file = Path(file_path)
            if file.exists():
                content = file.read_text()
                
                # Проверяем наличие проверок безопасности
                security_checks = [
                    'verify_webhook',
                    'is_allowed_ip',
                    'rate_limit',
                    'input_validation'
                ]
                
                for check in security_checks:
                    if check in content:
                        print_status(f"  {file_path}: {check} найден", "SUCCESS")
                    else:
                        print_status(f"  {file_path}: {check} не найден", "WARNING")
            else:
                print_status(f"  {file_path}: файл не найден", "ERROR")
        
        return True
    except Exception as e:
        print_status(f"Ошибка проверки Telegram бота: {e}", "ERROR")
        return False

def main():
    """Основная функция проверки"""
    print(f"{Colors.BOLD}🔒 ПРОВЕРКА БЕЗОПАСНОСТИ EXAMFLOW{Colors.ENDC}")
    print("=" * 50)
    
    # URL для проверки
    urls = [
        "https://examflow.ru",
        "https://www.examflow.ru"
    ]
    
    results = {
        'ssl': [],
        'headers': [],
        'dependencies': False,
        'django': False,
        'telegram_bot': False
    }
    
    # Проверяем SSL и заголовки для каждого URL
    for url in urls:
        print(f"\n{Colors.BOLD}Проверка {url}:{Colors.ENDC}")
        results['ssl'].append(check_ssl_certificate(url))
        results['headers'].append(check_security_headers(url))
    
    # Проверяем зависимости и настройки
    print(f"\n{Colors.BOLD}Проверка зависимостей и настроек:{Colors.ENDC}")
    results['dependencies'] = check_dependencies()
    results['django'] = check_django_settings()
    results['telegram_bot'] = check_telegram_bot()
    
    # Итоговая оценка
    print(f"\n{Colors.BOLD}ИТОГОВАЯ ОЦЕНКА БЕЗОПАСНОСТИ:{Colors.ENDC}")
    print("=" * 50)
    
    total_checks = len(results['ssl']) + len(results['headers']) + 3
    passed_checks = sum(results['ssl']) + sum(results['headers']) + sum([
        results['dependencies'], results['django'], results['telegram_bot']
    ])
    
    security_score = (passed_checks / total_checks) * 100
    
    if security_score >= 90:
        print_status(f"Общий балл безопасности: {security_score:.1f}% - ОТЛИЧНО", "SUCCESS")
    elif security_score >= 70:
        print_status(f"Общий балл безопасности: {security_score:.1f}% - ХОРОШО", "WARNING")
    else:
        print_status(f"Общий балл безопасности: {security_score:.1f}% - ТРЕБУЕТ ВНИМАНИЯ", "ERROR")
    
    print(f"\n{Colors.BOLD}Рекомендации:{Colors.ENDC}")
    if not all(results['ssl']):
        print_status("  Исправить SSL сертификаты", "ERROR")
    if not all(results['headers']):
        print_status("  Добавить недостающие заголовки безопасности", "WARNING")
    if not results['dependencies']:
        print_status("  Проверить зависимости на уязвимости", "WARNING")
    if not results['django']:
        print_status("  Настроить безопасность Django", "WARNING")
    if not results['telegram_bot']:
        print_status("  Улучшить безопасность Telegram бота", "WARNING")

if __name__ == "__main__":
    main()

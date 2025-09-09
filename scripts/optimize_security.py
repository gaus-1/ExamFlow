#!/usr/bin/env python3
"""
Скрипт для автоматического внедрения мер безопасности
"""

import subprocess
import sys
from pathlib import Path

def install_security_tools():
    """Устанавливает инструменты безопасности"""
    print("🔒 Устанавливаем инструменты безопасности...")
    
    tools = [
        'safety',
        'bandit',
        'pip-audit',
        'django-csp',
        'django-ratelimit'
    ]
    
    for tool in tools:
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', tool], check=True)
            print(f"✅ {tool} установлен")
        except subprocess.CalledProcessError:
            print(f"❌ Ошибка установки {tool}")

def update_dependencies():
    """Обновляет зависимости до последних версий"""
    print("📦 Обновляем зависимости...")
    
    try:
        # Проверяем уязвимости
        subprocess.run([sys.executable, '-m', 'safety', 'check'], check=True)
        print("✅ Проверка безопасности пройдена")
    except subprocess.CalledProcessError:
        print("⚠️ Найдены уязвимости, обновляем...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', '-r', 'requirements.txt'])

def enable_csp():
    """Включает Content Security Policy"""
    print("🛡️ Включаем CSP...")
    
    settings_file = Path('examflow_project/settings.py')
    if not settings_file.exists():
        print("❌ Файл settings.py не найден")
        return
    
    # Читаем текущие настройки
    with open(settings_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Добавляем CSP настройки если их нет
    csp_config = '''
# Content Security Policy
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "https://cdnjs.cloudflare.com")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://fonts.googleapis.com")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com")
CSP_CONNECT_SRC = ("'self'", "https://generativelanguage.googleapis.com")
CSP_FRAME_ANCESTORS = ("'none'",)
CSP_BASE_URI = ("'self'",)
CSP_OBJECT_SRC = ("'none'",)
'''
    
    if 'CSP_DEFAULT_SRC' not in content:
        # Добавляем CSP настройки перед INSTALLED_APPS
        content = content.replace('INSTALLED_APPS = [', csp_config + '\nINSTALLED_APPS = [')
        
        # Включаем CSP middleware
        if "'csp.middleware.CSPMiddleware'" not in content:
            content = content.replace(
                "# 'csp.middleware.CSPMiddleware',  # CSP middleware - ВРЕМЕННО ОТКЛЮЧЕН",
                "'csp.middleware.CSPMiddleware',  # CSP middleware"
            )
        
        with open(settings_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ CSP включен")
    else:
        print("✅ CSP уже настроен")

def add_security_headers():
    """Добавляет заголовки безопасности"""
    print("🔐 Добавляем заголовки безопасности...")
    
    middleware_file = Path('examflow_project/middleware.py')
    if not middleware_file.exists():
        # Создаем middleware файл
        middleware_content = '''"""
Middleware для заголовков безопасности
"""

class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Заголовки безопасности
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        return response
'''
        with open(middleware_file, 'w', encoding='utf-8') as f:
            f.write(middleware_content)
        print("✅ Middleware безопасности создан")
    else:
        print("✅ Middleware безопасности уже существует")

def add_input_validation():
    """Добавляет валидацию входных данных"""
    print("🔍 Добавляем валидацию входных данных...")
    
    validators_file = Path('core/validators.py')
    if not validators_file.exists():
        validators_content = '''"""
Валидаторы для входных данных
"""

import re
from typing import Any, Dict
from django.core.exceptions import ValidationError

def validate_prompt(prompt: str) -> str:
    """
    Валидирует промпт для AI API
    
    Args:
        prompt: Текст промпта
        
    Returns:
        Очищенный промпт
        
    Raises:
        ValidationError: Если промпт невалиден
    """
    if not prompt or not prompt.strip():
        raise ValidationError("Промпт не может быть пустым")
    
    if len(prompt) > 2000:
        raise ValidationError("Промпт слишком длинный (максимум 2000 символов)")
    
    # Проверка на XSS
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\\w+\\s*=',
        r'<iframe[^>]*>',
        r'<object[^>]*>',
        r'<embed[^>]*>'
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, prompt, re.IGNORECASE):
            raise ValidationError("Обнаружена попытка XSS атаки")
    
    # Базовая санитизация
    prompt = prompt.replace('<', '&lt;').replace('>', '&gt;')
    prompt = prompt.replace('"', '&quot;').replace("'", '&#x27;')
    
    return prompt.strip()

def validate_user_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Валидирует пользовательский ввод
    
    Args:
        data: Словарь с данными
        
    Returns:
        Валидированные данные
        
    Raises:
        ValidationError: Если данные невалидны
    """
    if not isinstance(data, dict):
        raise ValidationError("Данные должны быть словарем")
    
    # Валидация промпта
    if 'prompt' in data:
        data['prompt'] = validate_prompt(data['prompt'])
    
    # Валидация user_id
    if 'user_id' in data:
        user_id = data['user_id']
        if not isinstance(user_id, int) or user_id < 1:
            raise ValidationError("Невалидный user_id")
    
    return data
'''
        with open(validators_file, 'w', encoding='utf-8') as f:
            f.write(validators_content)
        print("✅ Валидаторы созданы")
    else:
        print("✅ Валидаторы уже существуют")

def run_security_checks():
    """Запускает проверки безопасности"""
    print("🔍 Запускаем проверки безопасности...")
    
    try:
        # Bandit проверка
        subprocess.run([sys.executable, '-m', 'bandit', '-r', '.', '-f', 'json', '-o', 'bandit-report.json'], check=True)
        print("✅ Bandit проверка пройдена")
    except subprocess.CalledProcessError:
        print("⚠️ Bandit нашел проблемы, проверьте bandit-report.json")
    
    try:
        # Safety проверка
        subprocess.run([sys.executable, '-m', 'safety', 'check'], check=True)
        print("✅ Safety проверка пройдена")
    except subprocess.CalledProcessError:
        print("⚠️ Safety нашел уязвимости в зависимостях")

def main():
    """Основная функция"""
    print("🚀 Начинаем внедрение мер безопасности...")
    
    # Устанавливаем инструменты
    install_security_tools()
    
    # Обновляем зависимости
    update_dependencies()
    
    # Включаем CSP
    enable_csp()
    
    # Добавляем заголовки безопасности
    add_security_headers()
    
    # Добавляем валидацию
    add_input_validation()
    
    # Запускаем проверки
    run_security_checks()
    
    print("🎉 Внедрение мер безопасности завершено!")
    print("📋 Следующие шаги:")
    print("1. Проверьте bandit-report.json на наличие проблем")
    print("2. Обновите requirements.txt с новыми версиями")
    print("3. Протестируйте приложение")
    print("4. Запустите миграции: python manage.py migrate")

if __name__ == "__main__":
    main()

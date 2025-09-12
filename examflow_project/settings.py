"""
Настройки Django для ExamFlow 2.0.

Этот файл использует модульную структуру настроек для лучшей организации.
Все основные настройки вынесены в отдельные компоненты в папке settings_components/.
"""

import os
import sys
import dj_database_url
from dotenv import load_dotenv

load_dotenv()

# Импорт всех компонентов настроек
from .settings_components import *

# Дополнительные настройки, специфичные для разработки
if DEBUG:
    # Настройки для разработки
    INSTALLED_APPS += [
        'django_extensions',
    ]
    
    # Отключение CSP в режиме разработки для удобства
    CSP_DEFAULT_SRC = ("'self'", "'unsafe-inline'", "'unsafe-eval'")
    CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "'unsafe-eval'")
    
    # Включение отладочной панели
    if os.getenv('ENABLE_DEBUG_TOOLBAR', 'False').lower() == 'true':
        INSTALLED_APPS += ['debug_toolbar']
        MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE
        INTERNAL_IPS = ['127.0.0.1', 'localhost']

# Настройки для продакшена
if not DEBUG:
    # Безопасность в продакшене
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Настройки сессий для продакшена
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # Настройки статических файлов для продакшена
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    
    # Настройки базы данных для продакшена (если используется DATABASE_URL)
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        db_config = dj_database_url.parse(database_url)
        # Добавляем SSL настройки для Render с более мягкими параметрами
        if 'OPTIONS' not in db_config:
            db_config['OPTIONS'] = {}
        db_config['OPTIONS']['sslmode'] = 'prefer'  # type: ignore
        db_config['OPTIONS']['connect_timeout'] = 30  # type: ignore
        db_config['OPTIONS']['keepalives_idle'] = 600  # type: ignore
        db_config['OPTIONS']['keepalives_interval'] = 30  # type: ignore
        db_config['OPTIONS']['keepalives_count'] = 3  # type: ignore
        DATABASES['default'] = dict(db_config)  # type: ignore
    
    # Временно отключаем drf-spectacular в продакшене для исправления ошибки
    try:
        import drf_spectacular
        # Если модуль доступен, оставляем настройки как есть
    except ImportError:
        # Если модуль недоступен, убираем из INSTALLED_APPS
        if 'drf_spectacular' in INSTALLED_APPS:
            INSTALLED_APPS.remove('drf_spectacular')
        # Убираем настройки REST_FRAMEWORK и SPECTACULAR
        REST_FRAMEWORK = {
            'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
            'PAGE_SIZE': 20,
        }
        SPECTACULAR_SETTINGS = {}

# API ключи и внешние сервисы
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_WEBHOOK_SECRET = os.getenv('TELEGRAM_WEBHOOK_SECRET', '')

# Настройки RAG системы
RAG_CONFIG = {
    'MAX_CONTEXT_LENGTH': 4000,
    'MAX_SOURCES': 5,
    'CACHE_TTL': 600,  # 10 минут
    'SIMILARITY_THRESHOLD': 0.7,
}

# Настройки FIPI
FIPI_CONFIG = {
    'BASE_URL': 'https://fipi.ru',
    'UPDATE_INTERVAL': 3600,  # 1 час
    'MAX_RETRIES': 3,
}

# Настройки Telegram бота
TELEGRAM_BOT_CONFIG = {
    'WEBHOOK_URL': os.getenv('TELEGRAM_WEBHOOK_URL', ''),
    'POLLING_INTERVAL': 1,
    'MAX_CONNECTIONS': 100,
    'TIMEOUT': 30,
}

# Настройки кэширования
CACHE_TTL = {
    'RAG_RESULTS': 600,  # 10 минут
    'FIPI_DATA': 3600,   # 1 час
    'USER_PROFILE': 300, # 5 минут
}

# Настройки мониторинга
MONITORING_CONFIG = {
    'HEALTH_CHECK_INTERVAL': 60,  # 1 минута
    'UPTIME_CHECK_INTERVAL': 300,  # 5 минут
    'ERROR_REPORTING': True,
}

# Настройки безопасности
SECURITY_CONFIG = {
    'RATE_LIMIT_PER_MINUTE': 60,
    'MAX_LOGIN_ATTEMPTS': 5,
    'LOCKOUT_DURATION': 900,  # 15 минут
    'PASSWORD_MIN_LENGTH': 8,
}

# Настройки персонализации
PERSONALIZATION_CONFIG = {
    'ENABLE_LEARNING_ANALYTICS': True,
    'ENABLE_RECOMMENDATIONS': True,
    'ENABLE_PROGRESS_TRACKING': True,
    'MAX_LEARNING_HISTORY': 1000,
}

# Настройки уведомлений
NOTIFICATION_CONFIG = {
    'EMAIL_ENABLED': True,
    'TELEGRAM_ENABLED': True,
    'PUSH_ENABLED': False,
    'DIGEST_FREQUENCY': 'weekly',
}

# Настройки для тестирования
if 'test' in sys.argv:
    # Упрощенные настройки для тестов
    PASSWORD_HASHERS = [
        'django.contrib.auth.hashers.MD5PasswordHasher',
    ]
    
    # Использование SQLite для тестов
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
    
    # Отключение кэширования в тестах
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }

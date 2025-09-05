"""
Настройки Django для продакшена ExamFlow 2.0
"""

import os
import dj_database_url
from .settings import *

# Принудительно отключаем DEBUG в продакшене
DEBUG = False

# Генерируем новый SECRET_KEY для продакшена
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError('SECURITY: SECRET_KEY must be set via environment in production')

# Настройки безопасности для продакшена
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_SECONDS = 31536000  # 1 год
SECURE_REDIRECT_EXEMPT = []
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'

# Настройки статических файлов для продакшена
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Настройки базы данных для продакшена
DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Настройки логирования для продакшена
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Настройки кеширования для продакшена
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Настройки сессий для продакшена
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Настройки CORS для продакшена
CORS_ALLOWED_ORIGINS = [
    'https://examflow.ru',
    'https://www.examflow.ru',
    'https://examflow.onrender.com',
]

# Настройки Content Security Policy
CSP_DEFAULT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://fonts.googleapis.com")
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "https://www.googletagmanager.com")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com")
CSP_CONNECT_SRC = ("'self'", "https://generativelanguage.googleapis.com")

# Настройки rate limiting для продакшена
RATELIMIT_USE_CACHE = 'default'
RATELIMIT_ENABLE = True

# Настройки для Render
if os.getenv('RENDER'):
    # Автоматически добавляем хост Render
    RENDER_HOST = os.getenv('RENDER_EXTERNAL_HOSTNAME')
    if RENDER_HOST:
        ALLOWED_HOSTS.append(RENDER_HOST)
    
    # Настройки для статических файлов на Render
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

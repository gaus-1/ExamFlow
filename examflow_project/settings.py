import os
import dj_database_url
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# для корректной работы путей
import sys
sys.path.append(str(BASE_DIR))

# Настройки разработки - не подходят для продакшена
# См. https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# ПРЕДУПРЕЖДЕНИЕ БЕЗОПАСНОСТИ: держите секретный ключ в секрете!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-b=8q90=se^7twm97htmj$v2n-(b@8!0(%h48n=tnb=t^%ja!ta')
# Запрет небезопасного SECRET_KEY в продакшене
if not os.getenv('DEBUG', 'False').lower() == 'true':
    if SECRET_KEY.startswith('django-insecure'):
        raise RuntimeError('SECURITY: SECRET_KEY must be set via environment in production')

# ПРЕДУПРЕЖДЕНИЕ БЕЗОПАСНОСТИ: не запускайте с debug=True в продакшене!
# В продакшене принудительно выключаем DEBUG
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'  # По умолчанию True для разработки

ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', 'examflow.ru,www.examflow.ru,localhost,127.0.0.1,testserver,examflow.onrender.com').split(',') if h.strip()]
# Добавим хост Render автоматически, если предоставлен платформой
RENDER_HOST = os.getenv('RENDER_EXTERNAL_HOSTNAME')
if RENDER_HOST and RENDER_HOST not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RENDER_HOST)

# Определение приложений

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Основные модули (legacy)
    'core',
    # 'bot',  # УБРАНО - конфликт с telegram_bot
    
    # Новые модульные приложения
    'authentication',      # Аутентификация и регистрация
    'learning',           # Обучение и задания  
    'telegram_bot',       # Telegram бот функционал
    'analytics',          # Аналитика и статистика
    'themes',             # Управление дизайнами и темами
    'ai.apps.AiConfig',    # ИИ-ассистент и голосовой помощник
    
    # Внешние библиотеки
    'corsheaders',
    'django_redis',
    'csp',  # Content Security Policy (django-csp)
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Включен для статических файлов на Render
    'corsheaders.middleware.CorsMiddleware',  # CORS middleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_ratelimit.middleware.RatelimitMiddleware',
    # 'csp.middleware.CSPMiddleware',  # CSP middleware - ВРЕМЕННО ОТКЛЮЧЕН
    # 🔒 Дополнительные middleware для безопасности
    'examflow_project.middleware.SecurityHeadersMiddleware',  # Кастомные заголовки безопасности
    # FREEMIUM middleware
    'core.freemium.middleware.FreemiumMiddleware',
]

ROOT_URLCONF = 'examflow_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'examflow_project.wsgi.application'

# URL-ы аутентификации
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'

# Keepalive настройки
WEBSITE_URL = os.getenv('WEBSITE_URL', 'https://examflow.ru')
KEEPALIVE_INTERVAL = int(os.getenv('KEEPALIVE_INTERVAL', '300'))  # 5 минут

# Кастомные backends для аутентификации
AUTHENTICATION_BACKENDS = [
    'authentication.backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Database
# Настройки базы данных
DATABASE_URL = os.getenv('DATABASE_URL')
RUNNING_TESTS = os.getenv('RUNNING_TESTS') == '1'
USE_SQLITE = os.getenv('USE_SQLITE', 'False').lower() == 'true'

def _sqlite_db():
    return {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }

# В отладке по умолчанию используем SQLite, если явно не указано иное
if USE_SQLITE or RUNNING_TESTS:
    DATABASES = _sqlite_db()
else:
    if DATABASE_URL:
        try:
            # Psycopg v3 (psycopg) дружит с django через стандартную строку ENGINE ниже
DATABASES = {
                'default': dj_database_url.parse(
                    DATABASE_URL,
                    conn_max_age=600,
                    ssl_require=not DEBUG
                )
            }
            # Явно указываем backend для совместимости
            DATABASES['default']['ENGINE'] = 'django.db.backends.postgresql'

            # Форсируем IPv4 при необходимости: некоторые окружения не имеют IPv6-маршрутизации,
            # а Supabase/PG-хост может сначала резолвиться в AAAA.
            # Если DB_FORCE_IPV4=1 (по умолчанию в продакшене), подставим hostaddr IPv4.
            force_ipv4 = os.getenv('DB_FORCE_IPV4', '1' if not DEBUG else '0') == '1'
            if force_ipv4:
                try:
                    import socket
                    host = DATABASES['default'].get('HOST') or ''
                    port = int(DATABASES['default'].get('PORT') or 5432)
                    if not host:
                        # Попробуем достать hostname из DATABASE_URL
                        from urllib.parse import urlparse
                        parsed = urlparse(DATABASE_URL)
                        host = parsed.hostname or ''

                    if host:
                        infos = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)
                        if infos:
                            ipv4_addr = infos[0][4][0]
                            opts = DATABASES['default'].setdefault('OPTIONS', {})
                            opts['hostaddr'] = ipv4_addr
                            # Гарантируем TLS
                            opts.setdefault('sslmode', 'require')
                            # Прямо подключимся по IPv4, чтобы libpq не выбирал AAAA
                            DATABASES['default']['HOST'] = ipv4_addr
                except Exception:
                    # Тихо продолжаем, если не удалось резолвить IPv4
                    pass
        except Exception:
            DATABASES = _sqlite_db()
    else:
        # Fallback на отдельные переменные PostgreSQL
        db_name = os.getenv('DB_NAME')
        db_user = os.getenv('DB_USER')
        db_password = os.getenv('DB_PASSWORD')
        db_host = os.getenv('DB_HOST')
        db_port = os.getenv('DB_PORT')
        
        if all([db_name, db_user, db_password, db_host]):
            DATABASES = {
                'default': {
                    'ENGINE': 'django.db.backends.postgresql',
                    'NAME': db_name,
                    'USER': db_user,
                    'PASSWORD': db_password,
                    'HOST': db_host,
                    'PORT': db_port or '5432',
                }
            }
        else:
            DATABASES = _sqlite_db()

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'ru-ru'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Настройки статических файлов для Render
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# На Render используем whitenoise для статических файлов
if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.StaticFilesStorage'
    # Настройки whitenoise для продакшена
    WHITENOISE_USE_FINDERS = True
    WHITENOISE_AUTOREFRESH = True
    WHITENOISE_INDEX_FILE = True
    WHITENOISE_ROOT = os.path.join(BASE_DIR, 'staticfiles')
else:
    # Отключаем хеширование файлов для разработки
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Media (для вложений задач)
# Cache
if os.getenv('USE_REDIS_CACHE', '0') == '1':
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'OPTIONS': {
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 50,
                    'retry_on_timeout': True,
                }
            }
        }
    }
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_CACHE_ALIAS = 'default'
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'examflow-local'
        }
    }

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS settings
if DEBUG:
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
else:
    CORS_ALLOWED_ORIGINS = [f"https://{h}" for h in ALLOWED_HOSTS if h and h not in ("localhost","127.0.0.1")]

# Telegram Bot settings
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
BILLING_SECRET = os.getenv('BILLING_SECRET', 'change-me')

# Настройки системы мониторинга
MONITORING_EMAIL_RECIPIENTS = [
    email.strip() for email in os.getenv('MONITORING_EMAIL_RECIPIENTS', '').split(',')
    if email.strip()
]
MONITORING_WEBHOOK_URL = os.getenv('MONITORING_WEBHOOK_URL')

# Настройки движка сбора данных
INGESTION_ENGINE_MAX_WORKERS = int(os.getenv('INGESTION_ENGINE_MAX_WORKERS', '5'))
INGESTION_ENGINE_CHECK_INTERVAL = int(os.getenv('INGESTION_ENGINE_CHECK_INTERVAL', '300'))  # 5 минут

# Настройки Change Data Capture
CHANGE_WEBHOOK_URL = os.getenv('CHANGE_WEBHOOK_URL')
CHANGE_NOTIFICATION_EMAILS = [
    email.strip() for email in os.getenv('CHANGE_NOTIFICATION_EMAILS', '').split(',')
    if email.strip()
]

# Redis settings for Celery
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Celery settings
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Security settings for production
if not DEBUG:
    # HTTPS settings
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Keep-alive настройки и базовый URL сайта
# Если явно не задан SITE_URL, а Render предоставляет хост, используем его
_ENV_SITE_URL = os.getenv('SITE_URL')
if _ENV_SITE_URL:
    SITE_URL = _ENV_SITE_URL
elif RENDER_HOST:
    SITE_URL = f"https://{RENDER_HOST}"
else:
    SITE_URL = 'https://examflow.ru'
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID', None)  # Telegram chat ID админа для уведомлений

# Автозапуск парсинга при первом запросе (по умолчанию включен)
AUTO_STARTUP_ENABLED = os.getenv('AUTO_STARTUP_ENABLED', 'true').lower() in ['true', '1', 'yes']

# Логирование — базовая конфигурация (подробная финальная версия ниже переопределяет её)
# Оставлено намеренно пустым для избежания дублирования

if not DEBUG:
    # HSTS settings
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Cookie settings
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # Content Security Policy
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'
    # Доп. заголовки
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
    CSRF_TRUSTED_ORIGINS = [
        'https://examflow.ru',
        'https://www.examflow.ru',
    ]
else:
    # При разработке тоже добавим доверенные домены, чтобы тестировать прокси/туннели
    CSRF_TRUSTED_ORIGINS = list(set([
        'http://localhost:8000',
        'http://127.0.0.1:8000',
        'https://examflow.ru',
        'https://www.examflow.ru',
        'https://*.onrender.com',
    ]))

# Обработка ошибок
handler404 = 'examflow_project.views.handler404'

# CSP — ВРЕМЕННО ОТКЛЮЧЕН для тестирования стилей
# if DEBUG:
#     CONTENT_SECURITY_POLICY = {
#         'default-src': ("'self'",),
#         'style-src': ("'self'", "'unsafe-inline'", "https://cdnjs.cloudflare.com", "https://cdn.jsdelivr.net"),
#         'style-src-elem': ("'self'", "'unsafe-inline'", "https://cdnjs.cloudflare.com", "https://cdn.jsdelivr.net"),
#         'script-src': ("'self'", "'unsafe-inline'", "'unsafe-eval'", "https://cdnjs.cloudflare.com", "https://cdn.jsdelivr.net"),
#         'script-src-elem': ("'self'", "'unsafe-inline'", "'unsafe-eval'", "https://cdnjs.cloudflare.com", "https://cdn.jsdelivr.net"),
#         'img-src': ("'self'", "data:", "https:", "https://api.qrserver.com"),
#         'font-src': ("'self'", "https://cdnjs.cloudflare.com", "https://cdn.jsdelivr.net"),
#         'connect-src': ("'self'", "https://generativelanguage.googleapis.com"),
#         'frame-ancestors': ("'none'",),
#     }
# else:
#     # В продакшене тоже разрешаем unsafe-inline для совместимости
#     CONTENT_SECURITY_POLICY = {
#         'default-src': ("'self'",),
#         'style-src': ("'self'", "'unsafe-inline'", "https://cdnjs.cloudflare.com", "https://cdn.jsdelivr.net"),
#         'style-src-elem': ("'self'", "'unsafe-inline'", "https://cdnjs.cloudflare.com", "https://cdn.jsdelivr.net"),
#         'script-src': ("'self'", "'unsafe-inline'", "https://cdnjs.cloudflare.com", "https://cdn.jsdelivr.net"),
#         'script-src-elem': ("'self'", "'unsafe-inline'", "https://cdnjs.cloudflare.com", "https://cdn.jsdelivr.net"),
#         'img-src': ("'self'", "data:", "https:", "https://api.qrserver.com"),
#         'font-src': ("'self'", "https://cdnjs.cloudflare.com", "https://cdn.jsdelivr.net"),
#         'connect-src': ("'self'", "https://generativelanguage.googleapis.com"),
#         'frame-ancestors': ("'none'",),
#     }

# Дополнительные заголовки безопасности
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# 🔒 ДОПОЛНИТЕЛЬНЫЕ ЗАГОЛОВКИ БЕЗОПАСНОСТИ
# Permissions-Policy - ограничение доступа к API браузера
PERMISSIONS_POLICY = {
    'accelerometer': [],
    'ambient-light-sensor': [],
    'autoplay': [],
    'battery': [],
    'camera': [],
    'cross-origin-isolated': [],
    'display-capture': [],
    'document-domain': [],
    'encrypted-media': [],
    'execution-while-not-rendered': [],
    'execution-while-out-of-viewport': [],
    'fullscreen': [],
    'geolocation': [],
    'gyroscope': [],
    'keyboard-map': [],
    'magnetometer': [],
    'microphone': [],
    'midi': [],
    'navigation-override': [],
    'payment': [],
    'picture-in-picture': [],
    'publickey-credentials-get': [],
    'screen-wake-lock': [],
    'sync-xhr': [],
    'usb': [],
    'web-share': [],
    'xr-spatial-tracking': [],
}

# Улучшенный Referrer-Policy
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Дополнительные заголовки безопасности
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'
SECURE_CROSS_ORIGIN_EMBEDDER_POLICY = 'credentialless'  # Изменено для совместимости

# Защита от MIME-sniffing
SECURE_CONTENT_TYPE_NOSNIFF = True

# Защита от XSS
SECURE_BROWSER_XSS_FILTER = True

# Защита от clickjacking
X_FRAME_OPTIONS = 'DENY'

# Дополнительные настройки сессий
SESSION_COOKIE_AGE = 3600  # 1 час
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = False

# Настройки паролей
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
]

# MFA настройки (готовность к внедрению)
MFA_ENABLED = os.getenv('MFA_ENABLED', 'False').lower() == 'true'
MFA_REQUIRED_FOR_ADMIN = True
MFA_REQUIRED_FOR_STAFF = True

# Rate limiting настройки
RATELIMIT_USE_CACHE = 'default'
RATELIMIT_ENABLE = True

# Безопасность API
API_RATE_LIMIT = '100/hour'
API_RATE_LIMIT_BLOCK = '10/minute'

# CORS настройки
CORS_ALLOWED_ORIGINS = [
    "https://examflow.ru",
    "https://www.examflow.ru",
]
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https:\/\/[a-zA-Z0-9-]+\.onrender\.com$",
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = [
    'GET',
    'POST',
    'PUT',
    'PATCH',
    'DELETE',
    'OPTIONS'
]
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Безопасные cookies
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

# HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = 31536000  # 1 год
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'security': {
            'format': '[SECURITY] {levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'security.log'),
            'formatter': 'security',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['security_file', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'bot': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'core': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'telegram_bot': {
            'handlers': ['console', 'file', 'security_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Create logs directory if it doesn't exist
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)

# 🔒 ЛОГИРОВАНИЕ БЕЗОПАСНОСТИ
# Создаем отдельную папку для логов безопасности
os.makedirs(os.path.join(BASE_DIR, 'logs', 'security'), exist_ok=True)

# Расширенное логирование безопасности
SECURITY_LOGGING = {
    'failed_login': True,
    'successful_login': True,
    'password_change': True,
    'user_creation': True,
    'admin_action': True,
    'suspicious_activity': True,
}

# Настройки для мониторинга безопасности
SECURITY_MONITORING = {
    'failed_login_threshold': 5,  # Количество неудачных попыток входа
    'suspicious_ip_threshold': 10,  # Количество запросов с одного IP
    'admin_action_logging': True,  # Логирование действий администратора
}

# ==========================================
# НАСТРОЙКИ GOOGLE GEMINI AI
# ==========================================

# 🤖 GEMINI AI - НАСТРОЙКИ
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

# OAuth настройки
GOOGLE_OAUTH_CLIENT_ID = os.getenv('GOOGLE_OAUTH_CLIENT_ID', 'demo')
GOOGLE_OAUTH_CLIENT_SECRET = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET', 'demo')
YANDEX_OAUTH_CLIENT_ID = os.getenv('YANDEX_OAUTH_CLIENT_ID', 'demo')
YANDEX_OAUTH_CLIENT_SECRET = os.getenv('YANDEX_OAUTH_CLIENT_SECRET', 'demo')
TELEGRAM_BOT_ID = os.getenv('TELEGRAM_BOT_ID', '8314335876')
GEMINI_BASE_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent'
GEMINI_TIMEOUT = 30

# Конфигурация для разных типов задач
GEMINI_TASK_CONFIGS = {
    'chat': {
        'model': 'gemini-2.0-flash',
        'temperature': 0.7,
        'max_tokens': 1000,
        'system_prompt': 'Ты - умный помощник для подготовки к экзаменам. Отвечай кратко, но по существу.'
    },
    'task_explanation': {
        'model': 'gemini-2.0-flash',
        'temperature': 0.3,
        'max_tokens': 800,
        'system_prompt': 'Ты - эксперт по объяснению учебных заданий. Объясняй понятно, с примерами и пошагово.'
    },
    'hint_generation': {
        'model': 'gemini-2.0-flash',
        'temperature': 0.5,
        'max_tokens': 400,
        'system_prompt': 'Ты - помощник, который дает подсказки к заданиям. Не давай прямого ответа, только направляй к решению.'
    },
    'personalized_learning': {
        'model': 'gemini-2.0-flash',
        'temperature': 0.4,
        'max_tokens': 600,
        'system_prompt': 'Ты - персональный тренер по обучению. Анализируй прогресс ученика и давай рекомендации.'
    }
}

# ==========================================
# НАСТРОЙКИ OPENAI GPT - УДАЛЕНЫ
# ==========================================

# OpenAI провайдер удален - используем только Gemini
# Все настройки перенесены в GEMINI_TASK_CONFIGS

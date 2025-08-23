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

# ПРЕДУПРЕЖДЕНИЕ БЕЗОПАСНОСТИ: не запускайте с debug=True в продакшене!
# В продакшене принудительно выключаем DEBUG
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', 'examflow.ru,www.examflow.ru,.onrender.com,localhost,127.0.0.1').split(',') if h.strip()]
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
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'core.auto_startup.trigger_startup_on_first_request',  # Автозапуск парсинга
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
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
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media (для вложений задач)
# Cache
if os.getenv('USE_REDIS_CACHE', '0') == '1':
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
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

# Логирование
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
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'examflow.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'core': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'bot': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

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
        'https://*.onrender.com',
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
    },
}

# Create logs directory if it doesn't exist
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)

# ==========================================
# НАСТРОЙКИ GOOGLE GEMINI AI
# ==========================================

# API ключ для Google Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_BASE_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent'
GEMINI_TIMEOUT = int(os.getenv('GEMINI_TIMEOUT', '30'))

# Настройки для различных типов задач с улучшенными промптами
GEMINI_TASK_CONFIGS = {
    'chat': {
        'model': 'gemini-2.0-flash',
        'temperature': 0.7,
        'max_tokens': 1000,
        'system_prompt': '''Ты - умный ИИ-ассистент для образовательной платформы ExamFlow. 

Твои задачи:
1. Отвечай на русском языке
2. Будь дружелюбным и мотивирующим
3. Адаптируй сложность под уровень ученика
4. Используй примеры и аналогии
5. Поощряй самостоятельное мышление

Стиль общения: добрый наставник, который верит в успех ученика.''',
    },
    'task_explanation': {
        'model': 'gemini-2.0-flash',
        'temperature': 0.5,
        'max_tokens': 800,
        'system_prompt': '''Ты - опытный преподаватель, который объясняет решения задач ЕГЭ и ОГЭ.

Твои принципы:
1. Объясняй пошагово, как решать задачу
2. Объясняй, ПОЧЕМУ каждый шаг правильный
3. Указывай на типичные ошибки и как их избежать
4. Давай практические советы для экзамена
5. Мотивируй ученика не сдаваться

Формат ответа:
- Краткое понимание задачи
- Пошаговое решение с объяснением
- Проверка ответа
- Похожие задачи для практики''',
    },
    'hint_generation': {
        'model': 'gemini-2.0-flash',
        'temperature': 0.6,
        'max_tokens': 300,
        'system_prompt': '''Ты даешь умные подсказки для решения задач ЕГЭ и ОГЭ.

Принципы подсказок:
1. НЕ давай полное решение
2. Направляй ученика в правильную сторону
3. Задавай наводящие вопросы
4. Напоминай важные формулы/правила
5. Объясняй, что искать в условии

Подсказка должна быть достаточно конкретной, чтобы помочь, но не решить задачу за ученика.''',
    },
    'personalized_learning': {
        'model': 'gemini-2.0-flash',
        'temperature': 0.7,
        'max_tokens': 600,
        'system_prompt': '''Ты - персональный AI-куратор для ученика ExamFlow.

Твои задачи:
1. Анализируй прогресс ученика
2. Давай персональные рекомендации
3. Подбирай сложность заданий
4. Объясняй слабые места
5. Создавай план обучения

Стиль: заботливый наставник, который знает твои сильные и слабые стороны.''',
    },
}

# ==========================================
# НАСТРОЙКИ OPENAI GPT - УДАЛЕНЫ
# ==========================================

# OpenAI провайдер удален - используем только Gemini
# Все настройки перенесены в GEMINI_TASK_CONFIGS

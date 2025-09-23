"""Базовые настройки Django для ExamFlow."""

import os
import dj_database_url
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-b=8q90=se^7twm97htmj$v2n-(b@8!0(%h48n=tnb=t^%ja!ta')

# Настройка модели пользователя
AUTH_USER_MODEL = 'telegram_auth.TelegramUser'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', 'examflow.ru, www.examflow.ru, localhost, 127.0.0.1, testserver, examflow.onrender.com').split(', ') if h.strip()]
# Доп. подстраховка для прод окружений, где Render делает health-пинги от имени домена
for host in ['examflow.ru', 'www.examflow.ru']:
    if host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(host)

# Добавим хост Render автоматически, если предоставлен платформой
RENDER_HOST = os.getenv('RENDER_EXTERNAL_HOSTNAME')
if RENDER_HOST and RENDER_HOST not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RENDER_HOST)

# Автоматический fallback режим для Render при проблемах с БД
if RENDER_HOST:
    os.environ.setdefault('FALLBACK_MODE', 'true')
    # Принудительно отключаем БД на Render при SSL проблемах
    os.environ.setdefault('USE_SQLITE_FALLBACK', 'true')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'corsheaders',
    'csp',
    'drf_spectacular',

    # Основные модули (legacy)
    'core',

    # Новые модульные приложения
    'learning',
    'ai',
    'analytics',
    'themes',
    'telegram_bot',
    'telegram_auth',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'csp.middleware.CSPMiddleware',
    'telegram_auth.middleware.TelegramAuthMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'examflow_project.middleware.DatabaseErrorMiddleware',  # Добавляем обработку ошибок БД
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'core.premium.middleware.PremiumAccessMiddleware',  # Отключено - модуль не существует
]

ROOT_URLCONF = 'examflow_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'examflow_project.context_processors.static_version',
            ],
        },
    },
]

WSGI_APPLICATION = 'examflow_project.wsgi.application'

# Database
_DATABASE_URL = os.getenv('DATABASE_URL')
# Проверяем принудительный SQLite fallback для Render
USE_SQLITE_FALLBACK = os.getenv('USE_SQLITE_FALLBACK', 'false').lower() == 'true'

if USE_SQLITE_FALLBACK and RENDER_HOST:
    # Принудительный SQLite для Render при проблемах с PostgreSQL
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': '/tmp/examflow_render.db',
            'OPTIONS': {
                'timeout': 30,
            },
        }
    }
    print("🔧 RENDER FALLBACK: Используется SQLite вместо PostgreSQL")
elif _DATABASE_URL:
    # Используем DATABASE_URL, если он задан (для тестов/CI/локально можно указать sqlite:///)
    DATABASES = {
        'default': dj_database_url.config(default=_DATABASE_URL)
    }
    # Настройки SSL для PostgreSQL на Render.com
    if 'postgres' in _DATABASE_URL and ('render.com' in _DATABASE_URL or '35.227.164.209' in _DATABASE_URL or 'dpg-d2dn09ali9vc73b2lg7g-a' in _DATABASE_URL or 'dpg-' in _DATABASE_URL):
        # Минимальный набор опций для совместимости с psycopg3 на Windows/CI
        DATABASES['default']['OPTIONS'] = {
            'sslmode': 'require',
            'connect_timeout': 60,
            'application_name': 'examflow_render',
            'target_session_attrs': 'read-write',
        }
        # Дополнительные настройки для Render
        DATABASES['default']['ENGINE'] = 'django.db.backends.postgresql'
        DATABASES['default']['CONN_MAX_AGE'] = 0  # Отключаем пул соединений для Render
        DATABASES['default']['CONN_HEALTH_CHECKS'] = True  # Проверка здоровья соединений
    elif 'postgres' in _DATABASE_URL and ('localhost' in _DATABASE_URL or '127.0.0.1' in _DATABASE_URL):
        # Локальный PostgreSQL без SSL
        DATABASES['default']['OPTIONS'] = {
            'sslmode': 'disable',
            'connect_timeout': 30,
        }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'examflow'),
            'USER': os.getenv('DB_USER', 'postgres'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
            'OPTIONS': {
                'sslmode': 'prefer',  # Изменено с 'require' на 'prefer' для локальной разработки
                'connect_timeout': 30,
            },
        }
    }

# Password validation
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
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Session settings
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 1209600  # 2 weeks

# CSRF settings
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_AGE = 31449600  # 1 year

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "https://examflow.ru",
    "https://www.examflow.ru",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

CORS_ALLOW_CREDENTIALS = True

# Telegram settings
TELEGRAM_BOT_USERNAME = 'examflow_bot'  # Имя бота без @

# AI API Keys
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')

# AI Configuration
GEMINI_TASK_CONFIGS = {
    'chat': {
        'model': 'gemini-1.5-flash',
        'temperature': 0.7,
        'max_tokens': 300,
        'system_prompt': 'Ты - ExamFlow AI, эксперт по подготовке к ЕГЭ и ОГЭ. Отвечай кратко и по делу.'
    },
    'math': {
        'model': 'gemini-1.5-flash',
        'temperature': 0.3,
        'max_tokens': 400,
        'system_prompt': 'Ты - ExamFlow AI, эксперт по математике ЕГЭ и ОГЭ. Давай пошаговые решения.'
    },
    'russian': {
        'model': 'gemini-1.5-flash',
        'temperature': 0.5,
        'max_tokens': 350,
        'system_prompt': 'Ты - ExamFlow AI, эксперт по русскому языку ЕГЭ и ОГЭ. Помогай с грамматикой и сочинениями.'
    }
}

# AI Timeouts
GEMINI_TIMEOUT = 10
GEMINI_MOBILE_TIMEOUT = 5

# Cache settings
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'rediss://red-d2qldkje5dus73c73tr0:zccbozd9aZ5sbiSSZ8xZaJpW9qM3BnOz@oregon-keyvalue.render.com:6379'),
    }
}

# Celery settings
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@examflow.ru')

# Admin settings
ADMIN_URL = os.getenv('ADMIN_URL', 'admin/')

# Static version for cache busting
STATIC_VERSION = os.getenv('STATIC_VERSION', 'v20250922-3')
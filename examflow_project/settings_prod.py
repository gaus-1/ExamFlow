"""
Настройки Django для продакшена ExamFlow 2.0
"""

import os

import dj_database_url

from .settings import *  # noqa: F403, F401

# Принудительно отключаем DEBUG в продакшене
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Генерируем новый SECRET_KEY для продакшена
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECURITY: SECRET_KEY must be set via environment in production")

# Настройки безопасности для продакшена
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_SECONDS = int(
    os.getenv("SECURE_HSTS_SECONDS", "31536000")
)  # по умолчанию 1 год
SECURE_REDIRECT_EXEMPT = []
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "true").lower() == "true"
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "true").lower() == "true"
CSRF_COOKIE_SECURE = os.getenv("CSRF_COOKIE_SECURE", "true").lower() == "true"
X_FRAME_OPTIONS = "DENY"

# Настройки статических файлов для продакшена
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")  # noqa: F405
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Настройки базы данных для продакшена с поддержкой SQLite fallback
USE_SQLITE_FALLBACK = os.getenv("USE_SQLITE_FALLBACK", "false").lower() == "true"
database_url = os.getenv("DATABASE_URL")

if USE_SQLITE_FALLBACK:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": "/tmp/examflow_render.db",
            "OPTIONS": {
                "timeout": 30,
            },
        }
    }
else:
    DATABASES = {
        "default": dj_database_url.config(
            default=database_url,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
    # Если DATABASE_URL пуст, также откатываемся на SQLite, чтобы сервис поднялся
    if not database_url:
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": "/tmp/examflow_render.db",
                "OPTIONS": {
                    "timeout": 30,
                },
            }
        }


# Настройки логирования для продакшена
class MaskSecretsFilter:
    """Фильтр для маскировки секретов в логах."""

    SENSITIVE_KEYS = (
        "password",
        "secret",
        "token",
        "authorization",
        "api_key",
        "sessionid",
    )

    def filter(self, record):  # noqa: D401
        try:
            msg = str(record.getMessage())
            for key in self.SENSITIVE_KEYS:
                if key in msg.lower():
                    msg = msg.replace(key, "***")
            record.msg = msg
        except Exception:
            pass
        return True


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            "filters": ["mask_secrets"],
        },
    },
    "filters": {
        "mask_secrets": {
            "()": MaskSecretsFilter,
        }
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# Настройки кеширования для продакшена (условно Redis или локальная память)
USE_REDIS_CACHE = os.getenv("USE_REDIS_CACHE", "0") == "1"
REDIS_URL = os.getenv("REDIS_URL", "")
if USE_REDIS_CACHE and REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            },
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "examflow-local-cache",
        }
    }

# Настройки сессий для продакшена
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# Настройки CORS для продакшена
CORS_ALLOWED_ORIGINS = [
    "https://examflow.ru",
    "https://www.examflow.ru",
    "https://examflow.onrender.com",
]

# Настройки Content Security Policy (разрешаем собственный домен и нужные внешние источники)
CSP_DEFAULT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://fonts.googleapis.com")
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "https://www.googletagmanager.com")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com")
CSP_CONNECT_SRC = ("'self'", "https://generativelanguage.googleapis.com")

# Настройки rate limiting для продакшена
RATELIMIT_USE_CACHE = "default"
RATELIMIT_ENABLE = True

# Настройки для Render
if os.getenv("RENDER"):
    # Автоматически добавляем хост Render
    RENDER_HOST = os.getenv("RENDER_EXTERNAL_HOSTNAME")
    if RENDER_HOST:
        ALLOWED_HOSTS.append(RENDER_HOST)  # noqa: F405

    # Настройки для статических файлов на Render
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

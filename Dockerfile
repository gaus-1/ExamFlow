FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_HOME=/app

WORKDIR ${APP_HOME}

# Системные зависимости
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev curl \
  && rm -rf /var/lib/apt/lists/*

# Устанавливаем зависимости отдельно для лучшего кэша
COPY requirements.txt ./
RUN python -m pip install --upgrade pip && pip install -r requirements.txt

# Копируем проект
COPY . .

# Переменные окружения по умолчанию (могут быть переопределены)
ENV DJANGO_SETTINGS_MODULE=examflow_project.settings \
    PORT=8000 \
    HOST=0.0.0.0

# Сбор статики (не критично при отсутствии конфига, поэтому не валимся)
RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

# Команда по умолчанию: Gunicorn (WSGI)
CMD ["bash", "-lc", "gunicorn examflow_project.wsgi:application --bind 0.0.0.0:${PORT} --workers 3 --timeout 120"]



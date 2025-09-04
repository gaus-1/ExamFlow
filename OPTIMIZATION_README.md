# 🚀 РУКОВОДСТВО ПО ОПТИМИЗАЦИИ EXAMFLOW 2.0

## 📋 БЫСТРЫЙ СТАРТ

### 1. Запуск полной оптимизации
```bash
# Установите зависимости
pip install -r requirements-optimization.txt

# Запустите полную оптимизацию
python scripts/optimize_all.py
```

### 2. Запуск отдельных оптимизаций
```bash
# Только безопасность
python scripts/optimize_security.py

# Только производительность
python scripts/optimize_performance.py

# Только качество кода
python scripts/optimize_code_quality.py
```

## 🔧 ИНСТРУМЕНТЫ

### Безопасность
- **safety** - проверка уязвимостей в зависимостях
- **bandit** - поиск проблем безопасности в коде
- **pip-audit** - аудит pip пакетов
- **django-csp** - Content Security Policy
- **django-ratelimit** - ограничение частоты запросов

### Производительность
- **django-compressor** - сжатие статических файлов
- **Pillow** - оптимизация изображений
- **django-debug-toolbar** - профилирование
- **memory-profiler** - профилирование памяти
- **django-extensions** - дополнительные команды

### Качество кода
- **mypy** - проверка типов
- **black** - форматирование кода
- **isort** - сортировка импортов
- **flake8** - линтинг
- **pylint** - расширенный линтинг
- **sphinx** - документация

## 📊 МЕТРИКИ

### Производительность
- **Lighthouse Score**: >90 (цель)
- **Время загрузки**: <3 сек
- **Размер бандла**: <500KB
- **Core Web Vitals**: все зеленые

### Безопасность
- **Критические уязвимости**: 0
- **Security Headers**: 95%+
- **Dependency Audit**: 0 уязвимостей

### Качество кода
- **Type Coverage**: 100%
- **Test Coverage**: 80%+
- **PEP 8 Compliance**: 98%+
- **Documentation**: 90%+

## 🛠️ КОНФИГУРАЦИЯ

### Pre-commit хуки
```bash
# Установка
pip install pre-commit
pre-commit install

# Запуск для всех файлов
pre-commit run --all-files
```

### MyPy конфигурация
```ini
# mypy.ini
[mypy]
python_version = 3.11
warn_return_any = True
disallow_untyped_defs = True
```

### Black конфигурация
```toml
# pyproject.toml
[tool.black]
line-length = 100
target-version = ['py311']
```

## 🧪 ТЕСТИРОВАНИЕ

### Запуск тестов
```bash
# Все тесты
python manage.py test

# С покрытием
pytest --cov=. --cov-report=html

# Только производительность
python manage.py test tests.test_performance
```

### Тесты безопасности
```bash
# Bandit
bandit -r . -f json -o bandit-report.json

# Safety
safety check

# Pip audit
pip-audit
```

## 📚 ДОКУМЕНТАЦИЯ

### Генерация документации
```bash
cd docs
sphinx-build -b html . _build/html
```

### Просмотр документации
```bash
# Откройте docs/_build/html/index.html в браузере
```

## 🔄 CI/CD

### GitHub Actions
Автоматические проверки запускаются при:
- Push в main/master
- Pull Request
- Еженедельно по понедельникам

### Локальная проверка
```bash
# Запуск всех проверок локально
python scripts/optimize_all.py
```

## 🚨 УСТРАНЕНИЕ ПРОБЛЕМ

### Частые проблемы

#### 1. MyPy ошибки
```bash
# Игнорировать конкретную ошибку
# type: ignore

# Игнорировать весь файл
# mypy: ignore-errors
```

#### 2. Black конфликты
```bash
# Принудительное форматирование
black --line-length 100 .

# Проверка без изменений
black --check .
```

#### 3. Flake8 ошибки
```bash
# Игнорировать конкретную ошибку
# noqa: E501

# Игнорировать весь файл
# flake8: noqa
```

#### 4. Тесты не проходят
```bash
# Запуск с подробным выводом
python manage.py test --verbosity=2

# Запуск конкретного теста
python manage.py test tests.test_ai_api.AIAssistantAPITests.test_valid_prompt
```

## 📈 МОНИТОРИНГ

### Логи производительности
```bash
# Просмотр логов
tail -f logs/django.log

# Фильтр по производительности
grep "Performance:" logs/django.log
```

### Debug Toolbar
```python
# В settings.py
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
```

## 🔄 ОБНОВЛЕНИЕ

### Обновление зависимостей
```bash
# Проверка устаревших пакетов
pip list --outdated

# Обновление всех пакетов
pip install --upgrade -r requirements-optimization.txt

# Проверка безопасности после обновления
safety check
```

### Обновление конфигураций
```bash
# Обновление pre-commit хуков
pre-commit autoupdate

# Обновление GitHub Actions
# Проверьте .github/workflows/ на наличие обновлений
```

## 📞 ПОДДЕРЖКА

### Получение помощи
1. Проверьте логи: `tail -f logs/django.log`
2. Запустите диагностику: `python manage.py check`
3. Проверьте документацию в `docs/`
4. Создайте issue в GitHub

### Полезные команды
```bash
# Диагностика Django
python manage.py check --deploy

# Сбор статики
python manage.py collectstatic --noinput

# Миграции
python manage.py migrate

# Создание суперпользователя
python manage.py createsuperuser

# Запуск сервера
python manage.py runserver
```

---

**Готово к использованию! 🚀**

Для начала работы просто запустите:
```bash
python scripts/optimize_all.py
```

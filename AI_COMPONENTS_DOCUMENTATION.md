# 🤖 Документация AI компонентов ExamFlow

## 📋 Обзор архитектуры

После оптимизации AI система ExamFlow состоит из следующих компонентов:

### 🏗️ Основные модули

1. **`ai/config.py`** - Единая конфигурация всех AI компонентов
2. **`ai/optimized_service.py`** - Оптимизированный AI сервис
3. **`telegram_bot/optimized_service.py`** - Оптимизированный бот сервис
4. **`core/rag_system/`** - RAG система (поиск и генерация)
5. **`telegram_bot/gamification.py`** - Система геймификации

---

## 🔧 Конфигурация (`ai/config.py`)

### Назначение
Централизованное управление всеми настройками AI системы.

### Основные классы

#### `AIProviderConfig`
Конфигурация AI провайдера (Gemini, OpenAI, etc.)
```python
@dataclass
class AIProviderConfig:
    name: str                    # Название провайдера
    api_key: str                 # API ключ
    base_url: str                # Базовый URL
    model: str                   # Модель AI
    temperature: float = 0.7     # Температура генерации
    max_tokens: int = 1000       # Максимум токенов
    timeout: int = 30            # Таймаут запроса
    priority: int = 1            # Приоритет (1 = высший)
    is_active: bool = True       # Активен ли провайдер
```

#### `RAGConfig`
Конфигурация RAG системы
```python
@dataclass
class RAGConfig:
    max_context_tokens: int = 4000      # Максимум токенов контекста
    max_response_tokens: int = 1000     # Максимум токенов ответа
    top_k_chunks: int = 5               # Количество источников
    similarity_threshold: float = 0.7   # Порог схожести
    cache_ttl: int = 600                # Время жизни кэша (сек)
    timeout_seconds: int = 30           # Таймаут RAG запросов
```

#### `LimitsConfig`
Конфигурация лимитов пользователей
```python
@dataclass
class LimitsConfig:
    daily_guest_limit: int = 10      # Лимит для гостей (день)
    daily_auth_limit: int = 30       # Лимит для авторизованных (день)
    weekly_auth_limit: int = 200     # Лимит для авторизованных (неделя)
    monthly_auth_limit: int = 1000   # Лимит для авторизованных (месяц)
```

### Шаблоны промптов

#### `PromptTemplates`
Готовые шаблоны для разных типов задач:

- **`SYSTEM_BASE`** - Базовый системный промпт
- **`TASK_EXPLANATION`** - Объяснение решения задачи
- **`HINT_GENERATION`** - Генерация подсказок
- **`PERSONALIZED_HELP`** - Персонализированная помощь
- **`LEARNING_PLAN`** - Создание плана обучения

### Использование
```python
from ai.config import ai_config

# Получить конфигурацию провайдера
provider = ai_config.get_provider_config('gemini')

# Получить шаблон промпта
prompt = ai_config.get_prompt_template(
    'TASK_EXPLANATION',
    task_text="Решите уравнение x² + 5x + 6 = 0"
)

# Получить лимиты для пользователя
limits = ai_config.get_limits_for_user(is_authenticated=True)
```

---

## 🚀 AI Сервис (`ai/optimized_service.py`)

### Назначение
Единый сервис для всех AI операций с оптимизированной архитектурой.

### Основные методы

#### `ask(prompt, user, task_type, use_rag, use_cache)`
Главный метод для AI запросов
```python
result = ai_service.ask(
    prompt="Как решить квадратное уравнение?",
    user=user,
    task_type="task_explanation",
    use_rag=True,
    use_cache=True
)
```

#### `explain_task(task_text, user)`
Объяснение решения задачи
```python
result = ai_service.explain_task(
    task_text="x² + 5x + 6 = 0",
    user=user
)
```

#### `get_hint(task_text, user)`
Получение подсказки для задачи
```python
result = ai_service.get_hint(
    task_text="Найдите корни уравнения",
    user=user
)
```

#### `get_personalized_help(task_text, user, user_level, weak_topics, strong_topics)`
Персонализированная помощь
```python
result = ai_service.get_personalized_help(
    task_text="Решите неравенство",
    user=user,
    user_level=3,
    weak_topics=["алгебра", "функции"],
    strong_topics=["геометрия"]
)
```

#### `get_learning_plan(user, current_level, accuracy, weak_topics, goal)`
Создание плана обучения
```python
result = ai_service.get_learning_plan(
    user=user,
    current_level=3,
    accuracy=75.0,
    weak_topics=["алгебра"],
    goal="Подготовка к ЕГЭ"
)
```

### Внутренние методы

- **`_check_limits(user)`** - Проверка лимитов пользователя
- **`_update_limits(user)`** - Обновление лимитов
- **`_get_cached_result(prompt, task_type)`** - Получение из кэша
- **`_cache_result(prompt, task_type, result)`** - Сохранение в кэш
- **`_get_best_provider(task_type)`** - Выбор провайдера
- **`_prepare_prompt(prompt, user, task_type, use_rag)`** - Подготовка промпта
- **`_generate_response(prompt, provider_config, task_type)`** - Генерация ответа
- **`_log_request(user, prompt, result, processing_time)`** - Логирование

---

## 🤖 Бот Сервис (`telegram_bot/optimized_service.py`)

### Назначение
Единый сервис для всех операций Telegram бота с оптимизированной архитектурой.

### Основные методы

#### `get_start_message(user_id)`
Получение приветственного сообщения
```python
message, keyboard = await bot_service.get_start_message(user_id)
```

#### `get_subjects_menu()`
Получение меню предметов
```python
message, keyboard = await bot_service.get_subjects_menu()
```

#### `get_subject_topics(subject_id)`
Получение тем предмета
```python
message, keyboard = await bot_service.get_subject_topics(subject_id)
```

#### `get_random_task(subject_id)`
Получение случайного задания
```python
message, keyboard = await bot_service.get_random_task(subject_id)
```

#### `get_ai_response(prompt, user_id, task_id)`
Получение ответа от AI
```python
message, keyboard = await bot_service.get_ai_response(
    prompt="Как решить уравнение?",
    user_id=user_id,
    task_id=123
)
```

#### `get_user_stats(user_id)`
Получение статистики пользователя
```python
message, keyboard = await bot_service.get_user_stats(user_id)
```

### Клавиатуры

#### `_get_main_menu_keyboard()`
Главное меню с кнопками:
- 📚 Предметы
- 🎲 Случайное задание
- 🤖 AI Помощник
- 📊 Статистика
- 🏆 Достижения

#### `_get_subjects_keyboard(subjects)`
Клавиатура предметов с кнопками для каждого предмета

#### `_get_topics_keyboard(subject_id, topics)`
Клавиатура тем предмета

#### `_get_task_keyboard(task_id)`
Клавиатура задания с кнопками:
- 🤖 Объяснить
- 💡 Подсказка
- ✅ Решено
- 🎲 Другое задание
- 🔙 Главное меню

#### `_get_ai_keyboard()`
Клавиатура AI с кнопками:
- 🔄 Новый вопрос
- 📚 Предметы
- 🔙 Главное меню

#### `_get_stats_keyboard()`
Клавиатура статистики с кнопками:
- 🏆 Достижения
- 📈 Прогресс
- 🔙 Главное меню

---

## 🔍 RAG Система (`core/rag_system/`)

### Назначение
Система поиска и генерации ответов на основе базы знаний.

### Основные компоненты

#### `orchestrator.py`
Центральный оркестратор RAG системы
```python
from core.rag_system.orchestrator import RAGOrchestrator

orchestrator = RAGOrchestrator()
result = orchestrator.process_query(
    query="Как решить квадратное уравнение?",
    subject="математика",
    user_id=123
)
```

#### `vector_store.py`
Векторное хранилище для семантического поиска

#### `text_processor.py`
Обработка текста для индексации

#### `search_api.py`
API для поиска по базе знаний

#### `ai_api.py`
API для AI запросов

---

## 🎮 Геймификация (`telegram_bot/gamification.py`)

### Назначение
Система геймификации для мотивации пользователей.

### Основные функции

#### `add_points(user_id, points, reason)`
Добавление очков пользователю
```python
result = await gamification.add_points(
    user_id=123,
    points=10,
    reason="Правильный ответ"
)
```

#### `check_achievements(user_id)`
Проверка достижений
```python
achievements = await gamification.check_achievements(user_id)
```

#### `get_leaderboard(limit)`
Получение таблицы лидеров
```python
leaders = await gamification.get_leaderboard(10)
```

#### `get_daily_challenges(user_id)`
Получение ежедневных заданий
```python
challenges = await gamification.get_daily_challenges(user_id)
```

---

## 📊 Модели данных

### `ai/models.py`
- **`AiRequest`** - Запросы к AI
- **`AiResponse`** - Ответы AI
- **`AiProvider`** - Провайдеры AI
- **`AiLimit`** - Лимиты пользователей

### `authentication/models.py`
- **`UserProfile`** - Профили пользователей

### `learning/models.py`
- **`Subject`** - Предметы
- **`Task`** - Задания
- **`UserProgress`** - Прогресс пользователей

---

## 🔄 Интеграция компонентов

### Схема взаимодействия

```
Telegram Bot
    ↓
OptimizedBotService
    ↓
OptimizedAIService
    ↓
AIConfig + RAGOrchestrator
    ↓
AI Providers (Gemini, OpenAI)
```

### Пример использования

```python
# В обработчике команды /start
from telegram_bot.optimized_service import bot_service

async def start_command(update, context):
    user_id = update.effective_user.id
    message, keyboard = await bot_service.get_start_message(user_id)
    await update.message.reply_text(message, reply_markup=keyboard)

# В обработчике AI запроса
async def ai_query(update, context):
    user_id = update.effective_user.id
    prompt = update.message.text
    
    message, keyboard = await bot_service.get_ai_response(prompt, user_id)
    await update.message.reply_text(message, reply_markup=keyboard)
```

---

## 🚀 Преимущества оптимизированной архитектуры

### ✅ Устранены дубли
- Удалены дублирующиеся AI сервисы
- Объединены RAG системы
- Унифицированы бот сервисы

### ✅ Единая конфигурация
- Централизованные настройки
- Легкое управление провайдерами
- Гибкая настройка лимитов

### ✅ Принцип единственной ответственности
- Каждый модуль отвечает за свою область
- Четкое разделение функций
- Легкое тестирование

### ✅ Оптимизированная производительность
- Эффективное кэширование
- Минимальные запросы к БД
- Асинхронная обработка

### ✅ Согласованный стиль кода
- Единые стандарты
- Подробная документация
- Логирование ошибок

---

## 🔧 Настройка и развертывание

### Переменные окружения
```bash
# AI провайдеры
GEMINI_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key

# RAG настройки
RAG_CONFIG_MAX_CONTEXT_LENGTH=4000
RAG_CONFIG_MAX_SOURCES=5
RAG_CONFIG_SIMILARITY_THRESHOLD=0.7

# Лимиты
AI_LIMITS_DAILY_GUEST=10
AI_LIMITS_DAILY_AUTH=30
```

### Миграции
```bash
python manage.py makemigrations
python manage.py migrate
```

### Тестирование
```bash
python manage.py test ai
python manage.py test telegram_bot
```

---

## 📈 Мониторинг и логирование

### Логи
- Все AI запросы логируются в `AiRequest`
- Ошибки записываются в Django лог
- Метрики производительности

### Мониторинг
- Количество запросов по провайдерам
- Время ответа AI
- Использование лимитов
- Популярные запросы

---

## 🔮 Планы развития

### Краткосрочные (1-2 недели)
- [ ] Интеграция с OpenAI API
- [ ] Улучшение RAG системы
- [ ] Добавление новых типов задач

### Среднесрочные (1-2 месяца)
- [ ] Машинное обучение для персонализации
- [ ] Аналитика пользовательского поведения
- [ ] A/B тестирование промптов

### Долгосрочные (3-6 месяцев)
- [ ] Собственная модель AI
- [ ] Мультиязычная поддержка
- [ ] Интеграция с внешними образовательными платформами

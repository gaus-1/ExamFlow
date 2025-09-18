# 🚀 Настройка работы 24/7 для ExamFlow 2.0

## 📋 Обзор решения

Комплексное решение для обеспечения бесперебойной работы ExamFlow 24/7 с использованием бесплатных инструментов и оптимизацией для Render бесплатного тарифа.

## 🏗️ Архитектура решения

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GitHub Actions│    │   Render Web    │    │  UptimeRobot    │
│   (Keepalive)   │───▶│   (ExamFlow)    │◀───│  (Monitoring)   │
│   Every 5 min   │    │   + PostgreSQL  │    │  Every 5 min    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Health Check  │    │  Keepalive      │    │  Notifications  │
│   Endpoints     │    │  Service        │    │  (Email/Telegram)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔧 Компоненты решения

### 1. Health Check Endpoints

**Основной health check** (`/health/`):
- Проверяет все компоненты системы
- Возвращает детальную информацию о состоянии
- Время ответа: ~2-5 секунд

**Простой health check** (`/health/simple/`):
- Быстрая проверка базы данных
- Время ответа: ~0.5-1 секунда
- Используется для Render health check

### 2. Keepalive Service

**Встроенный сервис** (`core/keepalive_service.py`):
- Проверяет компоненты каждые 5 минут
- Автоматически будит неработающие сервисы
- Ведет статистику работы
- Отправляет уведомления при сбоях

**Команда управления**:
```bash
# Запуск в режиме демона
python manage.py manage_keepalive start --daemon

# Проверка статуса
python manage.py manage_keepalive status

# Однократная проверка
python manage.py manage_keepalive check

# Пробуждение сервисов
python manage.py manage_keepalive wake
```

### 3. GitHub Actions

**Улучшенный workflow** (`.github/workflows/keepalive-enhanced.yml`):
- Запуск каждые 5 минут
- Проверка всех основных эндпоинтов
- Тестирование производительности
- Уведомления при сбоях

### 4. Render Configuration

**Оптимизированная конфигурация** (`render.yaml`):
- Health check каждые 30 секунд
- Cron задачи для пробуждения
- Настройки для бесплатного тарифа
- Автоматический перезапуск

## 🚀 Пошаговая настройка

### Шаг 1: Настройка Render

1. **Обновите настройки сервиса в Render Dashboard:**
   - Health Check Path: `/health/simple/`
   - Health Check Interval: 30 секунд
   - Auto-Restart: Включено
   - Health Check Timeout: 10 секунд

2. **Добавьте переменные окружения:**
   ```env
   WEBSITE_URL=https://examflow.ru
   ENVIRONMENT=production
   USE_REDIS_CACHE=0
   ```

3. **Настройте Cron задачи:**
   - Перейдите в раздел "Cron Jobs"
   - Добавьте задачу: `curl -s https://examflow.ru/health/simple/ > /dev/null`
   - Интервал: каждые 10 минут

### Шаг 2: Настройка GitHub Actions

1. **Активируйте workflow:**
   - Перейдите в Settings → Actions
   - Включите "Allow all actions and reusable workflows"

2. **Проверьте настройки:**
   - Workflow запускается каждые 5 минут
   - Проверяет все основные эндпоинты
   - Отправляет уведомления при сбоях

### Шаг 3: Настройка UptimeRobot

1. **Запустите скрипт настройки:**
   ```bash
   python scripts/setup_uptimerobot.py
   ```

2. **Или настройте вручную:**
   - Зарегистрируйтесь на https://uptimerobot.com
   - Добавьте мониторы для всех эндпоинтов
   - Настройте уведомления (Email + Telegram)

### Шаг 4: Настройка Telegram уведомлений

1. **Создайте бота для уведомлений:**
   - Напишите @BotFather в Telegram
   - Создайте нового бота
   - Получите токен

2. **Добавьте токен в Render:**
   ```env
   UPTIMEROBOT_TELEGRAM_TOKEN=your_bot_token
   UPTIMEROBOT_TELEGRAM_CHAT_ID=your_chat_id
   ```

## 📊 Мониторинг и диагностика

### Health Check Endpoints

**Основной health check:**
```bash
curl https://examflow.ru/health/
```

**Простой health check:**
```bash
curl https://examflow.ru/health/simple/
```

### Логи и статистика

**Render Dashboard:**
- Логи сервиса
- Метрики производительности
- Статус health check

**GitHub Actions:**
- История запусков
- Результаты проверок
- Уведомления о сбоях

**UptimeRobot:**
- Статистика доступности
- История инцидентов
- Время отклика

### Команды диагностики

```bash
# Проверка статуса keepalive
python manage.py manage_keepalive status

# Однократная проверка
python manage.py manage_keepalive check

# Пробуждение сервисов
python manage.py manage_keepalive wake

# Проверка компонентов
python manage.py keepalive --once --component all
```

## ⚡ Оптимизация для Render бесплатного тарифа

### Ограничения бесплатного тарифа:
- 750 часов в месяц
- 512MB RAM
- 1GB storage
- Sleep после 15 минут неактивности

### Наши оптимизации:

1. **Эффективное использование памяти:**
   - Лимит использования: <400MB
   - Мониторинг через health check
   - Автоматическая очистка кэша

2. **Предотвращение засыпания:**
   - GitHub Actions каждые 5 минут
   - UptimeRobot каждые 5 минут
   - Cron задачи каждые 10 минут

3. **Оптимизация базы данных:**
   - Пул соединений
   - Кэширование запросов
   - Индексы для быстрых запросов

4. **Webhook вместо polling:**
   - Telegram бот использует webhook
   - Снижение нагрузки на CPU
   - Более быстрый отклик

## 🔧 Устранение неполадок

### Проблема: Сайт засыпает

**Решение:**
1. Проверьте GitHub Actions
2. Проверьте UptimeRobot мониторы
3. Запустите keepalive вручную:
   ```bash
   python manage.py manage_keepalive wake
   ```

### Проблема: Медленный отклик

**Решение:**
1. Проверьте использование памяти
2. Очистите кэш:
   ```bash
   python manage.py clear_cache
   ```
3. Перезапустите сервис в Render

### Проблема: Ошибки базы данных

**Решение:**
1. Проверьте подключение:
   ```bash
   python manage.py dbshell
   ```
2. Выполните миграции:
   ```bash
   python manage.py migrate
   ```

### Проблема: Telegram бот не отвечает

**Решение:**
1. Проверьте webhook:
   ```bash
   curl https://examflow.ru/bot/webhook/
   ```
2. Проверьте токен бота
3. Перезапустите webhook

## 📈 Метрики и KPI

### Ключевые метрики:

1. **Uptime (цель: >99%):**
   - Время доступности сайта
   - Время доступности API
   - Время доступности бота

2. **Response Time (цель: <3s):**
   - Время ответа главной страницы
   - Время ответа health check
   - Время ответа API

3. **Error Rate (цель: <1%):**
   - Процент ошибок 5xx
   - Процент таймаутов
   - Процент ошибок базы данных

### Мониторинг в реальном времени:

- **Render Dashboard**: Метрики сервиса
- **GitHub Actions**: Статус проверок
- **UptimeRobot**: Доступность эндпоинтов
- **Telegram**: Уведомления о сбоях

## 🎯 Результат

После настройки всех компонентов:

✅ **Сайт работает 24/7** без засыпания  
✅ **Telegram бот отвечает** в любое время  
✅ **База данных доступна** постоянно  
✅ **Автоматическое восстановление** при сбоях  
✅ **Мониторинг** всех компонентов  
✅ **Уведомления** о проблемах  

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи в Render Dashboard
2. Проверьте статус в GitHub Actions
3. Проверьте мониторы в UptimeRobot
4. Запустите диагностические команды
5. Обратитесь к документации Render

---

**Система готова к работе 24/7! 🚀**

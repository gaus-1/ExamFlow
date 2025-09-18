# 🤖 ExamFlow Bot 24/7 - Полная настройка

Руководство по настройке Telegram бота для работы 24/7 в различных окружениях.

## 🎯 **Варианты развертывания**

### 1. 🏠 **Локальный сервер (Windows)**
Для запуска на собственном компьютере/сервере

### 2. ☁️ **Render.com (Облако)**
Бесплатный/платный облачный хостинг

### 3. 🐧 **Linux VPS**
Виртуальный частный сервер

---

## 🏠 **1. Настройка для Windows (Локальный сервер)**

### Шаг 1: Установка как системный сервис

```bash
# Запустите от имени администратора
cd C:\path\to\ExamFlow
deployment\windows\install_service.bat
```

### Шаг 2: Управление сервисом

```bash
# Запуск
deployment\windows\nssm.exe start ExamFlowBot

# Остановка
deployment\windows\nssm.exe stop ExamFlowBot

# Статус
deployment\windows\nssm.exe status ExamFlowBot

# Удаление
deployment\windows\nssm.exe remove ExamFlowBot confirm
```

### Шаг 3: Мониторинг

```bash
# Просмотр логов
type logs\bot_service.log

# Запуск мониторинга
python telegram_bot\monitoring.py
```

---

## ☁️ **2. Настройка для Render.com (Облако)**

### Шаг 1: Подготовка репозитория

1. Загрузите код на GitHub
2. Убедитесь, что `render.yaml` в корне проекта

### Шаг 2: Создание сервиса на Render.com

1. Зайдите на [render.com](https://render.com)
2. Подключите GitHub репозиторий
3. Render автоматически найдет `render.yaml`
4. Настройте переменные окружения:

```env
# Обязательные переменные
TELEGRAM_BOT_TOKEN=your_bot_token
SECRET_KEY=your_secret_key
GEMINI_API_KEY=your_gemini_key
DJANGO_SETTINGS_MODULE=examflow_project.settings_prod

# Автоматические (от Render)
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
```

### Шаг 3: Развертывание

1. Нажмите "Create" - Render развернет:
   - Web сервис (Django)
   - Worker сервис (Telegram Bot)
   - PostgreSQL база
   - Redis кэш

2. Бот автоматически запустится в режиме 24/7

---

## 🐧 **3. Настройка для Linux VPS**

### Шаг 1: Установка зависимостей

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv postgresql redis-server

# Клонируем проект
git clone https://github.com/your-repo/ExamFlow.git
cd ExamFlow

# Создаем виртуальное окружение
python3 -m venv venv
source venv/bin/activate
pip install -r config/requirements.txt
```

### Шаг 2: Настройка systemd сервиса

```bash
# Создаем сервис
sudo nano /etc/systemd/system/examflow-bot.service
```

```ini
[Unit]
Description=ExamFlow Telegram Bot
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/ExamFlow
Environment=DJANGO_SETTINGS_MODULE=examflow_project.settings
ExecStart=/path/to/ExamFlow/venv/bin/python telegram_bot/bot_24_7.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```bash
# Запускаем сервис
sudo systemctl daemon-reload
sudo systemctl enable examflow-bot
sudo systemctl start examflow-bot

# Проверяем статус
sudo systemctl status examflow-bot

# Просмотр логов
sudo journalctl -u examflow-bot -f
```

---

## 🔍 **Мониторинг и диагностика**

### Healthcheck endpoint

Бот создает healthcheck файл: `logs/bot_health_status.json`

```json
{
  "timestamp": "2025-09-18T14:30:00",
  "bot_online": true,
  "api_responsive": true,
  "database_connected": true,
  "ai_working": true,
  "overall_healthy": true,
  "errors": []
}
```

### Автоматические уведомления

Настройте `ADMIN_TELEGRAM_ID` для получения уведомлений:

```env
ADMIN_TELEGRAM_ID=123456789
```

### Интеграция с UptimeRobot

```env
UPTIMEROBOT_API_KEY=your_api_key
```

---

## ⚙️ **Настройки производительности**

### Для высоконагруженных ботов:

```python
# telegram_bot/bot_24_7.py
class ExamFlowBot24_7:
    def __init__(self):
        # Увеличиваем лимиты
        self.max_restarts = 100
        self.check_interval = 60  # Проверка каждую минуту
```

### Масштабирование на Render.com:

```yaml
# render.yaml
services:
  - type: worker
    name: examflow-bot
    plan: standard  # Больше ресурсов
    scaling:
      minInstances: 1
      maxInstances: 3
```

---

## 🚨 **Устранение неполадок**

### Бот не запускается

1. **Проверьте токен:**
   ```bash
   curl https://api.telegram.org/bot<TOKEN>/getMe
   ```

2. **Проверьте базу данных:**
   ```bash
   python manage.py dbshell
   ```

3. **Проверьте логи:**
   ```bash
   tail -f logs/bot_service.log
   ```

### Бот часто перезапускается

1. **Увеличьте timeout:**
   ```python
   # В bot_24_7.py
   self.max_restarts = 50
   ```

2. **Проверьте память:**
   ```bash
   free -h
   htop
   ```

3. **Оптимизируйте AI запросы:**
   ```python
   # Добавьте кэширование
   @lru_cache(maxsize=100)
   def process_ai_query(query):
       # ...
   ```

---

## 📊 **Метрики и аналитика**

### Логирование событий

```python
# Добавьте в bot_handlers.py
logger.info(f"User {user_id} used command: {command}")
logger.info(f"AI query processed in {time:.2f}s")
```

### Мониторинг ресурсов

```bash
# CPU и память
htop

# Дисковое пространство
df -h

# Сетевая активность
iftop
```

---

## 🔐 **Безопасность**

### Рекомендации:

1. **Используйте переменные окружения** для секретов
2. **Настройте firewall** для VPS
3. **Регулярно обновляйте** зависимости
4. **Мониторьте логи** на подозрительную активность
5. **Делайте резервные копии** базы данных

### Автоматическое обновление:

```bash
# Создайте cron job
0 4 * * 1 cd /path/to/ExamFlow && git pull && pip install -r config/requirements.txt && sudo systemctl restart examflow-bot
```

---

## 🎉 **Готово!**

Теперь ваш ExamFlow Bot работает 24/7 с:

- ✅ Автоматическим перезапуском при сбоях
- ✅ Мониторингом состояния
- ✅ Логированием всех событий
- ✅ Уведомлениями о проблемах
- ✅ Масштабированием под нагрузку

**Бот готов обслуживать пользователей круглосуточно!** 🚀

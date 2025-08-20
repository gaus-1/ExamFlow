# 🚀 Система Keep-Alive для ExamFlow

## 📋 **Описание**

Система автоматически предотвращает "засыпание" PostgreSQL базы данных и сайта на Render.

## ⚙️ **Как это работает**

### **База данных (PostgreSQL)**
- **Интервал:** каждые 5 минут (300 секунд)
- **Действие:** Выполняет `SELECT 1` для поддержания соединения
- **Результат:** База никогда не засыпает

### **Сайт (examflow.ru)**
- **Интервал:** каждые 10 минут (600 секунд)  
- **Действие:** Делает HTTP-запрос к главной странице
- **Результат:** Сайт остается активным

## 🛠️ **Команды**

### **Автоматический запуск (рекомендуется)**
```bash
# Запускает все keep-alive автоматически
python manage.py start_keepalive --daemon
```

### **Ручной запуск**
```bash
# Только база данных
python manage.py keep_db_alive --continuous --interval 300

# Только сайт  
python manage.py keep_site_alive --continuous --interval 600

# Все вместе
python manage.py start_keepalive
```

### **Проверка статуса**
```bash
# Проверить базу один раз
python manage.py keep_db_alive

# Проверить сайт один раз
python manage.py keep_site_alive
```

## 🔧 **Настройка на Render**

В `render.yaml` уже настроено:
```yaml
startCommand: |
  python manage.py migrate --noinput
  python manage.py reload_bot_data --force
  python manage.py start_keepalive --daemon --db-interval 300 --site-interval 600
  gunicorn examflow_project.wsgi:application
```

## 📊 **Логирование**

Все действия логируются:
- ✅ Успешные проверки
- ❌ Ошибки соединения
- 🔄 Переподключения
- ⏰ Таймауты

## 🚨 **Устранение проблем**

### **База не отвечает**
```bash
python manage.py keep_db_alive --interval 60
```

### **Сайт не отвечает**
```bash
python manage.py keep_site_alive --interval 300
```

### **Перезапуск всех keep-alive**
```bash
python manage.py start_keepalive --daemon
```

## 💡 **Преимущества**

1. **Автоматически** - не требует ручного вмешательства
2. **Надежно** - работает 24/7
3. **Эффективно** - минимальное потребление ресурсов
4. **Логируется** - полная история всех проверок
5. **Восстанавливается** - автоматические переподключения

## 🎯 **Результат**

- ✅ **PostgreSQL** никогда не засыпает
- ✅ **Сайт** всегда доступен
- ✅ **Бот** работает стабильно
- ✅ **Пользователи** не ждут загрузки

---

**Система работает автоматически после деплоя на Render!** 🚀

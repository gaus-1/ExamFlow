# 🚀 БЫСТРЫЙ СТАРТ: ФОКУСИРОВКА НА МАТЕМАТИКЕ И РУССКОМ ЯЗЫКЕ

## ⚡ БЫСТРЫЙ ЗАПУСК (5 минут)

### 1. **Применить миграции**
```bash
python manage.py makemigrations
python manage.py migrate
```

### 2. **Инициализировать предметы**
```bash
python manage.py init_focused_subjects --clear --load-data
```

### 3. **Запустить сервер**
```bash
python manage.py runserver
```

### 4. **Проверить результат**
- Откройте http://localhost:8000/subjects/
- Должны отображаться только математика и русский язык
- Проверьте поиск и ИИ-помощника

## 🔧 ДОПОЛНИТЕЛЬНАЯ НАСТРОЙКА

### **Мониторинг ФИПИ**
```bash
# Проверить обновления
python manage.py monitor_fipi --check

# Показать статистику
python manage.py monitor_fipi --stats

# Запустить непрерывный мониторинг
python manage.py monitor_fipi --continuous
```

### **Тестирование**
```bash
# Запустить все тесты
python manage.py test tests.test_math_russian_focus

# Запустить конкретный тест
python manage.py test tests.test_math_russian_focus.MathRussianFocusTestCase
```

## 📊 ПРОВЕРКА РЕЗУЛЬТАТА

### **Что должно работать:**
- ✅ Только 5 предметов (3 математики + 2 русского языка)
- ✅ Красивые карточки с иконками
- ✅ Фокусированный поиск
- ✅ ИИ отвечает подробно по профильным предметам
- ✅ ИИ перенаправляет с других предметов
- ✅ Мобильная адаптивность

### **Что НЕ должно отображаться:**
- ❌ Физика, Химия, Биология
- ❌ История, География, Литература
- ❌ Информатика, Обществознание
- ❌ Иностранные языки

## 🎯 ОСНОВНЫЕ ФАЙЛЫ

### **Новые файлы:**
- `MATH_RUSSIAN_FOCUS_PLAN.md` - Детальный план
- `MATH_RUSSIAN_FOCUS_IMPLEMENTATION.md` - Отчет о реализации
- `core/migrations/0001_focus_math_russian.py` - Миграция
- `learning/focused_views.py` - Фокусированные представления
- `templates/learning/focused_subjects.html` - Шаблон предметов
- `core/ai/priority_manager.py` - Система приоритетов ИИ
- `core/fipi_monitor.py` - Мониторинг ФИПИ
- `tests/test_math_russian_focus.py` - Тесты

### **Измененные файлы:**
- `learning/models.py` - Обновлена модель Subject
- `learning/urls.py` - Добавлены новые маршруты
- `core/management/commands/` - Новые команды

## 🚨 ВОЗМОЖНЫЕ ПРОБЛЕМЫ

### **Ошибка миграции:**
```bash
# Если есть конфликты
python manage.py migrate --fake-initial
python manage.py migrate
```

### **Ошибка импорта:**
```bash
# Установить зависимости
pip install -r requirements.txt
```

### **Ошибка тестов:**
```bash
# Создать тестовую базу
python manage.py test --keepdb
```

## 📞 ПОДДЕРЖКА

### **Логи:**
- Проверьте `logs/` директорию
- Используйте `python manage.py shell` для отладки

### **База данных:**
- Проверьте миграции: `python manage.py showmigrations`
- Сбросить: `python manage.py flush`

### **Статистика:**
```python
# В Django shell
from learning.models import Subject
Subject.objects.filter(is_primary=True).count()  # Должно быть 5
Subject.objects.filter(is_archived=True).count()  # Должно быть 9
```

---

## 🎉 ГОТОВО!

**ExamFlow теперь сфокусирован на математике и русском языке!**

- **5 предметов** вместо 14
- **Специализированный ИИ**
- **Автоматический мониторинг ФИПИ**
- **Красивый адаптивный дизайн**

**Удачи в подготовке к экзаменам! 🚀📐📝**

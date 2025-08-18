# 🔥 ЗАПУСК ПАРСИНГА МАТЕРИАЛОВ ФИПИ

## 🚀 БЫСТРЫЙ СТАРТ

### 1. Зайти в Render Console
- Открыть https://dashboard.render.com
- Выбрать сервис ExamFlow
- Нажать **"Shell"** или **"Console"**

### 2. Запустить полный парсинг
```bash
python manage.py parse_all_fipi --with-voices
```

**ИЛИ быстрый парсинг (только основные предметы):**
```bash
python manage.py parse_all_fipi --quick --with-voices
```

### 3. Настроить webhook бота
```bash
python manage.py setup_webhook set
```

## 📋 ДОСТУПНЫЕ КОМАНДЫ

### 🔥 Полный парсинг (все предметы)
```bash
python manage.py parse_all_fipi
```
**Загружает:** математика, физика, химия, биология, история, обществознание, русский язык, информатика, литература, география, английский язык

### ⚡ Быстрый парсинг (основные предметы)
```bash
python manage.py parse_all_fipi --quick
```
**Загружает:** математика, физика, русский язык

### 🎤 С голосовыми подсказками
```bash
python manage.py parse_all_fipi --with-voices
```
**Дополнительно:** генерирует аудио файлы для заданий

### 🎯 Отдельные предметы
```bash
python manage.py load_fipi_data --subjects математика физика
python manage.py load_fipi_data --subjects биология химия история
python manage.py load_fipi_data --subjects русский_язык информатика
```

## 📊 ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ

### ✅ Успешный парсинг покажет:
```
🎉 ПАРСИНГ ЗАВЕРШЕН УСПЕШНО!
📚 Всего предметов: 8-12
📝 Всего заданий: 100-500+
✨ Новых предметов: +X
🎯 Новых заданий: +Y
🌐 Материалы ФИПИ загружены на сайт
```

### 📈 Статистика по группам:
- **Группа 1**: математика, физика, химия → ~50-150 заданий
- **Группа 2**: биология, история, обществознание → ~40-120 заданий  
- **Группа 3**: русский язык, информатика, литература → ~30-100 заданий
- **Группа 4**: география, английский язык → ~20-80 заданий

## 🐛 РЕШЕНИЕ ПРОБЛЕМ

### ❌ Ошибка "No module named 'django'"
```bash
pip install -r requirements.txt
```

### ❌ Ошибка подключения к БД
```bash
python manage.py migrate
```

### ❌ Таймаут при парсинге
Используйте поэтапный подход:
```bash
python manage.py load_fipi_data --subjects математика
python manage.py load_fipi_data --subjects физика
python manage.py load_fipi_data --subjects химия
```

### ❌ Нет новых данных
```bash
python manage.py load_fipi_data --subjects математика --force
```

## 🔄 АВТОМАТИЧЕСКОЕ ОБНОВЛЕНИЕ

### Настройка периодических обновлений:
```bash
python manage.py auto_update start --daemon
```

### Проверка статуса:
```bash
python manage.py auto_update status
```

## 📱 ПРОВЕРКА РЕЗУЛЬТАТОВ

### 1. Проверить сайт:
- Открыть https://examflow.ru
- Убедиться, что предметы загружены
- Проверить количество заданий в каждом предмете

### 2. Проверить бота:
- Нажать кнопку "Telegram Бот" на сайте
- В боте выполнить `/start`
- Проверить меню "📚 Выбрать предмет"
- Убедиться, что задания загружаются

### 3. Проверить базу данных:
```bash
python manage.py shell -c "
from core.models import Subject, Task
print(f'Предметов: {Subject.objects.count()}')
print(f'Заданий: {Task.objects.count()}')
for subject in Subject.objects.all():
    tasks_count = Task.objects.filter(subject=subject).count()
    print(f'{subject.name}: {tasks_count} заданий')
"
```

## ⏱️ ВРЕМЯ ВЫПОЛНЕНИЯ

- **Быстрый парсинг**: 2-5 минут
- **Полный парсинг**: 10-30 минут  
- **С голосовыми подсказками**: +5-15 минут

## 🎯 ФИНАЛЬНАЯ ПРОВЕРКА

После успешного парсинга:

1. ✅ Сайт показывает все предметы
2. ✅ В каждом предмете есть задания
3. ✅ Бот отвечает на команды
4. ✅ Кнопки в боте работают
5. ✅ Webhook настроен
6. ✅ Голосовые подсказки работают (если включены)

**🎉 ГОТОВО! Материалы ФИПИ загружены на сайт!**

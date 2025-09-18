# 🎯 ПЛАН ФОКУСИРОВКИ EXAMFLOW НА МАТЕМАТИКЕ И РУССКОМ ЯЗЫКЕ

## 📋 ОБЗОР ПРОЕКТА

Полная фокусировка ExamFlow на двух ключевых предметах: **Математика** (профильная/непрофильная) и **Русский язык** для ОГЭ/ЕГЭ с сохранением текущего стиля, наполнения и архитектуры проекта.

## 🎯 ЦЕЛЕВЫЕ ПРЕДМЕТЫ

### 1. **МАТЕМАТИКА**
- **Профильная математика (ЕГЭ)**: Задания 1-19 с полными решениями
- **Непрофильная математика (ЕГЭ)**: Задания 1-20 с пошаговыми объяснениями  
- **Математика (ОГЭ)**: Задания 1-26 с детальными разборами

### 2. **РУССКИЙ ЯЗЫК**
- **Русский язык (ЕГЭ)**: Все типы сочинений, грамматические нормы
- **Русский язык (ОГЭ)**: Изложение, сочинение, тестовые задания

## 🗂️ ЭТАП 1: АНАЛИЗ И ПОДГОТОВКА

### 1.1 Текущая структура предметов
```python
# Текущие предметы в системе:
subjects = [
    'Математика', 'Русский язык', 'Физика', 'Химия', 'Биология', 
    'История', 'География', 'Литература', 'Информатика', 
    'Обществознание', 'Английский язык', 'Немецкий язык', 
    'Французский язык', 'Испанский язык'
]

# Целевые предметы:
target_subjects = ['Математика', 'Русский язык']
```

### 1.2 План удаления лишних предметов
1. **Создать миграцию** для архивации ненужных предметов
2. **Обновить интерфейс** - убрать карточки предметов
3. **Модифицировать навигацию** - оставить только целевые разделы
4. **Обновить поиск** - сфокусировать на математике и русском

## 🎨 ЭТАП 2: ОБНОВЛЕНИЕ ИНТЕРФЕЙСА

### 2.1 Главная страница
```html
<!-- Обновленная секция предметов -->
<div class="subjects-section">
  <div class="subjects-grid grid grid-cols-1 md:grid-cols-2 gap-8">
    <!-- Математика -->
    <div class="subject-card math-card">
      <div class="subject-header">
        <div class="subject-icon">📐</div>
        <h3>Математика</h3>
      </div>
      <div class="subject-variants">
        <div class="variant">Профильная (ЕГЭ)</div>
        <div class="variant">Непрофильная (ЕГЭ)</div>
        <div class="variant">ОГЭ (9 класс)</div>
      </div>
    </div>
    
    <!-- Русский язык -->
    <div class="subject-card russian-card">
      <div class="subject-header">
        <div class="subject-icon">📝</div>
        <h3>Русский язык</h3>
      </div>
      <div class="subject-variants">
        <div class="variant">ЕГЭ (11 класс)</div>
        <div class="variant">ОГЭ (9 класс)</div>
      </div>
    </div>
  </div>
</div>
```

### 2.2 Навигация
- Убрать выпадающий список предметов
- Оставить только "Математика" и "Русский язык"
- Добавить подразделы по типам экзаменов

## 🗄️ ЭТАП 3: ОБНОВЛЕНИЕ БАЗЫ ДАННЫХ

### 3.1 Миграция предметов
```python
# core/migrations/XXXX_focus_math_russian.py
from django.db import migrations

def archive_unused_subjects(apps, schema_editor):
    Subject = apps.get_model('learning', 'Subject')
    
    # Архивируем ненужные предметы
    unused_subjects = [
        'Физика', 'Химия', 'Биология', 'История', 'География',
        'Литература', 'Информатика', 'Обществознание',
        'Английский язык', 'Немецкий язык', 'Французский язык', 'Испанский язык'
    ]
    
    for subject_name in unused_subjects:
        Subject.objects.filter(name=subject_name).update(is_archived=True)

def create_math_variants(apps, schema_editor):
    Subject = apps.get_model('learning', 'Subject')
    
    # Создаем варианты математики
    math_variants = [
        {'name': 'Математика (профильная)', 'code': 'math_prof', 'exam_type': 'ege'},
        {'name': 'Математика (непрофильная)', 'code': 'math_base', 'exam_type': 'ege'},
        {'name': 'Математика (ОГЭ)', 'code': 'math_oge', 'exam_type': 'oge'},
    ]
    
    for variant in math_variants:
        Subject.objects.get_or_create(
            name=variant['name'],
            code=variant['code'],
            exam_type=variant['exam_type']
        )

def create_russian_variants(apps, schema_editor):
    Subject = apps.get_model('learning', 'Subject')
    
    # Создаем варианты русского языка
    russian_variants = [
        {'name': 'Русский язык (ЕГЭ)', 'code': 'russian_ege', 'exam_type': 'ege'},
        {'name': 'Русский язык (ОГЭ)', 'code': 'russian_oge', 'exam_type': 'oge'},
    ]
    
    for variant in russian_variants:
        Subject.objects.get_or_create(
            name=variant['name'],
            code=variant['code'],
            exam_type=variant['exam_type']
        )
```

### 3.2 Обновление моделей
```python
# Добавить поле архивации в модель Subject
class Subject(models.Model):
    # ... существующие поля ...
    is_archived = models.BooleanField(default=False, verbose_name="Архивирован")
    is_primary = models.BooleanField(default=False, verbose_name="Основной предмет")
    
    class Meta:
        verbose_name = "Предмет"
        verbose_name_plural = "Предметы"
        ordering = ['is_primary', 'name']
```

## 📚 ЭТАП 4: НАПОЛНЕНИЕ БАЗЫ ДАННЫХ

### 4.1 Структура заданий по математике

#### Профильная математика (ЕГЭ)
```python
math_prof_topics = [
    {
        'name': 'Алгебра',
        'tasks': [
            {'number': 1, 'type': 'Простейшие уравнения', 'difficulty': 'easy'},
            {'number': 2, 'type': 'Стереометрия', 'difficulty': 'easy'},
            {'number': 3, 'type': 'Планиметрия', 'difficulty': 'easy'},
            {'number': 4, 'type': 'Теория вероятностей', 'difficulty': 'easy'},
            {'number': 5, 'type': 'Простейшие уравнения', 'difficulty': 'easy'},
            {'number': 6, 'type': 'Планиметрия', 'difficulty': 'medium'},
            {'number': 7, 'type': 'Производная', 'difficulty': 'medium'},
            {'number': 8, 'type': 'Стереометрия', 'difficulty': 'medium'},
            {'number': 9, 'type': 'Вычисления', 'difficulty': 'easy'},
            {'number': 10, 'type': 'Теория вероятностей', 'difficulty': 'medium'},
            {'number': 11, 'type': 'Стереометрия', 'difficulty': 'hard'},
            {'number': 12, 'type': 'Производная', 'difficulty': 'hard'},
            {'number': 13, 'type': 'Уравнения', 'difficulty': 'hard'},
            {'number': 14, 'type': 'Стереометрия', 'difficulty': 'hard'},
            {'number': 15, 'type': 'Неравенства', 'difficulty': 'hard'},
            {'number': 16, 'type': 'Планиметрия', 'difficulty': 'hard'},
            {'number': 17, 'type': 'Экономические задачи', 'difficulty': 'hard'},
            {'number': 18, 'type': 'Параметры', 'difficulty': 'hard'},
            {'number': 19, 'type': 'Числа и их свойства', 'difficulty': 'hard'},
        ]
    }
]
```

#### Русский язык (ЕГЭ)
```python
russian_ege_topics = [
    {
        'name': 'Сочинение',
        'subtopics': [
            'Проблема и комментарий',
            'Позиция автора',
            'Собственная позиция',
            'Аргументы',
            'Композиция',
            'Речевое оформление'
        ]
    },
    {
        'name': 'Грамматические нормы',
        'subtopics': [
            'Орфография',
            'Пунктуация',
            'Лексические нормы',
            'Синтаксические нормы',
            'Морфологические нормы'
        ]
    },
    {
        'name': 'Тестовые задания',
        'subtopics': [
            'Средства выразительности',
            'Типы речи',
            'Стили речи',
            'Синтаксический анализ',
            'Морфологический анализ'
        ]
    }
]
```

### 4.2 Источники данных
```python
# Приоритетные источники для наполнения
data_sources = {
    'mathematics': {
        'fipi': 'https://fipi.ru/ege/demoversii-specifikacii-kodifikatory',
        'reshu_ege': 'https://ege.sdamgia.ru/matematika',
        'foxford': 'https://foxford.ru/courses/mathematics',
        'yandex_tutor': 'https://yandex.ru/tutor/subject/?subject_id=1'
    },
    'russian': {
        'fipi': 'https://fipi.ru/ege/demoversii-specifikacii-kodifikatory',
        'reshu_ege': 'https://ege.sdamgia.ru/russkiy',
        'foxford': 'https://foxford.ru/courses/russian',
        'yandex_tutor': 'https://yandex.ru/tutor/subject/?subject_id=2'
    }
}
```

## 🤖 ЭТАП 5: НАСТРОЙКА ИИ-ПОМОЩНИКА

### 5.1 Приоритеты ответов
```python
# core/ai/priorities.py
class AIPriorityManager:
    def __init__(self):
        self.priority_subjects = ['Математика', 'Русский язык']
        self.secondary_subjects = ['Физика', 'Химия', 'Биология', 'История']
    
    def get_response_priority(self, subject, question_type):
        if subject in self.priority_subjects:
            return {
                'depth': 'detailed',
                'examples': True,
                'step_by_step': True,
                'video_links': True,
                'fipi_references': True
            }
        else:
            return {
                'depth': 'brief',
                'redirect': True,
                'message': 'Сейчас я специализируюсь на математике и русском языке. Хотите перейти к этим предметам?'
            }
```

### 5.2 Специализированные промпты
```python
# Промпты для математики
MATH_PROMPTS = {
    'profile_ege': """
    Ты эксперт по профильной математике ЕГЭ. 
    Предоставляй подробные решения с пошаговыми объяснениями.
    Включай альтернативные методы решения.
    Ссылайся на соответствующие темы из кодификатора ФИПИ.
    """,
    
    'base_ege': """
    Ты эксперт по базовой математике ЕГЭ.
    Объясняй простым языком с примерами.
    Показывай типичные ошибки и как их избежать.
    """,
    
    'oge': """
    Ты эксперт по математике ОГЭ.
    Адаптируй объяснения для 9 класса.
    Используй наглядные примеры и схемы.
    """
}

# Промпты для русского языка
RUSSIAN_PROMPTS = {
    'ege': """
    Ты эксперт по русскому языку ЕГЭ.
    Помогай с сочинениями, грамматическими нормами.
    Показывай примеры из классической литературы.
    Объясняй критерии оценивания.
    """,
    
    'oge': """
    Ты эксперт по русскому языку ОГЭ.
    Помогай с изложением, сочинением, тестовыми заданиями.
    Адаптируй для 9 класса.
    """
}
```

## 🔄 ЭТАП 6: ИНТЕГРАЦИЯ С ФИПИ

### 6.1 Автоматическое отслеживание изменений
```python
# core/fipi_monitor.py
class FIPIMonitor:
    def __init__(self):
        self.check_interval = 3600  # 1 час
        self.subjects = ['Математика', 'Русский язык']
    
    def check_for_updates(self):
        """Проверяет обновления на ФИПИ"""
        for subject in self.subjects:
            self.check_subject_updates(subject)
    
    def check_subject_updates(self, subject):
        """Проверяет обновления по конкретному предмету"""
        # Проверяем демо-варианты
        demo_updates = self.check_demo_variants(subject)
        
        # Проверяем открытый банк
        bank_updates = self.check_open_bank(subject)
        
        # Проверяем спецификации
        spec_updates = self.check_specifications(subject)
        
        if any([demo_updates, bank_updates, spec_updates]):
            self.notify_admin(subject, {
                'demo': demo_updates,
                'bank': bank_updates,
                'spec': spec_updates
            })
    
    def notify_admin(self, subject, updates):
        """Уведомляет администратора об обновлениях"""
        # Отправка в Telegram
        # Отправка email
        # Логирование
        pass
```

### 6.2 Система уведомлений
```python
# core/notifications.py
class UpdateNotificationSystem:
    def __init__(self):
        self.telegram_bot = TelegramBot()
        self.email_service = EmailService()
    
    def notify_admin(self, subject, update_type, details):
        message = f"""
        🔄 ОБНОВЛЕНИЕ ФИПИ
        
        Предмет: {subject}
        Тип: {update_type}
        Детали: {details}
        
        Время: {timezone.now()}
        """
        
        # Отправка в Telegram
        self.telegram_bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=message
        )
        
        # Отправка email
        self.email_service.send(
            to=ADMIN_EMAIL,
            subject=f"Обновление ФИПИ: {subject}",
            body=message
        )
```

## 🧪 ЭТАП 7: ТЕСТИРОВАНИЕ

### 7.1 Тест-кейсы
```python
# tests/test_math_russian_focus.py
class TestMathRussianFocus:
    def test_subjects_filtering(self):
        """Тест фильтрации предметов"""
        response = self.client.get('/subjects/')
        self.assertContains(response, 'Математика')
        self.assertContains(response, 'Русский язык')
        self.assertNotContains(response, 'Физика')
        self.assertNotContains(response, 'Химия')
    
    def test_ai_priorities(self):
        """Тест приоритетов ИИ"""
        # Тест математики
        math_response = self.ai_service.ask_question(
            "Как решить квадратное уравнение?",
            subject="Математика"
        )
        self.assertTrue(len(math_response) > 500)  # Подробный ответ
        
        # Тест других предметов
        physics_response = self.ai_service.ask_question(
            "Что такое сила?",
            subject="Физика"
        )
        self.assertIn("специализируюсь на математике", physics_response)
    
    def test_fipi_integration(self):
        """Тест интеграции с ФИПИ"""
        monitor = FIPIMonitor()
        updates = monitor.check_for_updates()
        self.assertIsInstance(updates, dict)
```

### 7.2 Проверка производительности
```python
def test_performance():
    """Тест производительности после изменений"""
    # Время загрузки главной страницы
    start_time = time.time()
    response = client.get('/')
    load_time = time.time() - start_time
    assert load_time < 2.0  # Менее 2 секунд
    
    # Время поиска по математике
    start_time = time.time()
    response = client.get('/search/?q=квадратное уравнение')
    search_time = time.time() - start_time
    assert search_time < 1.0  # Менее 1 секунды
```

## 📊 ЭТАП 8: МОНИТОРИНГ И АНАЛИТИКА

### 8.1 Метрики фокусировки
```python
# core/analytics/focus_metrics.py
class FocusMetrics:
    def __init__(self):
        self.target_subjects = ['Математика', 'Русский язык']
    
    def get_subject_usage_stats(self):
        """Статистика использования предметов"""
        return {
            'math_requests': self.count_requests('Математика'),
            'russian_requests': self.count_requests('Русский язык'),
            'other_requests': self.count_other_requests(),
            'focus_ratio': self.calculate_focus_ratio()
        }
    
    def get_ai_effectiveness(self):
        """Эффективность ИИ по предметам"""
        return {
            'math_satisfaction': self.get_satisfaction_rate('Математика'),
            'russian_satisfaction': self.get_satisfaction_rate('Русский язык'),
            'redirect_success': self.get_redirect_success_rate()
        }
```

## 🚀 ПЛАН РЕАЛИЗАЦИИ

### Неделя 1: Подготовка и миграция
- [ ] Создать миграции для архивации предметов
- [ ] Обновить модели данных
- [ ] Протестировать миграции на тестовой базе

### Неделя 2: Обновление интерфейса
- [ ] Модифицировать главную страницу
- [ ] Обновить навигацию
- [ ] Адаптировать мобильную версию

### Неделя 3: Настройка ИИ
- [ ] Реализовать систему приоритетов
- [ ] Создать специализированные промпты
- [ ] Протестировать ответы ИИ

### Неделя 4: Интеграция с ФИПИ
- [ ] Настроить мониторинг изменений
- [ ] Реализовать систему уведомлений
- [ ] Протестировать автоматические обновления

### Неделя 5: Наполнение и тестирование
- [ ] Загрузить данные по математике и русскому
- [ ] Провести полное тестирование
- [ ] Оптимизировать производительность

## ✅ ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ

1. **Фокус на двух предметах** - 100% контента по математике и русскому
2. **Улучшенное качество** - подробные ответы ИИ по профильным предметам
3. **Актуальность данных** - автоматические обновления с ФИПИ
4. **Высокая производительность** - быстрая загрузка и поиск
5. **Удобный интерфейс** - интуитивная навигация по предметам

## 🔧 ТЕХНИЧЕСКИЕ ТРЕБОВАНИЯ

- **Обратимость изменений** - все изменения можно откатить
- **Сохранение данных** - пользовательский прогресс не теряется
- **SEO-совместимость** - URL структура остается прежней
- **Мобильная адаптация** - работа на всех устройствах
- **Бесплатные инструменты** - только open-source решения

---

**Система готова к фокусировке на математике и русском языке! 🎯**

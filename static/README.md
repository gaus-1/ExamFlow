# 🎨 ExamFlow 2.0 - Фронтенд структура

## 📁 Организация файлов

### CSS
```
static/css/
├── variables.css          # CSS переменные и дизайн-система
├── components.css         # Базовые компоненты
├── examflow-2.0.css       # Основные стили ExamFlow 2.0
├── components/            # Модульные CSS компоненты
│   └── buttons.css        # Стили кнопок
└── utilities/             # Утилитарные классы
```

### JavaScript
```
static/js/
├── main.js                # Главный модуль с основной логикой
├── core-functions.js      # Основные функции (legacy)
└── modules/               # Модульные JS компоненты
    ├── ai-learning.js     # AI система обучения
    ├── gamification.js    # Геймификация
    └── theme-manager.js   # Менеджер тем
```

## 🎯 Принципы архитектуры

### 1. **Модульность**
- Каждый компонент в отдельном файле
- Четкое разделение ответственности
- Легкое подключение/отключение модулей

### 2. **Современные стандарты**
- **CSS**: Variables, Flexbox, Grid, CSS-in-JS подход
- **JavaScript**: ES6+, модули, async/await
- **Адаптивность**: Mobile-first подход

### 3. **Производительность**
- Минимальный размер файлов
- Ленивая загрузка модулей
- Оптимизированные анимации

### 4. **Совместимость**
- Telegram Web App API
- Все современные браузеры
- Graceful degradation

## 🚀 Использование

### Подключение модулей
```html
<!-- Основной модуль -->
<script src="{% static 'js/main.js' %}"></script>

<!-- Дополнительные модули -->
<script src="{% static 'js/modules/ai-learning.js' %}"></script>
<script src="{% static 'js/modules/gamification.js' %}"></script>
```

### CSS переменные
```css
:root {
  --primary-color: #2563eb;
  --secondary-color: #1d4ed8;
  --spacing-4: 1rem;
  --radius-lg: 0.5rem;
}
```

### JavaScript API
```javascript
// Основные функции
ExamFlow.Utils.showNotification('Сообщение', 'success');
ExamFlow.Utils.navigate('/path', false);

// Менеджер тем
window.themeManager.setTheme('dark');

// Анимации
window.animationManager.animateElement(element);
```

## 📱 Адаптивность

### Breakpoints
- **Mobile**: < 768px
- **Tablet**: 768px - 1024px  
- **Desktop**: > 1024px

### Touch-friendly
- Минимальный размер кнопок: 44px
- Увеличенные отступы на мобильных
- Оптимизированные жесты

## 🎨 Дизайн-система

### Цвета
- **Primary**: #2563eb (синий)
- **Secondary**: #1d4ed8 (темно-синий)
- **Success**: #10b981 (зеленый)
- **Warning**: #f59e0b (оранжевый)
- **Error**: #ef4444 (красный)

### Типографика
- **Primary Font**: Inter (UI)
- **Heading Font**: Manrope (заголовки)
- **Sizes**: 12px - 48px (responsive)

### Отступы
- **Spacing Scale**: 0.25rem - 4rem
- **Consistent**: 8px grid system

## 🔧 Разработка

### Добавление нового модуля
1. Создать файл в `static/js/modules/`
2. Экспортировать класс/функции
3. Подключить в `base.html`
4. Инициализировать в `main.js`

### Добавление стилей
1. Создать файл в `static/css/components/`
2. Использовать CSS переменные
3. Добавить адаптивность
4. Подключить в `base.html`

## 📊 Производительность

### Оптимизации
- **CSS**: Минификация, критический CSS
- **JS**: Tree-shaking, lazy loading
- **Images**: WebP, responsive images
- **Fonts**: Preload, font-display: swap

### Метрики
- **First Paint**: < 1.5s
- **Interactive**: < 3s
- **Lighthouse Score**: > 90

## 🐛 Отладка

### Dev Tools
```javascript
// Включить debug режим
window.ExamFlow.DEBUG = true;

// Логи
console.log('ExamFlow:', window.ExamFlow);
```

### CSS Debug
```css
/* Добавить outline для отладки */
* { outline: 1px solid red; }
```

## 📝 Changelog

### v2.0.0
- ✅ Полный рефакторинг фронтенда
- ✅ Модульная архитектура
- ✅ Современные CSS/JS стандарты
- ✅ Удаление legacy кода
- ✅ Оптимизация производительности
- ✅ Telegram Web App совместимость

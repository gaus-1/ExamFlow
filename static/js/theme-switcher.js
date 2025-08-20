/**
 * МОДУЛЬ УПРАВЛЕНИЯ ДИЗАЙНАМИ EXAMFLOW
 * 
 * Функционал:
 * - Переключение между темами "Школьник" и "Взрослый"
 * - Сохранение выбора в localStorage
 * - Автоматическое применение темы при загрузке
 * - Анимации и уведомления
 * - Адаптивность для мобильных устройств
 */

class ThemeManager {
    constructor() {
        this.currentTheme = 'adult'; // Тема по умолчанию
        this.themes = ['school', 'adult'];
        this.themeNames = {
            'school': 'Школьник',
            'adult': 'Взрослый'
        };
        
        this.init();
    }
    
    /**
     * Инициализация менеджера тем
     */
    init() {
        // Создаем переключатель тем
        this.createThemeSwitcher();
        
        // Загружаем сохраненную тему
        this.loadSavedTheme();
        
        // Применяем тему к странице
        this.applyTheme(this.currentTheme);
        // Обновляем активное состояние кнопок при старте
        this.updateActiveButton(this.currentTheme);
        
        // Добавляем класс для плавных переходов
        document.documentElement.classList.add('theme-transition');
        
        console.log('ThemeManager: Инициализирован, текущая тема:', this.currentTheme);
    }
    
    /**
     * Создание HTML переключателя тем
     */
    createThemeSwitcher() {
        // Проверяем, не создан ли уже переключатель
        if (document.querySelector('.theme-switcher')) {
            return;
        }
        
        const switcherHTML = `
            <div class="theme-switcher" id="theme-switcher">
                <div class="theme-switcher-container">
                    <button class="theme-switcher-btn" data-theme="school" title="Дизайн для школьников">
                        <i class="fas fa-graduation-cap"></i> Школьник
                    </button>
                    <button class="theme-switcher-btn" data-theme="adult" title="Дизайн для взрослых">
                        <i class="fas fa-briefcase"></i> Взрослый
                    </button>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', switcherHTML);
        
        // Добавляем обработчики событий
        this.addEventListeners();
        
        console.log('ThemeManager: Переключатель тем создан');
    }
    
    /**
     * Добавление обработчиков событий
     */
    addEventListeners() {
        const switcher = document.getElementById('theme-switcher');
        if (!switcher) return;
        
        // Обработчики для кнопок
        switcher.addEventListener('click', (e) => {
            const btn = e.target.closest('.theme-switcher-btn');
            if (!btn) return;
            const theme = btn.dataset.theme;
            if (theme) this.switchTheme(theme);
        });
        
        // Обработчик для мобильных устройств
        if (window.innerWidth <= 768) {
            switcher.addEventListener('touchstart', (e) => {
                const btn = e.target.closest('.theme-switcher-btn');
                if (!btn) return;
                const theme = btn.dataset.theme;
                if (theme) this.switchTheme(theme);
            }, { passive: true });
        }
        
        console.log('ThemeManager: Обработчики событий добавлены');
    }
    
    /**
     * Загрузка сохраненной темы из localStorage
     */
    loadSavedTheme() {
        try {
            const savedTheme = localStorage.getItem('examflow_theme');
            if (savedTheme && this.themes.includes(savedTheme)) {
                this.currentTheme = savedTheme;
                console.log('ThemeManager: Загружена сохраненная тема:', savedTheme);
            } else {
                console.log('ThemeManager: Используется тема по умолчанию:', this.currentTheme);
            }
        } catch (error) {
            console.warn('ThemeManager: Ошибка загрузки темы из localStorage:', error);
        }
    }
    
    /**
     * Сохранение темы в localStorage
     */
    saveTheme(theme) {
        try {
            localStorage.setItem('examflow_theme', theme);
            console.log('ThemeManager: Тема сохранена в localStorage:', theme);
        } catch (error) {
            console.warn('ThemeManager: Ошибка сохранения темы в localStorage:', error);
        }
    }
    
    /**
     * Переключение на новую тему
     */
    switchTheme(newTheme) {
        if (!this.themes.includes(newTheme)) {
            console.warn('ThemeManager: Неизвестная тема:', newTheme);
            return;
        }
        
        if (newTheme === this.currentTheme) {
            console.log('ThemeManager: Тема уже активна:', newTheme);
            return;
        }
        
        console.log('ThemeManager: Переключение с', this.currentTheme, 'на', newTheme);
        
        // Применяем новую тему
        this.applyTheme(newTheme);
        
        // Обновляем текущую тему
        this.currentTheme = newTheme;
        
        // Сохраняем в localStorage
        this.saveTheme(newTheme);
        
        // Обновляем активную кнопку
        this.updateActiveButton(newTheme);
        
        // Показываем уведомление
        this.showNotification(newTheme);
        
        // Отправляем событие для других модулей
        this.dispatchThemeChangeEvent(newTheme);
    }
    
    /**
     * Применение темы к странице
     */
    applyTheme(theme) {
        // Устанавливаем атрибут data-theme на html элементе
        document.documentElement.setAttribute('data-theme', theme);
        
        // Обновляем мета-тег theme-color для PWA
        this.updateThemeColor(theme);
        
        console.log('ThemeManager: Тема применена:', theme);
    }
    
    /**
     * Обновление цвета темы в мета-тегах
     */
    updateThemeColor(theme) {
        let themeColor = '#00ff88'; // По умолчанию
        
        if (theme === 'school') {
            themeColor = '#8B5CF6'; // Фиолетовый для школьников
        } else if (theme === 'adult') {
            themeColor = '#1E40AF'; // Синий для взрослых
        }
        
        // Обновляем существующий мета-тег или создаем новый
        let metaThemeColor = document.querySelector('meta[name="theme-color"]');
        if (metaThemeColor) {
            metaThemeColor.setAttribute('content', themeColor);
        } else {
            metaThemeColor = document.createElement('meta');
            metaThemeColor.setAttribute('name', 'theme-color');
            metaThemeColor.setAttribute('content', themeColor);
            document.head.appendChild(metaThemeColor);
        }
    }
    
    /**
     * Обновление активной кнопки
     */
    updateActiveButton(activeTheme) {
        const buttons = document.querySelectorAll('.theme-switcher-btn');
        
        buttons.forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.theme === activeTheme) {
                btn.classList.add('active');
            }
        });
    }
    
    /**
     * Показ уведомления о смене темы
     */
    showNotification(theme) {
        // Удаляем существующие уведомления
        const existingNotification = document.querySelector('.theme-notification');
        if (existingNotification) {
            existingNotification.remove();
        }
        
        const themeName = this.themeNames[theme];
        const notificationHTML = `
            <div class="theme-notification" id="theme-notification">
                <div class="theme-notification-title">
                    <i class="fas fa-palette"></i> Тема изменена
                </div>
                <div class="theme-notification-text">
                    Активирована тема "${themeName}"
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', notificationHTML);
        
        const notification = document.getElementById('theme-notification');
        
        // Показываем уведомление
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);
        
        // Скрываем через 3 секунды
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 300);
        }, 3000);
        
        console.log('ThemeManager: Показано уведомление о смене темы на', themeName);
    }
    
    /**
     * Отправка события о смене темы
     */
    dispatchThemeChangeEvent(theme) {
        const event = new CustomEvent('themeChanged', {
            detail: {
                theme: theme,
                themeName: this.themeNames[theme],
                previousTheme: this.currentTheme
            }
        });
        
        document.dispatchEvent(event);
        console.log('ThemeManager: Событие themeChanged отправлено:', theme);
    }
    
    /**
     * Получение текущей темы
     */
    getCurrentTheme() {
        return this.currentTheme;
    }
    
    /**
     * Получение названия текущей темы
     */
    getCurrentThemeName() {
        return this.themeNames[this.currentTheme];
    }
    
    /**
     * Проверка, является ли тема школьной
     */
    isSchoolTheme() {
        return this.currentTheme === 'school';
    }
    
    /**
     * Проверка, является ли тема взрослой
     */
    isAdultTheme() {
        return this.currentTheme === 'adult';
    }
    
    /**
     * Принудительное обновление темы (для отладки)
     */
    refreshTheme() {
        this.applyTheme(this.currentTheme);
        console.log('ThemeManager: Тема обновлена:', this.currentTheme);
    }
}

// Инициализация при загрузке DOM
document.addEventListener('DOMContentLoaded', () => {
    // Создаем глобальный экземпляр менеджера тем
    window.themeManager = new ThemeManager();
    
    // Добавляем глобальные функции для совместимости
    window.switchTheme = (theme) => {
        if (window.themeManager) {
            window.themeManager.switchTheme(theme);
        }
    };
    
    window.getCurrentTheme = () => {
        if (window.themeManager) {
            return window.themeManager.getCurrentTheme();
        }
        return 'adult';
    };
    
    console.log('ThemeManager: DOM загружен, менеджер тем инициализирован');
});

// Инициализация при загрузке страницы (fallback)
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        if (!window.themeManager) {
            window.themeManager = new ThemeManager();
        }
    });
} else {
    // DOM уже загружен
    if (!window.themeManager) {
        window.themeManager = new ThemeManager();
    }
}

// Экспорт для модульных систем
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemeManager;
}

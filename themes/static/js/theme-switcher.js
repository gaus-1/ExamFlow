/**
 * ========================================
 * ПЕРЕКЛЮЧАТЕЛЬ ДИЗАЙНОВ EXAMFLOW
 * ========================================
 * 
 * Класс для управления переключением между дизайнами:
 * - "school" (Школьник) - яркий, игровой стиль
 * - "adult" (Взрослый) - профессиональный стиль
 */

class ThemeSwitcher {
    constructor() {
        this.currentTheme = 'school'; // Тема по умолчанию
        this.themes = {
            school: {
                name: 'Школьник',
                icon: '🎓',
                description: 'Яркий и игровой дизайн для учащихся 9-11 классов'
            },
            adult: {
                name: 'Взрослый', 
                icon: '👔',
                description: 'Профессиональный дизайн для родителей и учителей'
            }
        };
        
        this.init();
    }

    /**
     * Инициализация переключателя дизайнов
     */
    init() {
        this.setupThemeSwitcher();
        this.restoreTheme();
        this.addEventListeners();
        
        // Уведомляем о готовности
        console.log('🎨 Переключатель дизайнов инициализирован');
    }

    /**
     * Настройка HTML элементов переключателя
     */
    setupThemeSwitcher() {
        // Проверяем, что кнопки переключателя существуют
        const switcherButtons = document.querySelectorAll('.theme-switcher-btn');
        if (switcherButtons.length === 0) {
            console.warn('⚠️ Кнопки переключателя дизайнов не найдены');
            return;
        }
        
        // Добавляем атрибут data-theme к body
        document.body.setAttribute('data-theme', this.currentTheme);
        
        // Обновляем UI переключателя
        this.updateSwitcherUI(this.currentTheme);
    }

    /**
     * Восстановление сохраненной темы из localStorage
     */
    restoreTheme() {
        const savedTheme = localStorage.getItem('examflow_theme');
        if (savedTheme && this.themes[savedTheme]) {
            this.currentTheme = savedTheme;
        }
        this.applyTheme(this.currentTheme);
    }

    /**
     * Добавление обработчиков событий
     */
    addEventListeners() {
        // Обработчики для кнопок переключения
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('theme-switcher-btn')) {
                const theme = e.target.getAttribute('data-theme');
                if (theme && this.themes[theme]) {
                    this.toggleTheme(theme);
                }
            }
        });

        // Обработчик для изменения localStorage в других вкладках
        window.addEventListener('storage', (e) => {
            if (e.key === 'examflow_theme' && e.newValue) {
                this.switchTheme(e.newValue);
            }
        });
    }

    /**
     * Переключение темы с анимацией
     */
    toggleTheme(newTheme) {
        if (newTheme === this.currentTheme) return;
        
        this.animateThemeSwitch(() => {
            this.switchTheme(newTheme);
        });
    }

    /**
     * Анимация переключения темы
     */
    animateThemeSwitch(callback) {
        // Добавляем класс для анимации
        document.body.classList.add('theme-switching');
        
        // Небольшая задержка для плавности
        setTimeout(() => {
            callback();
            document.body.classList.remove('theme-switching');
        }, 150);
    }

    /**
     * Переключение на указанную тему
     */
    switchTheme(theme) {
        if (!this.themes[theme]) return;
        
        this.currentTheme = theme;
        this.applyTheme(theme);
        this.saveTheme(theme);
        this.updateSwitcherUI(theme);
        this.notifyThemeChange(theme);
        
        // Обновляем PWA тему
        this.updatePWATheme(theme);
    }

    /**
     * Применение темы к странице
     */
    applyTheme(theme) {
        // Устанавливаем атрибут data-theme
        document.body.setAttribute('data-theme', theme);
        
        // Обновляем CSS переменные
        this.updateCSSVariables(theme);
        
        // Обновляем мета-теги для PWA
        this.updateMetaTags(theme);
        
        console.log(`🎨 Применена тема: ${this.themes[theme].name}`);
    }

    /**
     * Обновление CSS переменных для темы
     */
    updateCSSVariables(theme) {
        const root = document.documentElement;
        
        if (theme === 'school') {
            // Школьная тема - яркие цвета
            root.style.setProperty('--accent-primary', '#22C55E');
            root.style.setProperty('--accent-secondary', '#3B82F6');
            root.style.setProperty('--accent-purple', '#8B5CF6');
            root.style.setProperty('--accent-orange', '#F97316');
            root.style.setProperty('--accent-neon', '#10B981');
        } else {
            // Взрослая тема - профессиональные цвета
            root.style.setProperty('--accent-primary', '#1E40AF');
            root.style.setProperty('--accent-secondary', '#475569');
            root.style.setProperty('--accent-info', '#0891B2');
            root.style.setProperty('--accent-success', '#059669');
        }
    }

    /**
     * Обновление мета-тегов для PWA
     */
    updateMetaTags(theme) {
        const themeColor = theme === 'school' ? '#22C55E' : '#1E40AF';
        
        // Обновляем цвет темы для PWA
        let themeColorMeta = document.querySelector('meta[name="theme-color"]');
        if (!themeColorMeta) {
            themeColorMeta = document.createElement('meta');
            themeColorMeta.name = 'theme-color';
            document.head.appendChild(themeColorMeta);
        }
        themeColorMeta.content = themeColor;
        
        // Обновляем цвет для Apple устройств
        let appleThemeColor = document.querySelector('meta[name="apple-mobile-web-app-status-bar-style"]');
        if (!appleThemeColor) {
            appleThemeColor = document.createElement('meta');
            appleThemeColor.name = 'apple-mobile-web-app-status-bar-style';
            document.head.appendChild(appleThemeColor);
        }
        appleThemeColor.content = theme === 'school' ? 'default' : 'black-translucent';
    }

    /**
     * Сохранение выбранной темы
     */
    saveTheme(theme) {
        localStorage.setItem('examflow_theme', theme);
        
        // Отправляем на сервер если пользователь авторизован
        this.saveThemeToServer(theme);
    }

    /**
     * Сохранение темы на сервере
     */
    async saveThemeToServer(theme) {
        try {
            const response = await fetch('/themes/api/switch/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ theme: theme })
            });
            
            if (response.ok) {
                console.log('✅ Тема сохранена на сервере');
            }
        } catch (error) {
            console.log('⚠️ Не удалось сохранить тему на сервере:', error);
        }
    }

    /**
     * Получение CSRF токена
     */
    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }

    /**
     * Обновление UI переключателя
     */
    updateSwitcherUI(theme) {
        // Обновляем активные состояния кнопок
        document.querySelectorAll('.theme-switcher-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.getAttribute('data-theme') === theme) {
                btn.classList.add('active');
            }
        });
        
        // Обновляем текст в заголовке если есть
        const themeIndicator = document.querySelector('.theme-indicator');
        if (themeIndicator) {
            themeIndicator.textContent = this.themes[theme].name;
            themeIndicator.innerHTML = `${this.themes[theme].icon} ${this.themes[theme].name}`;
        }
    }

    /**
     * Уведомление об изменении темы
     */
    notifyThemeChange(theme) {
        // Создаем кастомное событие
        const event = new CustomEvent('themeChanged', {
            detail: {
                theme: theme,
                themeInfo: this.themes[theme]
            }
        });
        
        document.dispatchEvent(event);
        
        // Показываем уведомление
        this.showThemeNotification(theme);
    }

    /**
     * Показ уведомления об изменении темы
     */
    showThemeNotification(theme) {
        const notification = document.createElement('div');
        notification.className = 'theme-notification';
        notification.innerHTML = `
            <div class="theme-notification-content">
                <span class="theme-notification-icon">${this.themes[theme].icon}</span>
                <span class="theme-notification-text">Дизайн изменен на "${this.themes[theme].name}"</span>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Анимация появления
        setTimeout(() => notification.classList.add('show'), 100);
        
        // Автоматическое скрытие
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    /**
     * Обновление темы для PWA
     */
    updatePWATheme(theme) {
        // Обновляем manifest если есть
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.ready.then(registration => {
                registration.postMessage({
                    type: 'THEME_CHANGED',
                    theme: theme
                });
            });
        }
    }

    /**
     * Получение текущей темы
     */
    getCurrentTheme() {
        return this.currentTheme;
    }

    /**
     * Установка темы (публичный метод)
     */
    setTheme(theme) {
        if (this.themes[theme]) {
            this.switchTheme(theme);
        }
    }
}

// Автоматическая инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    window.themeSwitcher = new ThemeSwitcher();
});

// Экспорт для использования в других модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemeSwitcher;
}

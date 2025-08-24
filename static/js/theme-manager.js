/**
 * 🎨 Менеджер тем и анимаций для ExamFlow
 * 
 * Функции:
 * - Автоматическое определение времени суток
 * - Адаптация под системные настройки
 * - Управление анимациями при скроллинге
 * - Сохранение предпочтений пользователя
 */

class ThemeManager {
    constructor() {
        this.currentTheme = 'light';
        this.currentTime = 'afternoon';
        this.userPreference = null;
        this.autoTheme = true;
        
        this.init();
    }
    
    init() {
        this.loadUserPreferences();
        this.detectSystemTheme();
        this.detectTimeOfDay();
        this.setupEventListeners();
        this.initScrollAnimations();
        this.applyTheme();
        this.updateThemeButton();
        
        console.log('🎨 ThemeManager инициализирован');
    }
    
    /**
     * Загружает предпочтения пользователя из localStorage
     */
    loadUserPreferences() {
        try {
            const saved = localStorage.getItem('examflow-theme');
            if (saved) {
                const prefs = JSON.parse(saved);
                this.userPreference = prefs.theme;
                this.autoTheme = prefs.autoTheme !== false;
            }
        } catch (e) {
            console.warn('Не удалось загрузить настройки темы:', e);
        }
    }
    
    /**
     * Сохраняет предпочтения пользователя
     */
    saveUserPreferences() {
        try {
            const prefs = {
                theme: this.currentTheme,
                autoTheme: this.autoTheme,
                timestamp: Date.now()
            };
            localStorage.setItem('examflow-theme', JSON.stringify(prefs));
        } catch (e) {
            console.warn('Не удалось сохранить настройки темы:', e);
        }
    }
    
    /**
     * Определяет системную тему (светлая/темная)
     */
    detectSystemTheme() {
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            this.systemTheme = mediaQuery.matches ? 'dark' : 'light';
            
            // Слушаем изменения системной темы
            mediaQuery.addEventListener('change', (e) => {
                this.systemTheme = e.matches ? 'dark' : 'light';
                if (this.autoTheme) {
                    this.applyTheme();
                }
            });
        }
    }
    
    /**
     * Определяет время суток
     */
    detectTimeOfDay() {
        const hour = new Date().getHours();
        
        if (hour >= 6 && hour < 12) {
            this.currentTime = 'morning';
        } else if (hour >= 12 && hour < 18) {
            this.currentTime = 'afternoon';
        } else if (hour >= 18 && hour < 22) {
            this.currentTime = 'evening';
        } else {
            this.currentTime = 'night';
        }
        
        // Обновляем время каждую минуту
        setInterval(() => {
            this.detectTimeOfDay();
            if (this.autoTheme) {
                this.applyTheme();
            }
        }, 60000);
    }
    
    /**
     * Применяет текущую тему
     */
    applyTheme() {
        const root = document.documentElement;
        
        // Убираем предыдущие атрибуты
        root.removeAttribute('data-theme');
        root.removeAttribute('data-time');
        
        // Применяем тему пользователя или системную
        if (this.userPreference && !this.autoTheme) {
            this.currentTheme = this.userPreference;
        } else if (this.autoTheme) {
            this.currentTheme = this.systemTheme || 'light';
        }
        
        // Применяем атрибуты
        root.setAttribute('data-theme', this.currentTheme);
        root.setAttribute('data-time', this.currentTime);
        
        // Обновляем мета-теги
        this.updateMetaTags();
        
        // Сохраняем настройки
        this.saveUserPreferences();
        
        console.log(`🎨 Применена тема: ${this.currentTheme}, время: ${this.currentTime}`);
    }
    
    /**
     * Обновляет мета-теги для PWA
     */
    updateMetaTags() {
        const themeColor = getComputedStyle(document.documentElement)
            .getPropertyValue('--primary-bg')
            .trim();
        
        let metaTheme = document.querySelector('meta[name="theme-color"]');
        if (!metaTheme) {
            metaTheme = document.createElement('meta');
            metaTheme.name = 'theme-color';
            document.head.appendChild(metaTheme);
        }
        metaTheme.content = themeColor;
    }
    
    /**
     * Переключает тему вручную
     */
    toggleTheme() {
        this.autoTheme = false;
        this.currentTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.applyTheme();
        
        // Показываем уведомление
        this.showThemeNotification();
    }
    
    /**
     * Включает автоматическое определение темы
     */
    enableAutoTheme() {
        this.autoTheme = true;
        this.applyTheme();
        
        // Показываем уведомление
        this.showNotification('Автоматическая тема включена', 'info');
    }
    
    /**
     * Показывает уведомление о смене темы
     */
    showThemeNotification() {
        const themeName = this.currentTheme === 'light' ? 'светлую' : 'темную';
        this.showNotification(`Переключено на ${themeName} тему`, 'success');
    }
    
    /**
     * Показывает уведомление
     */
    showNotification(message, type = 'info') {
        // Создаем элемент уведомления
        const notification = document.createElement('div');
        notification.className = `theme-notification theme-notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-icon">${this.getNotificationIcon(type)}</span>
                <span class="notification-text">${message}</span>
            </div>
        `;
        
        // Добавляем стили
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--card-bg);
            color: var(--primary-text);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 12px 16px;
            box-shadow: 0 4px 20px var(--shadow-color);
            z-index: 10000;
            transform: translateX(100%);
            transition: transform 0.3s var(--transition-timing);
            max-width: 300px;
        `;
        
        document.body.appendChild(notification);
        
        // Анимация появления
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        // Автоматическое скрытие
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
    
    /**
     * Возвращает иконку для типа уведомления
     */
    getNotificationIcon(type) {
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        return icons[type] || icons.info;
    }
    
    /**
     * Настраивает обработчики событий
     */
    setupEventListeners() {
        // Кнопка переключения темы
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => {
                this.toggleTheme();
                this.updateThemeButton();
            });
        }
        
        // Слушаем клавиши для быстрого переключения
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + T для переключения темы
            if ((e.ctrlKey || e.metaKey) && e.key === 't') {
                e.preventDefault();
                this.toggleTheme();
                this.updateThemeButton();
            }
            
            // Ctrl/Cmd + A для включения автотемы
            if ((e.ctrlKey || e.metaKey) && e.key === 'a') {
                e.preventDefault();
                this.enableAutoTheme();
            }
        });
        
        // Слушаем изменения видимости страницы
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.detectTimeOfDay();
                if (this.autoTheme) {
                    this.applyTheme();
                }
            }
        });
    }
    
    /**
     * Обновляет иконку кнопки темы
     */
    updateThemeButton() {
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            const icon = this.currentTheme === 'dark' ? '☀️' : '🌙';
            const title = this.currentTheme === 'dark' ? 'Переключить на светлую тему (Ctrl+T)' : 'Переключить на темную тему (Ctrl+T)';
            
            themeToggle.textContent = icon;
            themeToggle.title = title;
            themeToggle.setAttribute('data-theme', this.currentTheme);
        }
    }
    
    /**
     * Инициализирует анимации при скроллинге
     */
    initScrollAnimations() {
        this.observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('revealed');
                    
                    // Анимация для заголовков
                    if (entry.target.classList.contains('heading-animate')) {
                        this.animateHeading(entry.target);
                    }
                    
                    // Анимация для статистики
                    if (entry.target.classList.contains('stat-counter')) {
                        this.animateStatCounter(entry.target);
                    }
                    
                    // Анимация для прогресс-баров
                    if (entry.target.classList.contains('progress-bar')) {
                        this.animateProgressBar(entry.target);
                    }
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        });
        
        // Находим все элементы для анимации
        this.observeElements();
        
        // Слушаем изменения DOM
        this.setupMutationObserver();
    }
    
    /**
     * Наблюдает за элементами для анимации
     */
    observeElements() {
        const elements = document.querySelectorAll(`
            .text-reveal,
            .heading-animate,
            .stat-counter,
            .progress-bar,
            .card-hover
        `);
        
        elements.forEach(el => {
            this.observer.observe(el);
        });
    }
    
    /**
     * Настраивает наблюдатель за изменениями DOM
     */
    setupMutationObserver() {
        const observer = new MutationObserver((mutations) => {
            let shouldReobserve = false;
            
            mutations.forEach(mutation => {
                if (mutation.type === 'childList') {
                    shouldReobserve = true;
                }
            });
            
            if (shouldReobserve) {
                setTimeout(() => {
                    this.observeElements();
                }, 100);
            }
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
    
    /**
     * Анимирует заголовок по буквам
     */
    animateHeading(heading) {
        const text = heading.textContent;
        const letters = text.split('').map(letter => {
            const span = document.createElement('span');
            span.className = 'letter-animate';
            span.textContent = letter === ' ' ? '\u00A0' : letter;
            span.style.animationDelay = `${Math.random() * 0.5}s`;
            return span;
        });
        
        heading.innerHTML = '';
        letters.forEach(span => heading.appendChild(span));
    }
    
    /**
     * Анимирует счетчик статистики
     */
    animateStatCounter(counter) {
        const target = parseInt(counter.textContent) || 0;
        const duration = 2000;
        const step = target / (duration / 16);
        let current = 0;
        
        const timer = setInterval(() => {
            current += step;
            if (current >= target) {
                current = target;
                clearInterval(timer);
            }
            counter.textContent = Math.floor(current);
        }, 16);
    }
    
    /**
     * Анимирует прогресс-бар
     */
    animateProgressBar(progressBar) {
        const width = progressBar.getAttribute('data-progress') || '0';
        progressBar.style.setProperty('--progress-width', width + '%');
        progressBar.classList.add('animate');
    }
    
    /**
     * Получает текущую информацию о теме
     */
    getThemeInfo() {
        return {
            currentTheme: this.currentTheme,
            currentTime: this.currentTime,
            systemTheme: this.systemTheme,
            userPreference: this.userPreference,
            autoTheme: this.autoTheme
        };
    }
}

// Инициализируем менеджер тем при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    window.themeManager = new ThemeManager();
});

// Экспортируем для использования в других модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemeManager;
}

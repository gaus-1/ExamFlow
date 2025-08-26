/**
 * 🎨 Менеджер тем и анимаций для ExamFlow
 * Автоматическое переключение тем по времени суток (МСК)
 * Плавные анимации по аналогии с Superhuman.com
 */

class ThemeManager {
    constructor() {
        this.currentTheme = 'light';
        this.init();
    }

    init() {
        this.setupTheme();
        this.setupAnimations();
        this.setupAccordions();
        this.setupScrollAnimations();
        this.createThemeToggle();
    }

    /**
     * Настройка автоматического переключения тем
     */
    setupTheme() {
        // Определяем текущее время в МСК
        const now = new Date();
        const moscowTime = new Date(now.getTime() + (3 * 60 * 60 * 1000)); // +3 часа для МСК
        const hour = moscowTime.getHours();
        
        // С 9:00 до 21:00 - светлая тема, иначе - темная
        const shouldBeDark = hour < 9 || hour >= 21;
        
        // Применяем тему
        this.setTheme(shouldBeDark ? 'dark' : 'light');
        
        // Сохраняем в localStorage
        localStorage.setItem('examflow-theme', this.currentTheme);
        
        // Обновляем meta тег для цвета темы
        this.updateThemeColor();
        
        // Проверяем тему каждые 5 минут
        setInterval(() => this.checkTimeAndUpdateTheme(), 5 * 60 * 1000);
    }

    /**
     * Применение темы
     */
    setTheme(theme) {
        this.currentTheme = theme;
        document.documentElement.setAttribute('data-theme', theme);
        document.body.className = `theme-${theme}`;
        
        // Обновляем цвета для всех элементов
        this.updateThemeColors();
    }

    /**
     * Обновление цветов темы
     */
    updateThemeColors() {
        const root = document.documentElement;
        
        if (this.currentTheme === 'dark') {
            root.style.setProperty('--aesop-primary', '#ffffff');
            root.style.setProperty('--aesop-secondary', '#2a2a2a');
            root.style.setProperty('--aesop-accent', '#d4af37');
            root.style.setProperty('--aesop-text', '#e0e0e0');
            root.style.setProperty('--aesop-text-light', '#b0b0b0');
            root.style.setProperty('--aesop-border', '#404040');
            root.style.setProperty('--aesop-hover', '#353535');
            root.style.setProperty('--aesop-background', '#1a1a1a');
            root.style.setProperty('--aesop-card-bg', '#2c2c2c');
            root.style.setProperty('--aesop-shadow', '0 2px 8px rgba(0, 0, 0, 0.3)');
            root.style.setProperty('--aesop-shadow-hover', '0 4px 16px rgba(0, 0, 0, 0.4)');
        } else {
            root.style.setProperty('--aesop-primary', '#1a1a1a');
            root.style.setProperty('--aesop-secondary', '#f5f5f5');
            root.style.setProperty('--aesop-accent', '#8b7355');
            root.style.setProperty('--aesop-text', '#333333');
            root.style.setProperty('--aesop-text-light', '#666666');
            root.style.setProperty('--aesop-border', '#e0e0e0');
            root.style.setProperty('--aesop-hover', '#f8f8f8');
            root.style.setProperty('--aesop-background', '#faf7f0');
            root.style.setProperty('--aesop-card-bg', '#ffffff');
            root.style.setProperty('--aesop-shadow', '0 2px 8px rgba(0, 0, 0, 0.1)');
            root.style.setProperty('--aesop-shadow-hover', '0 4px 16px rgba(0, 0, 0, 0.15)');
        }
    }

    /**
     * Проверка времени и обновление темы
     */
    checkTimeAndUpdateTheme() {
        const now = new Date();
        const moscowTime = new Date(now.getTime() + (3 * 60 * 60 * 1000));
        const hour = moscowTime.getHours();
        
        const shouldBeDark = hour < 9 || hour >= 21;
        const newTheme = shouldBeDark ? 'dark' : 'light';
        
        if (newTheme !== this.currentTheme) {
            this.setTheme(newTheme);
            localStorage.setItem('examflow-theme', newTheme);
            this.updateThemeColor();
            
            // Показываем уведомление о смене темы
            this.showThemeChangeNotification(newTheme);
        }
    }

    /**
     * Обновление meta тега для цвета темы
     */
    updateThemeColor() {
        let metaThemeColor = document.querySelector('meta[name="theme-color"]');
        
        if (!metaThemeColor) {
            metaThemeColor = document.createElement('meta');
            metaThemeColor.name = 'theme-color';
            document.head.appendChild(metaThemeColor);
        }
        
        metaThemeColor.content = this.currentTheme === 'dark' ? '#1a1a1a' : '#faf7f0';
    }

    /**
     * Настройка анимаций появления элементов
     */
    setupAnimations() {
        // Анимация появления при загрузке страницы
        const animatedElements = document.querySelectorAll('.ai-chat-container, .fipi-tab, .accordion, .gamification');
        
        animatedElements.forEach((element, index) => {
            element.style.opacity = '0';
            element.style.transform = 'translateY(30px)';
            
            setTimeout(() => {
                element.style.transition = 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1)';
                element.style.opacity = '1';
                element.style.transform = 'translateY(0)';
            }, index * 200);
        });
    }

    /**
     * Настройка аккордеонов с плавными анимациями
     */
    setupAccordions() {
        const accordionItems = document.querySelectorAll('.accordion-item');
        
        accordionItems.forEach(item => {
            const header = item.querySelector('.accordion-header');
            const content = item.querySelector('.accordion-content');
            
            header.addEventListener('click', () => {
                const isActive = item.classList.contains('active');
                
                // Закрываем все аккордеоны
                accordionItems.forEach(otherItem => {
                    otherItem.classList.remove('active');
                    const otherContent = otherItem.querySelector('.accordion-content');
                    otherContent.style.maxHeight = '0';
                });
                
                // Открываем текущий, если он был закрыт
                if (!isActive) {
                    item.classList.add('active');
                    content.style.maxHeight = content.scrollHeight + 'px';
                    
                    // Плавная анимация содержимого
                    content.style.opacity = '0';
                    content.style.transform = 'translateY(-10px)';
                    
                    setTimeout(() => {
                        content.style.transition = 'all 0.3s ease';
                        content.style.opacity = '1';
                        content.style.transform = 'translateY(0)';
                    }, 100);
                }
            });
        });
    }

    /**
     * Настройка анимаций при скролле
     */
    setupScrollAnimations() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                    observer.unobserve(entry.target);
                }
            });
        }, observerOptions);

        // Наблюдаем за элементами для анимации при скролле
        const scrollElements = document.querySelectorAll('.subject-card, .progress-item, .query-example');
        scrollElements.forEach(el => observer.observe(el));
    }

    /**
     * Создание кнопки переключения темы
     */
    createThemeToggle() {
        const navbarUser = document.querySelector('.navbar-user');
        
        if (navbarUser && !document.querySelector('.theme-toggle')) {
            const themeToggle = document.createElement('button');
            themeToggle.className = 'theme-toggle';
            themeToggle.innerHTML = this.currentTheme === 'dark' ? '☀️' : '🌙';
            themeToggle.title = 'Переключить тему';
            
            themeToggle.addEventListener('click', () => {
                const newTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
                this.setTheme(newTheme);
                localStorage.setItem('examflow-theme', newTheme);
                this.updateThemeColor();
                
                // Обновляем иконку
                themeToggle.innerHTML = newTheme === 'dark' ? '☀️' : '🌙';
                
                // Плавная анимация переключения
                themeToggle.style.transform = 'scale(1.2) rotate(180deg)';
                setTimeout(() => {
                    themeToggle.style.transform = 'scale(1) rotate(0deg)';
                }, 300);
            });
            
            navbarUser.appendChild(themeToggle);
        }
    }

    /**
     * Показ уведомления о смене темы
     */
    showThemeChangeNotification(theme) {
        const message = theme === 'dark' ? 'Переключено на темную тему' : 'Переключено на светлую тему';
        const icon = theme === 'dark' ? '🌙' : '☀️';
        
        this.showNotification(`${icon} ${message}`, 'info');
    }

    /**
     * Показ уведомлений
     */
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = message;
        
        // Стили для уведомления
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--aesop-secondary);
            color: var(--aesop-text);
            border: 1px solid var(--aesop-border);
            border-radius: 8px;
            padding: 12px 16px;
            box-shadow: var(--aesop-shadow);
            z-index: 10000;
            transform: translateX(100%);
            transition: transform 0.3s ease;
            max-width: 300px;
            font-family: 'Georgia', 'Times New Roman', serif;
            font-size: 14px;
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
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    window.themeManager = new ThemeManager();
});

// Экспорт для использования в других модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemeManager;
}

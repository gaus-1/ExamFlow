/**
 * ExamFlow Animations - Анимации и интерактивные элементы
 * Реализует плавные переходы, hover эффекты и анимации
 */

class ExamFlowAnimations {
    constructor() {
        this.init();
    }

    init() {
        this.setupScrollAnimations();
        this.setupTabSystem();
        this.setupAccordions();
        this.setupAIChat();
        this.setupHoverEffects();
        this.setupLoadingStates();
    }

    setupScrollAnimations() {
        // Анимация появления элементов при скролле
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                }
            });
        }, observerOptions);

        // Наблюдаем за всеми анимируемыми элементами
        document.querySelectorAll('.animate-on-scroll').forEach(el => {
            observer.observe(el);
        });
    }

    setupTabSystem() {
        // Система вкладок для "Задания ФИПИ"
        const tabButtons = document.querySelectorAll('.tab-button');
        const tabContents = document.querySelectorAll('.tab-content');

        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const targetTab = button.getAttribute('data-tab');
                
                // Убираем активный класс у всех кнопок и контента
                tabButtons.forEach(btn => btn.classList.remove('active'));
                tabContents.forEach(content => content.classList.remove('active'));
                
                // Активируем выбранную вкладку
                button.classList.add('active');
                const targetContent = document.querySelector(`[data-tab="${targetTab}"]`);
                if (targetContent) {
                    targetContent.classList.add('active');
                }
            });
        });
    }

    setupAccordions() {
        // Аккордеоны для информации
        const accordionHeaders = document.querySelectorAll('.accordion-header');
        
        accordionHeaders.forEach(header => {
            header.addEventListener('click', () => {
                const content = header.nextElementSibling;
                const isOpen = content.classList.contains('open');
                
                // Закрываем все аккордеоны
                document.querySelectorAll('.accordion-content').forEach(acc => {
                    acc.classList.remove('open');
                });
                
                // Открываем/закрываем текущий
                if (!isOpen) {
                    content.classList.add('open');
                }
            });
        });
    }

    setupAIChat() {
        // Обработка AI чата
        const aiInput = document.querySelector('#ai-chat-input');
        const aiSubmit = document.querySelector('#ai-chat-submit');
        const aiExamples = document.querySelectorAll('.ai-example');

        if (aiInput && aiSubmit) {
            aiSubmit.addEventListener('click', () => {
                this.handleAISubmit();
            });

            aiInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.handleAISubmit();
                }
            });
        }

        // Обработка примеров
        aiExamples.forEach(example => {
            example.addEventListener('click', () => {
                if (aiInput) {
                    aiInput.value = example.textContent;
                    aiInput.focus();
                }
            });
        });
    }

    handleAISubmit() {
        const input = document.querySelector('#ai-chat-input');
        const submitBtn = document.querySelector('#ai-chat-submit');
        
        if (!input || !submitBtn) return;

        const query = input.value.trim();
        if (!query) return;

        // Показываем состояние загрузки
        submitBtn.disabled = true;
        submitBtn.textContent = 'Отправка...';

        // Имитируем отправку (здесь будет реальный API вызов)
        setTimeout(() => {
            this.showAINotification('Запрос отправлен! В реальной версии здесь будет ответ от AI.');
            input.value = '';
            submitBtn.disabled = false;
            submitBtn.textContent = 'Отправить';
        }, 1000);
    }

    showAINotification(message) {
        const notification = document.createElement('div');
        notification.className = 'ai-notification';
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    setupHoverEffects() {
        // Hover эффекты для карточек и кнопок
        const hoverElements = document.querySelectorAll('.hover-effect');
        
        hoverElements.forEach(element => {
            element.addEventListener('mouseenter', () => {
                element.classList.add('hovered');
            });
            
            element.addEventListener('mouseleave', () => {
                element.classList.remove('hovered');
            });
        });
    }

    setupLoadingStates() {
        // Состояния загрузки для кнопок
        const loadingButtons = document.querySelectorAll('[data-loading]');
        
        loadingButtons.forEach(button => {
            button.addEventListener('click', () => {
                this.setButtonLoading(button, true);
                
                // Имитируем загрузку
                setTimeout(() => {
                    this.setButtonLoading(button, false);
                }, 2000);
            });
        });
    }

    setButtonLoading(button, isLoading) {
        if (isLoading) {
            button.disabled = true;
            button.dataset.originalText = button.textContent;
            button.textContent = 'Загрузка...';
        } else {
            button.disabled = false;
            button.textContent = button.dataset.originalText || 'Кнопка';
        }
    }

    // Утилиты для плавной прокрутки
    smoothScrollTo(target, duration = 500) {
        const targetElement = typeof target === 'string' ? document.querySelector(target) : target;
        if (!targetElement) return;

        const targetPosition = targetElement.offsetTop;
        const startPosition = window.pageYOffset;
        const distance = targetPosition - startPosition;
        let startTime = null;

        function animation(currentTime) {
            if (startTime === null) startTime = currentTime;
            const timeElapsed = currentTime - startTime;
            const run = ExamFlowAnimations.easeInOutCubic(timeElapsed, startPosition, distance, duration);
            window.scrollTo(0, run);
            if (timeElapsed < duration) requestAnimationFrame(animation);
        }

        requestAnimationFrame(animation);
    }

    static easeInOutCubic(t, b, c, d) {
        t /= d / 2;
        if (t < 1) return c / 2 * t * t * t + b;
        t -= 2;
        return c / 2 * (t * t * t + 2) + b;
    }
}

// Инициализация анимаций при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    new ExamFlowAnimations();
});

// Экспорт для использования в других модулях
window.ExamFlowAnimations = ExamFlowAnimations;

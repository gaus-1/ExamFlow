/**
 * Анимации и интерактивность для ExamFlow
 * Стиль Superhuman с плавными переходами
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

    /**
     * Анимации при скроллинге
     */
    setupScrollAnimations() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const element = entry.target;
                    const animationClass = element.dataset.animation || 'fade-in';
                    
                    // Добавляем задержку для элементов
                    const delay = element.dataset.delay || 0;
                    
                    setTimeout(() => {
                        element.classList.add(animationClass);
                        element.classList.add('visible');
                    }, delay);
                }
            });
        }, observerOptions);

        // Наблюдаем за элементами с анимациями
        document.querySelectorAll('[data-animation]').forEach(el => {
            observer.observe(el);
        });
    }

    /**
     * Система вкладок
     */
    setupTabSystem() {
        const tabContainers = document.querySelectorAll('.fipi-tabs');
        
        tabContainers.forEach(container => {
            const tabs = container.querySelectorAll('.fipi-tab');
            const contents = container.querySelectorAll('.fipi-tab-content');
            
            tabs.forEach((tab, index) => {
                tab.addEventListener('click', () => {
                    // Убираем активный класс со всех вкладок
                    tabs.forEach(t => t.classList.remove('active'));
                    contents.forEach(c => c.classList.remove('active'));
                    
                    // Добавляем активный класс к выбранной вкладке
                    tab.classList.add('active');
                    if (contents[index]) {
                        contents[index].classList.add('active');
                    }
                });
            });
        });
    }

    /**
     * Аккордеоны
     */
    setupAccordions() {
        const accordionItems = document.querySelectorAll('.accordion-item');
        
        accordionItems.forEach(item => {
            const header = item.querySelector('.accordion-header');
            const content = item.querySelector('.accordion-content');
            
            if (header && content) {
                header.addEventListener('click', () => {
                    const isActive = item.classList.contains('active');
                    
                    // Закрываем все аккордеоны
                    accordionItems.forEach(acc => {
                        acc.classList.remove('active');
                        const accContent = acc.querySelector('.accordion-content');
                        if (accContent) {
                            accContent.style.maxHeight = '0';
                        }
                    });
                    
                    // Открываем выбранный, если он был закрыт
                    if (!isActive) {
                        item.classList.add('active');
                        content.style.maxHeight = content.scrollHeight + 'px';
                    }
                });
            }
        });
    }

    /**
     * ИИ чат
     */
    setupAIChat() {
        const aiInput = document.querySelector('.ai-chat-input');
        const aiSubmit = document.querySelector('.ai-chat-submit');
        const aiExamples = document.querySelectorAll('.ai-example');
        
        if (aiInput && aiSubmit) {
            // Автоматическое изменение размера поля ввода
            aiInput.addEventListener('input', () => {
                aiInput.style.height = 'auto';
                aiInput.style.height = Math.min(aiInput.scrollHeight, 200) + 'px';
            });

            // Отправка по Enter
            aiInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.submitAIChat();
                }
            });

            // Клик по кнопке отправки
            aiSubmit.addEventListener('click', () => {
                this.submitAIChat();
            });
        }

        // Кликабельные примеры
        aiExamples.forEach(example => {
            example.addEventListener('click', () => {
                if (aiInput) {
                    aiInput.value = example.textContent;
                    aiInput.focus();
                    this.animateInput(aiInput);
                }
            });
        });
    }

    /**
     * Анимация поля ввода
     */
    animateInput(input) {
        input.classList.add('pulse');
        setTimeout(() => {
            input.classList.remove('pulse');
        }, 600);
    }

    /**
     * Отправка ИИ чата
     */
    submitAIChat() {
        const input = document.querySelector('.ai-chat-input');
        const submitBtn = document.querySelector('.ai-chat-submit');
        
        if (input && submitBtn) {
            const message = input.value.trim();
            if (message) {
                // Анимация отправки
                submitBtn.classList.add('rotate-in');
                
                // Здесь будет логика отправки сообщения
                console.log('Отправка ИИ чата:', message);
                
                // Сброс поля ввода
                input.value = '';
                input.style.height = 'auto';
                
                setTimeout(() => {
                    submitBtn.classList.remove('rotate-in');
                }, 1000);
            }
        }
    }

    /**
     * Эффекты при наведении
     */
    setupHoverEffects() {
        // Карточки с эффектом подъёма
        document.querySelectorAll('.card, .subject-card').forEach(card => {
            card.addEventListener('mouseenter', () => {
                card.style.transform = 'translateY(-8px) scale(1.02)';
            });
            
            card.addEventListener('mouseleave', () => {
                card.style.transform = 'translateY(0) scale(1)';
            });
        });

        // Кнопки с эффектом волны
        document.querySelectorAll('.btn-animate').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const rect = btn.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                btn.style.setProperty('--wave-x', x + 'px');
                btn.style.setProperty('--wave-y', y + 'px');
                btn.classList.add('wave');
                
                setTimeout(() => {
                    btn.classList.remove('wave');
                }, 600);
            });
        });
    }

    /**
     * Состояния загрузки
     */
    setupLoadingStates() {
        // Скелетон загрузки для карточек
        const createSkeleton = (element) => {
            element.classList.add('loading');
            element.innerHTML = `
                <div class="skeleton-line" style="height: 20px; background: var(--block-bg-medium); border-radius: 4px; margin-bottom: 10px;"></div>
                <div class="skeleton-line" style="height: 16px; background: var(--block-bg-medium); border-radius: 4px; margin-bottom: 8px; width: 80%;"></div>
                <div class="skeleton-line" style="height: 16px; background: var(--block-bg-medium); border-radius: 4px; width: 60%;"></div>
            `;
        };

        // Анимация скелетона
        const animateSkeleton = () => {
            const skeletons = document.querySelectorAll('.skeleton-line');
            skeletons.forEach((line, index) => {
                line.style.animationDelay = `${index * 0.1}s`;
                line.classList.add('skeleton-pulse');
            });
        };

        // Применяем скелетон к элементам с классом loading
        document.querySelectorAll('.loading').forEach(el => {
            createSkeleton(el);
            animateSkeleton();
        });
    }

    /**
     * Плавная прокрутка к элементам
     */
    smoothScrollTo(element, offset = 0) {
        const targetPosition = element.offsetTop - offset;
        const startPosition = window.pageYOffset;
        const distance = targetPosition - startPosition;
        const duration = 1000;
        let start = null;

        const animation = (currentTime) => {
            if (start === null) start = currentTime;
            const timeElapsed = currentTime - start;
            const run = this.easeInOutCubic(timeElapsed, startPosition, distance, duration);
            window.scrollTo(0, run);
            if (timeElapsed < duration) requestAnimationFrame(animation);
        };

        requestAnimationFrame(animation);
    }

    /**
     * Функция плавности
     */
    easeInOutCubic(t, b, c, d) {
        t /= d / 2;
        if (t < 1) return c / 2 * t * t * t + b;
        t -= 2;
        return c / 2 * (t * t * t + 2) + b;
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    new ExamFlowAnimations();
});

// Экспорт для использования в других модулях
window.ExamFlowAnimations = ExamFlowAnimations;

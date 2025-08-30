/* ExamFlow Components JavaScript - Адаптировано из React для Django */
/* ==================================================== */

// Инициализация компонентов при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    initializeComponents();
});

// Основная функция инициализации
function initializeComponents() {
    initializeDropdowns();
    initializeTabs();
    initializeAccordions();
    initializeDialogs();
    initializeToasts();
    initializeMobileMenu();
    initializeAIInterface();
}

// ===== DROPDOWN MENU =====
function initializeDropdowns() {
    const dropdowns = document.querySelectorAll('.dropdown-menu');
    
    dropdowns.forEach(dropdown => {
        const trigger = dropdown.querySelector('.dropdown-trigger');
        const content = dropdown.querySelector('.dropdown-content');
        
        if (trigger && content) {
            // Закрытие при клике вне dropdown
            document.addEventListener('click', (e) => {
                if (!dropdown.contains(e.target)) {
                    content.classList.remove('show');
                }
            });
            
            // Переключение dropdown
            trigger.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                // Закрываем все другие dropdowns
                document.querySelectorAll('.dropdown-content.show').forEach(openContent => {
                    if (openContent !== content) {
                        openContent.classList.remove('show');
                    }
                });
                
                content.classList.toggle('show');
            });
        }
    });
}

// ===== TABS =====
function initializeTabs() {
    const tabGroups = document.querySelectorAll('.tabs-component');
    
    tabGroups.forEach(tabGroup => {
        const triggers = tabGroup.querySelectorAll('.tabs-trigger');
        const panels = tabGroup.querySelectorAll('.tabs-panel');
        
        triggers.forEach((trigger, index) => {
            trigger.addEventListener('click', () => {
                // Убираем активный класс у всех триггеров и панелей
                triggers.forEach(t => t.classList.remove('active'));
                panels.forEach(p => p.style.display = 'none');
                
                // Активируем текущий таб
                trigger.classList.add('active');
                if (panels[index]) {
                    panels[index].style.display = 'block';
                }
            });
        });
        
        // Активируем первый таб по умолчанию
        if (triggers.length > 0) {
            triggers[0].click();
        }
    });
}

// ===== ACCORDION =====
function initializeAccordions() {
    const accordionItems = document.querySelectorAll('.accordion-item');
    
    accordionItems.forEach(item => {
        const trigger = item.querySelector('.accordion-trigger');
        const content = item.querySelector('.accordion-content');
        
        if (trigger && content) {
            trigger.addEventListener('click', () => {
                const isActive = trigger.classList.contains('active');
                
                // Закрываем все другие элементы
                accordionItems.forEach(otherItem => {
                    if (otherItem !== item) {
                        const otherTrigger = otherItem.querySelector('.accordion-trigger');
                        const otherContent = otherItem.querySelector('.accordion-content');
                        
                        otherTrigger.classList.remove('active');
                        otherContent.style.maxHeight = '0px';
                    }
                });
                
                // Переключаем текущий элемент
                if (isActive) {
                    trigger.classList.remove('active');
                    content.style.maxHeight = '0px';
                } else {
                    trigger.classList.add('active');
                    content.style.maxHeight = content.scrollHeight + 'px';
                }
            });
        }
    });
}

// ===== DIALOG =====
function initializeDialogs() {
    const dialogs = document.querySelectorAll('.dialog-component');
    
    dialogs.forEach(dialog => {
        const overlay = dialog.querySelector('.dialog-overlay');
        const content = dialog.querySelector('.dialog-content');
        const closeBtn = dialog.querySelector('.dialog-close');
        const openTriggers = document.querySelectorAll(`[data-dialog="${dialog.id}"]`);
        
        // Открытие диалога
        openTriggers.forEach(trigger => {
            trigger.addEventListener('click', (e) => {
                e.preventDefault();
                openDialog(dialog);
            });
        });
        
        // Закрытие по кнопке
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                closeDialog(dialog);
            });
        }
        
        // Закрытие по клику на overlay
        if (overlay) {
            overlay.addEventListener('click', () => {
                closeDialog(dialog);
            });
        }
        
        // Закрытие по Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && dialog.classList.contains('show')) {
                closeDialog(dialog);
            }
        });
    });
}

function openDialog(dialog) {
    const overlay = dialog.querySelector('.dialog-overlay');
    const content = dialog.querySelector('.dialog-content');
    
    if (overlay) overlay.classList.add('show');
    if (content) content.classList.add('show');
    dialog.classList.add('show');
    
    // Блокируем скролл body
    document.body.style.overflow = 'hidden';
}

function closeDialog(dialog) {
    const overlay = dialog.querySelector('.dialog-overlay');
    const content = dialog.querySelector('.dialog-content');
    
    if (overlay) overlay.classList.remove('show');
    if (content) content.classList.remove('show');
    dialog.classList.remove('show');
    
    // Восстанавливаем скролл body
    document.body.style.overflow = '';
}

// ===== TOAST =====
function initializeToasts() {
    // Глобальная функция для показа toast
    window.showToast = function(message, type = 'default', duration = 5000) {
        const toast = createToast(message, type);
        document.body.appendChild(toast);
        
        // Показываем toast
        setTimeout(() => {
            toast.classList.add('show');
        }, 100);
        
        // Автоматически скрываем
        setTimeout(() => {
            hideToast(toast);
        }, duration);
        
        // Обработчик закрытия
        const closeBtn = toast.querySelector('.toast-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                hideToast(toast);
            });
        }
    };
}

function createToast(message, type) {
    const toast = document.createElement('div');
    toast.className = `toast-component toast-${type}`;
    
    const icon = getToastIcon(type);
    
    toast.innerHTML = `
        <div class="toast-icon">${icon}</div>
        <div class="toast-content">
            <div class="toast-title">${message}</div>
        </div>
        <button class="toast-close" aria-label="Закрыть">
            <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
                <path d="M11.7816 4.03157C12.0062 3.80702 12.0062 3.44295 11.7816 3.2184C11.5571 2.99385 11.193 2.99385 10.9685 3.2184L7.50005 6.68682L4.03164 3.2184C3.80708 2.99385 3.44301 2.99385 3.21846 3.2184C2.99391 3.44295 2.99391 3.80702 3.21846 4.03157L6.68688 7.49999L3.21846 10.9684C2.99391 11.193 2.99391 11.557 3.21846 11.7816C3.44301 12.0061 3.80708 12.0061 4.03164 11.7816L7.50005 8.31316L10.9685 11.7816C11.193 12.0061 11.5571 12.0061 11.7816 11.7816C12.0062 11.557 12.0062 11.193 11.7816 10.9684L8.31322 7.49999L11.7816 4.03157Z" fill="currentColor"/>
            </svg>
        </button>
    `;
    
    return toast;
}

function getToastIcon(type) {
    const icons = {
        success: `<svg width="15" height="15" viewBox="0 0 15 15" fill="none">
            <path d="M7.49991 0.877075C3.84222 0.877075 0.877075 3.84222 0.877075 7.49991C0.877075 11.1576 3.84222 14.1227 7.49991 14.1227C11.1576 14.1227 14.1227 11.1576 14.1227 7.49991C14.1227 3.84222 11.1576 0.877075 7.49991 0.877075ZM1.82708 7.49991C1.82708 4.36686 4.36686 1.82708 7.49991 1.82708C10.633 1.82708 13.1727 4.36686 13.1727 7.49991C13.1727 10.633 10.633 13.1727 7.49991 13.1727C4.36686 13.1727 1.82708 10.633 1.82708 7.49991ZM10.1589 5.53774C10.3178 5.31191 10.2636 5.00001 10.0378 4.84109C9.81194 4.68217 9.50004 4.73642 9.34112 4.96225L6.51977 8.97154L5.35681 7.78706C5.16334 7.59002 4.84669 7.58711 4.64965 7.78058C4.45261 7.97404 4.4497 8.29069 4.64317 8.48773L6.24704 10.1004C6.44051 10.2974 6.75716 10.3003 6.9542 10.1068L10.1589 5.53774Z" fill="currentColor"/>
        </svg>`,
        error: `<svg width="15" height="15" viewBox="0 0 15 15" fill="none">
            <path d="M7.49991 0.877075C3.84222 0.877075 0.877075 3.84222 0.877075 7.49991C0.877075 11.1576 3.84222 14.1227 7.49991 14.1227C11.1576 14.1227 14.1227 11.1576 14.1227 7.49991C14.1227 3.84222 11.1576 0.877075 7.49991 0.877075ZM1.82708 7.49991C1.82708 4.36686 4.36686 1.82708 7.49991 1.82708C10.633 1.82708 13.1727 4.36686 13.1727 7.49991C13.1727 10.633 10.633 13.1727 7.49991 13.1727C4.36686 13.1727 1.82708 10.633 1.82708 7.49991ZM7.49991 3.49991C7.77605 3.49991 7.99991 3.72377 7.99991 3.99991V7.49991C7.99991 7.77605 7.77605 7.99991 7.49991 7.99991C7.22377 7.99991 6.99991 7.77605 6.99991 7.49991V3.99991C6.99991 3.72377 7.22377 3.49991 7.49991 3.49991ZM7.49991 10.4999C7.77605 10.4999 7.99991 10.7238 7.99991 10.9999C7.99991 11.2761 7.77605 11.4999 7.49991 11.4999C7.22377 11.4999 6.99991 11.2761 6.99991 10.9999C6.99991 10.7238 7.22377 10.4999 7.49991 10.4999Z" fill="currentColor"/>
        </svg>`,
        warning: `<svg width="15" height="15" viewBox="0 0 15 15" fill="none">
            <path d="M8.4449 0.608765C8.0183 -0.107015 6.9817 -0.107015 6.5551 0.608765L0.161277 11.3368C-0.265316 12.0526 0.223299 13 1.10618 13H13.8938C14.7767 13 15.2653 12.0526 14.8387 11.3368L8.4449 0.608765ZM7.4141 1.12073C7.4141 1.12073 7.4141 1.12073 7.4141 1.12073ZM7.49991 7.49991C7.77605 7.49991 7.99991 7.72377 7.99991 7.99991V10.9999C7.99991 11.2761 7.77605 11.4999 7.49991 11.4999C7.22377 11.4999 6.99991 11.2761 6.99991 10.9999V7.99991C6.99991 7.72377 7.22377 7.49991 7.49991 7.49991ZM7.49991 12.4999C7.77605 12.4999 7.99991 12.7238 7.99991 12.9999C7.99991 13.2761 7.77605 13.4999 7.49991 13.4999C7.22377 13.4999 6.99991 13.2761 6.99991 12.9999C6.99991 12.7238 7.22377 12.4999 7.49991 12.4999Z" fill="currentColor"/>
        </svg>`,
        info: `<svg width="15" height="15" viewBox="0 0 15 15" fill="none">
            <path d="M7.49991 0.877075C3.84222 0.877075 0.877075 3.84222 0.877075 7.49991C0.877075 11.1576 3.84222 14.1227 7.49991 14.1227C11.1576 14.1227 14.1227 11.1576 14.1227 7.49991C14.1227 3.84222 11.1576 0.877075 7.49991 0.877075ZM1.82708 7.49991C1.82708 4.36686 4.36686 1.82708 7.49991 1.82708C10.633 1.82708 13.1727 4.36686 13.1727 7.49991C13.1727 10.633 10.633 13.1727 7.49991 13.1727C4.36686 13.1727 1.82708 10.633 1.82708 7.49991ZM7.49991 3.49991C7.77605 3.49991 7.99991 3.72377 7.99991 3.99991C7.99991 4.27605 7.77605 4.49991 7.49991 4.49991C7.22377 4.49991 6.99991 4.27605 6.99991 3.99991C6.99991 3.72377 7.22377 3.49991 7.49991 3.49991ZM7.49991 10.4999C7.77605 10.4999 7.99991 10.7238 7.99991 10.9999C7.99991 11.2761 7.77605 11.4999 7.49991 11.4999C7.22377 11.4999 6.99991 11.2761 6.99991 10.9999C6.99991 10.7238 7.22377 10.4999 7.49991 10.4999ZM7.49991 5.99991C7.77605 5.99991 7.99991 6.22377 7.99991 6.49991V9.49991C7.99991 9.77605 7.77605 9.99991 7.49991 9.99991C7.22377 9.99991 6.99991 9.77605 6.99991 9.49991V6.49991C6.99991 6.22377 7.22377 5.99991 7.49991 5.99991Z" fill="currentColor"/>
        </svg>`,
        default: `<svg width="15" height="15" viewBox="0 0 15 15" fill="none">
            <path d="M7.49991 0.877075C3.84222 0.877075 0.877075 3.84222 0.877075 7.49991C0.877075 11.1576 3.84222 14.1227 7.49991 14.1227C11.1576 14.1227 14.1227 11.1576 14.1227 7.49991C14.1227 3.84222 11.1576 0.877075 7.49991 0.877075ZM1.82708 7.49991C1.82708 4.36686 4.36686 1.82708 7.49991 1.82708C10.633 1.82708 13.1727 4.36686 13.1727 7.49991C13.1727 10.633 10.633 13.1727 7.49991 13.1727C4.36686 13.1727 1.82708 10.633 1.82708 7.49991Z" fill="currentColor"/>
        </svg>`
    };
    
    return icons[type] || icons.default;
}

function hideToast(toast) {
    toast.classList.remove('show');
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 300);
}

// ===== MOBILE MENU =====
function initializeMobileMenu() {
    const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
    const mobileMenu = document.querySelector('.mobile-menu');
    
    if (mobileMenuBtn && mobileMenu) {
        mobileMenuBtn.addEventListener('click', () => {
            const isOpen = mobileMenu.style.display === 'block';
            mobileMenu.style.display = isOpen ? 'none' : 'block';
            
            // Анимация иконки
            const icon = mobileMenuBtn.querySelector('svg');
            if (icon) {
                icon.style.transform = isOpen ? 'rotate(0deg)' : 'rotate(90deg)';
            }
        });
        
        // Закрытие при клике на ссылку
        const mobileLinks = mobileMenu.querySelectorAll('a');
        mobileLinks.forEach(link => {
            link.addEventListener('click', () => {
                mobileMenu.style.display = 'none';
                const icon = mobileMenuBtn.querySelector('svg');
                if (icon) {
                    icon.style.transform = 'rotate(0deg)';
                }
            });
        });
    }
}

// ===== AI INTERFACE =====
function initializeAIInterface() {
    const aiInput = document.querySelector('.ai-input-new');
    const aiSendBtn = document.querySelector('.ai-send-btn');
    const aiSubjects = document.querySelectorAll('.ai-subject-badge');
    
    if (aiInput && aiSendBtn) {
        // Отправка по Enter
        aiInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                handleAISearch();
            }
        });
        
        // Отправка по кнопке
        aiSendBtn.addEventListener('click', handleAISearch);
    }
    
    // Быстрые примеры
    aiSubjects.forEach(subject => {
        subject.addEventListener('click', () => {
            if (aiInput) {
                aiInput.value = `Помоги подготовиться к ${subject.textContent}`;
                aiInput.focus();
            }
        });
    });
}

function handleAISearch() {
    const aiInput = document.querySelector('.ai-input-new');
    const query = aiInput ? aiInput.value.trim() : '';
    
    if (query) {
        // Показываем toast с подтверждением
        window.showToast(`Отправляем запрос: "${query}"`, 'info');
        
        // Здесь можно добавить логику отправки запроса на сервер
        console.log('AI Query:', query);
        
        // Очищаем поле
        if (aiInput) {
            aiInput.value = '';
        }
    }
}

// ===== UTILITY FUNCTIONS =====
function cn(...classes) {
    return classes.filter(Boolean).join(' ');
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    // Показываем toast
    window.showToast(`Тема изменена на: ${newTheme === 'dark' ? 'темную' : 'светлую'}`, 'info');
}

function animateOnScroll() {
    const elements = document.querySelectorAll('.animate-fade-in, .animate-slide-up');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.animationPlayState = 'running';
            }
        });
    }, {
        threshold: 0.1
    });
    
    elements.forEach(el => {
        observer.observe(el);
    });
}

// Инициализация анимаций при скролле
document.addEventListener('DOMContentLoaded', () => {
    animateOnScroll();
});

// Экспорт функций для использования в других скриптах
window.ExamFlowComponents = {
    showToast: window.showToast,
    toggleTheme,
    cn,
    animateOnScroll
};

// Глобальные утилиты
window.utils = {
    // Debounce функция
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    // Throttle функция
    throttle: function(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },
    
    // Проверка поддержки CSS свойств
    supportsCSS: function(property) {
        return CSS.supports(property, 'initial');
    },
    
    // Получение computed стилей
    getComputedStyle: function(element, property) {
        return window.getComputedStyle(element).getPropertyValue(property);
    }
};

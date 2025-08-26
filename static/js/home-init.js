// Инициализация анимаций и геймификации для главной страницы ExamFlow
document.addEventListener('DOMContentLoaded', function() {
    // Инициализация анимаций
    if (typeof ExamFlowAnimations !== 'undefined') {
        const animations = new ExamFlowAnimations();
        animations.init();
    }
    
    // Инициализация геймификации
    if (typeof ExamFlowGamification !== 'undefined') {
        const gamification = new ExamFlowGamification();
        gamification.init();
    }
    
    // Обработка ошибок QR-кода
    const qrImage = document.querySelector('img[src*="api.qrserver.com"]');
    if (qrImage) {
        qrImage.addEventListener('error', function() {
            this.style.display = 'none';
            const fallback = this.parentElement?.querySelector('div');
            if (fallback) {
                fallback.style.display = 'flex';
            }
        });
    }
    
    // Инициализация табов ФИПИ
    initFipiTabs();
    
    // Инициализация аккордеона
    initAccordion();
});

// Функция для инициализации табов ФИПИ
function initFipiTabs() {
    const tabButtons = document.querySelectorAll('.fipi-tab');
    const tabContents = document.querySelectorAll('.fipi-tab-content');
    
    tabButtons.forEach((button, index) => {
        button.addEventListener('click', () => {
            // Убираем активный класс у всех кнопок и контента
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Добавляем активный класс к выбранной кнопке и контенту
            button.classList.add('active');
            if (tabContents[index]) {
                tabContents[index].classList.add('active');
            }
        });
    });
}

// Функция для инициализации аккордеона
function initAccordion() {
    const accordionHeaders = document.querySelectorAll('.accordion-header');
    
    accordionHeaders.forEach(header => {
        header.addEventListener('click', () => {
            const item = header.parentElement;
            const content = item.querySelector('.accordion-content');
            const icon = header.querySelector('.accordion-icon');
            
            // Переключаем состояние
            if (item.classList.contains('active')) {
                item.classList.remove('active');
                content.style.maxHeight = '0px';
                icon.style.transform = 'rotate(0deg)';
            } else {
                // Закрываем все остальные элементы
                document.querySelectorAll('.accordion-item').forEach(accItem => {
                    accItem.classList.remove('active');
                    const accContent = accItem.querySelector('.accordion-content');
                    const accIcon = accItem.querySelector('.accordion-icon');
                    if (accContent) accContent.style.maxHeight = '0px';
                    if (accIcon) accIcon.style.transform = 'rotate(0deg)';
                });
                
                // Открываем текущий элемент
                item.classList.add('active');
                content.style.maxHeight = content.scrollHeight + 'px';
                icon.style.transform = 'rotate(180deg)';
            }
        });
    });
}



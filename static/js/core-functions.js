// Функции для страниц core приложения ExamFlow

// Функции для персонализации
function showFeatureComingSoon() {
    alert('Функция решения задач будет добавлена позже');
}

// Функции для рекомендаций
function startTask(taskId) {
    console.log('Запуск задачи:', taskId);
    // Здесь будет логика запуска задачи
    window.location.href = `/tasks/${taskId}/`;
}

function reloadPage() {
    location.reload();
}

// Функции для плана обучения
function continueTopic(topicId) {
    console.log('Продолжение темы:', topicId);
    // Здесь будет логика продолжения темы
    window.location.href = `/topics/${topicId}/continue/`;
}

function startTopic(topicId) {
    console.log('Начало темы:', topicId);
    // Здесь будет логика начала темы
    window.location.href = `/topics/${topicId}/start/`;
}

// Функции для слабых тем
function startPractice(topicId) {
    console.log('Начало практики по теме:', topicId);
    // Здесь будет логика начала практики
    window.location.href = `/topics/${topicId}/practice/`;
}

function showTheory(topicId) {
    console.log('Показать теорию по теме:', topicId);
    // Здесь будет логика показа теории
    window.location.href = `/topics/${topicId}/theory/`;
}

// Функции для деталей темы
function filterTasks(difficulty) {
    console.log('Фильтрация задач по сложности:', difficulty);
    
    // Убираем активный класс у всех кнопок
    document.querySelectorAll('.btn-outline-secondary, .btn-outline-success, .btn-outline-warning, .btn-outline-danger').forEach(btn => {
        btn.classList.remove('btn-outline-secondary', 'btn-outline-success', 'btn-outline-warning', 'btn-outline-danger');
        btn.classList.add('btn-outline-secondary');
    });
    
    // Добавляем активный класс к выбранной кнопке
    const activeButton = event.target;
    activeButton.classList.remove('btn-outline-secondary');
    
    if (difficulty === 'easy') {
        activeButton.classList.add('btn-outline-success');
    } else if (difficulty === 'medium') {
        activeButton.classList.add('btn-outline-warning');
    } else if (difficulty === 'hard') {
        activeButton.classList.add('btn-outline-danger');
    } else {
        activeButton.classList.add('btn-outline-secondary');
    }
    
    // Здесь будет логика фильтрации задач
    const taskCards = document.querySelectorAll('.task-card');
    taskCards.forEach(card => {
        if (difficulty === 'all' || card.dataset.difficulty === difficulty) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    console.log('Core functions initialized');
    
    // Добавляем обработчики событий для всех кнопок
    addEventListeners();
});

function addEventListeners() {
    // Кнопки "Функция будет добавлена позже"
    document.querySelectorAll('[onclick*="alert"]').forEach(btn => {
        btn.removeAttribute('onclick');
        btn.addEventListener('click', showFeatureComingSoon);
    });
    
    // Кнопки startTask
    document.querySelectorAll('[onclick*="startTask"]').forEach(btn => {
        const taskId = btn.getAttribute('data-task-id') || btn.closest('[data-task-id]')?.dataset.taskId;
        btn.removeAttribute('onclick');
        btn.addEventListener('click', () => startTask(taskId));
    });
    
    // Кнопки reload
    document.querySelectorAll('[onclick*="location.reload"]').forEach(btn => {
        btn.removeAttribute('onclick');
        btn.addEventListener('click', reloadPage);
    });
    
    // Кнопки continueTopic
    document.querySelectorAll('[onclick*="continueTopic"]').forEach(btn => {
        const topicId = btn.getAttribute('data-topic-id') || btn.closest('[data-topic-id]')?.dataset.topicId;
        btn.removeAttribute('onclick');
        btn.addEventListener('click', () => continueTopic(topicId));
    });
    
    // Кнопки startTopic
    document.querySelectorAll('[onclick*="startTopic"]').forEach(btn => {
        const topicId = btn.getAttribute('data-topic-id') || btn.closest('[data-topic-id]')?.dataset.topicId;
        btn.removeAttribute('onclick');
        btn.addEventListener('click', () => startTopic(topicId));
    });
    
    // Кнопки startPractice
    document.querySelectorAll('[onclick*="startPractice"]').forEach(btn => {
        const topicId = btn.getAttribute('data-topic-id') || btn.closest('[data-topic-id]')?.dataset.topicId;
        btn.removeAttribute('onclick');
        btn.addEventListener('click', () => startPractice(topicId));
    });
    
    // Кнопки showTheory
    document.querySelectorAll('[onclick*="showTheory"]').forEach(btn => {
        const topicId = btn.getAttribute('data-topic-id') || btn.closest('[data-topic-id]')?.dataset.topicId;
        btn.removeAttribute('onclick');
        btn.addEventListener('click', () => showTheory(topicId));
    });
    
    // Кнопки filterTasks
    document.querySelectorAll('[onclick*="filterTasks"]').forEach(btn => {
        const difficulty = btn.getAttribute('data-difficulty') || 'all';
        btn.removeAttribute('onclick');
        btn.addEventListener('click', () => filterTasks(difficulty));
    });
}

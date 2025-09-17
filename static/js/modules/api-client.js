/**
 * 🔌 ExamFlow API Client
 * Современный клиент для работы с API (ES2025+)
 */

class APIClient {
  #baseURL;
  #defaultHeaders;
  #abortController;

  constructor(baseURL = '') {
    this.#baseURL = baseURL;
    this.#defaultHeaders = {
      'Content-Type': 'application/json',
    };
    this.#abortController = new AbortController();
  }

  /**
   * Получает CSRF токен из cookies или meta-тегов
   * @returns {string} CSRF токен
   */
  #getCSRFToken() {
    // Сначала ищем в cookies
    const cookies = document.cookie.split(';');
    for (const cookie of cookies) {
      const [name, value] = cookie.trim().split('=');
      if (name === 'csrftoken') {
        return decodeURIComponent(value);
      }
    }
    
    // Fallback: поиск в meta-тегах
    const csrfMeta = document.querySelector('meta[name="csrf-token"]');
    return csrfMeta?.getAttribute('content') ?? '';
  }

  /**
   * Выполняет HTTP запрос с современными стандартами
   * @param {string} endpoint - Конечная точка API
   * @param {Object} options - Опции запроса
   * @returns {Promise<Object>} Ответ API
   */
  async #makeRequest(endpoint, options = {}) {
    const url = new URL(endpoint, this.#baseURL);
    
    const config = {
      headers: {
        ...this.#defaultHeaders,
        'X-CSRFToken': this.#getCSRFToken(),
        ...options.headers,
      },
      signal: this.#abortController.signal,
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new APIError(
          `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          await response.text()
        );
      }
      
      const contentType = response.headers.get('content-type');
      if (contentType?.includes('application/json')) {
        return await response.json();
      }
      
      return await response.text();
      
    } catch (error) {
      if (error.name === 'AbortError') {
        throw new APIError('Запрос отменен', 0, 'Request aborted');
      }
      
      if (error instanceof APIError) {
        throw error;
      }
      
      throw new APIError('Ошибка сети', 0, error.message);
    }
  }

  /**
   * Отправляет вопрос к AI ассистенту
   * @param {string} prompt - Вопрос пользователя
   * @returns {Promise<Object>} Ответ AI
   */
  async askAI(prompt) {
    if (!prompt?.trim()) {
      throw new APIError('Пустой запрос', 400, 'Prompt is required');
    }

    return await this.#makeRequest('/ai/api/', {
      method: 'POST',
      body: JSON.stringify({ prompt: prompt.trim() }),
    });
  }

  /**
   * Получает список предметов
   * @returns {Promise<Array>} Список предметов
   */
  async getSubjects() {
    return await this.#makeRequest('/api/subjects/');
  }

  /**
   * Получает случайную задачу
   * @param {number} subjectId - ID предмета (опционально)
   * @returns {Promise<Object>} Задача
   */
  async getRandomTask(subjectId = null) {
    const endpoint = subjectId 
      ? `/api/tasks/random/?subject=${subjectId}`
      : '/api/tasks/random/';
    
    return await this.#makeRequest(endpoint);
  }

  /**
   * Отправляет ответ на задачу
   * @param {number} taskId - ID задачи
   * @param {string} answer - Ответ пользователя
   * @returns {Promise<Object>} Результат проверки
   */
  async submitAnswer(taskId, answer) {
    return await this.#makeRequest(`/api/tasks/${taskId}/submit/`, {
      method: 'POST',
      body: JSON.stringify({ answer }),
    });
  }

  /**
   * Получает статистику пользователя
   * @returns {Promise<Object>} Статистика
   */
  async getUserStats() {
    return await this.#makeRequest('/api/user/stats/');
  }

  /**
   * Отменяет все активные запросы
   */
  abort() {
    this.#abortController.abort();
    this.#abortController = new AbortController();
  }
}

/**
 * Кастомный класс ошибок API
 */
class APIError extends Error {
  constructor(message, status = 0, details = '') {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.details = details;
  }

  toString() {
    return `${this.name}: ${this.message} (${this.status})`;
  }
}

// Экспорт для использования в других модулях
export { APIClient, APIError };

// Глобальный экземпляр для обратной совместимости
window.examFlowAPI = new APIClient();

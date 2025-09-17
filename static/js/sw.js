/**
 * 🔧 ExamFlow Service Worker
 * Кэширование ресурсов для быстрой загрузки и офлайн работы
 */

const CACHE_NAME = 'examflow-v3.0';
const STATIC_CACHE = 'examflow-static-v3.0';

// Ресурсы для кэширования
const CACHE_RESOURCES = [
  '/',
  '/static/css/examflow-unified.css',
  '/static/js/examflow-main.js',
  'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap'
];

// Установка Service Worker
self.addEventListener('install', (event) => {
  console.log('🔧 Service Worker: установка');
  
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => {
        console.log('📦 Кэширование статических ресурсов');
        return cache.addAll(CACHE_RESOURCES);
      })
      .catch((error) => {
        console.error('❌ Ошибка кэширования:', error);
      })
  );
  
  // Принудительная активация нового SW
  self.skipWaiting();
});

// Активация Service Worker
self.addEventListener('activate', (event) => {
  console.log('🚀 Service Worker: активация');
  
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          // Удаляем старые кэши
          if (cacheName !== CACHE_NAME && cacheName !== STATIC_CACHE) {
            console.log('🧹 Удаление старого кэша:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  
  // Захватываем контроль над всеми клиентами
  self.clients.claim();
});

// Обработка запросов
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Игнорируем запросы к API и админке
  if (url.pathname.startsWith('/api/') || 
      url.pathname.startsWith('/admin/') || 
      url.pathname.startsWith('/bot/')) {
    return;
  }
  
  event.respondWith(
    caches.match(request)
      .then((response) => {
        // Возвращаем из кэша если есть
        if (response) {
          return response;
        }
        
        // Иначе загружаем из сети
        return fetch(request)
          .then((response) => {
            // Проверяем валидность ответа
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }
            
            // Клонируем ответ для кэширования
            const responseToCache = response.clone();
            
            // Кэшируем только GET запросы
            if (request.method === 'GET') {
              caches.open(CACHE_NAME)
                .then((cache) => {
                  cache.put(request, responseToCache);
                });
            }
            
            return response;
          })
          .catch(() => {
            // Офлайн fallback
            if (request.destination === 'document') {
              return caches.match('/');
            }
          });
      })
  );
});

// Обработка сообщений от главного потока
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

// Уведомления о обновлениях
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'GET_VERSION') {
    event.ports[0].postMessage({ version: CACHE_NAME });
  }
});

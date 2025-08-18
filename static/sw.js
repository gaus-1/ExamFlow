// ExamFlow Service Worker для PWA
const CACHE_NAME = 'examflow-v1.0';
const STATIC_CACHE_URLS = [
  '/',
  '/subjects/',
  '/static/manifest.json',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
  'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap'
];

// Установка Service Worker
self.addEventListener('install', event => {
  console.log('ExamFlow SW: Installing...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('ExamFlow SW: Caching static resources');
        return cache.addAll(STATIC_CACHE_URLS);
      })
      .then(() => {
        console.log('ExamFlow SW: Installation complete');
        return self.skipWaiting();
      })
  );
});

// Активация Service Worker
self.addEventListener('activate', event => {
  console.log('ExamFlow SW: Activating...');
  event.waitUntil(
    caches.keys()
      .then(cacheNames => {
        return Promise.all(
          cacheNames.map(cacheName => {
            if (cacheName !== CACHE_NAME) {
              console.log('ExamFlow SW: Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('ExamFlow SW: Activation complete');
        return self.clients.claim();
      })
  );
});

// Обработка запросов
self.addEventListener('fetch', event => {
  const { request } = event;
  
  // Пропускаем не-GET запросы и внешние API
  if (request.method !== 'GET' || 
      request.url.includes('/api/') ||
      request.url.includes('telegram') ||
      request.url.includes('chrome-extension')) {
    return;
  }
  
  event.respondWith(
    caches.match(request)
      .then(cachedResponse => {
        // Возвращаем кэшированный ответ если есть
        if (cachedResponse) {
          console.log('ExamFlow SW: Serving from cache:', request.url);
          return cachedResponse;
        }
        
        // Иначе делаем сетевой запрос
        return fetch(request)
          .then(response => {
            // Проверяем валидность ответа
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }
            
            // Клонируем ответ для кэширования
            const responseToCache = response.clone();
            
            // Кэшируем ответ для статических ресурсов
            if (request.url.includes('.css') || 
                request.url.includes('.js') || 
                request.url.includes('.png') || 
                request.url.includes('.jpg') ||
                request.url.includes('.woff')) {
              
              caches.open(CACHE_NAME)
                .then(cache => {
                  console.log('ExamFlow SW: Caching new resource:', request.url);
                  cache.put(request, responseToCache);
                });
            }
            
            return response;
          })
          .catch(() => {
            // В случае отсутствия сети показываем офлайн страницу
            if (request.destination === 'document') {
              return caches.match('/offline.html') || 
                     new Response('ExamFlow временно недоступен. Проверьте подключение к интернету.', {
                       headers: { 'Content-Type': 'text/plain; charset=utf-8' }
                     });
            }
            
            // Для других ресурсов возвращаем пустой ответ
            return new Response('', { status: 408, statusText: 'Request timeout' });
          });
      })
  );
});

// Push уведомления (для будущего использования)
self.addEventListener('push', event => {
  if (!event.data) return;
  
  const data = event.data.json();
  
  const options = {
    body: data.body || 'У вас есть новые задания для решения!',
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/icon-72x72.png',
    tag: 'examflow-notification',
    data: data.url || '/',
    actions: [
      {
        action: 'open',
        title: 'Открыть',
        icon: '/static/icons/icon-96x96.png'
      },
      {
        action: 'close',
        title: 'Закрыть'
      }
    ],
    requireInteraction: true,
    silent: false
  };
  
  event.waitUntil(
    self.registration.showNotification(data.title || 'ExamFlow', options)
  );
});

// Обработка кликов по уведомлениям
self.addEventListener('notificationclick', event => {
  event.notification.close();
  
  if (event.action === 'close') {
    return;
  }
  
  const url = event.notification.data || '/';
  
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then(clientList => {
        // Ищем уже открытое окно
        for (let client of clientList) {
          if (client.url.includes(self.location.origin) && 'focus' in client) {
            client.navigate(url);
            return client.focus();
          }
        }
        
        // Открываем новое окно
        if (clients.openWindow) {
          return clients.openWindow(url);
        }
      })
  );
});

// Синхронизация в фоне (для будущего использования)
self.addEventListener('sync', event => {
  console.log('ExamFlow SW: Background sync:', event.tag);
  
  if (event.tag === 'background-sync') {
    event.waitUntil(
      // Здесь можно синхронизировать данные
      fetch('/api/sync/')
        .then(response => response.json())
        .then(data => {
          console.log('ExamFlow SW: Background sync completed:', data);
        })
        .catch(error => {
          console.error('ExamFlow SW: Background sync failed:', error);
        })
    );
  }
});

console.log('ExamFlow Service Worker loaded');

/**
 * ExamFlow Service Worker
 * Кэширование и оптимизация производительности
 */

const CACHE_NAME = 'examflow-v1.0.0';
const STATIC_CACHE = 'examflow-static-v1.0.0';
const DYNAMIC_CACHE = 'examflow-dynamic-v1.0.0';

// Ресурсы для кэширования при установке
const STATIC_ASSETS = [
    '/',
    '/static/css/examflow-ux-optimized.css',
    '/static/js/examflow-optimizations.js',
    '/static/images/examflow-logo.png',
    '/static/images/examflow-og-image.jpg',
    // Шрифты
    'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap',
    'https://fonts.gstatic.com/s/inter/v12/UcCO3FwrK3iLTeHuS_fvQtMwCp50KnMw2boKoduKmMEVuLyfAZ9hiA.woff2'
];

// Стратегии кэширования
const CACHE_STRATEGIES = {
    // Статические ресурсы - Cache First
    static: ['css', 'js', 'woff', 'woff2', 'png', 'jpg', 'jpeg', 'svg', 'ico'],
    
    // HTML страницы - Network First
    html: ['html', 'htm'],
    
    // API запросы - Network First с fallback
    api: ['/api/', '/telegram_auth/', '/learning/'],
    
    // Изображения - Cache First
    images: ['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg']
};

// Установка Service Worker
self.addEventListener('install', event => {
    console.log('[SW] Installing...');
    
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then(cache => {
                console.log('[SW] Caching static assets');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => {
                console.log('[SW] Static assets cached');
                return self.skipWaiting();
            })
            .catch(error => {
                console.error('[SW] Failed to cache static assets:', error);
            })
    );
});

// Активация Service Worker
self.addEventListener('activate', event => {
    console.log('[SW] Activating...');
    
    event.waitUntil(
        caches.keys()
            .then(cacheNames => {
                return Promise.all(
                    cacheNames.map(cacheName => {
                        if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
                            console.log('[SW] Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('[SW] Activated');
                return self.clients.claim();
            })
    );
});

// Перехват запросов
self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Пропускаем не-GET запросы
    if (request.method !== 'GET') {
        return;
    }
    
    // Пропускаем chrome-extension и другие протоколы
    if (!url.protocol.startsWith('http')) {
        return;
    }
    
    event.respondWith(handleRequest(request));
});

// Обработка запросов с различными стратегиями
async function handleRequest(request) {
    const url = new URL(request.url);
    const pathname = url.pathname;
    const extension = getFileExtension(pathname);
    
    try {
        // Статические ресурсы - Cache First
        if (CACHE_STRATEGIES.static.includes(extension)) {
            return await cacheFirst(request, STATIC_CACHE);
        }
        
        // HTML страницы - Network First
        if (CACHE_STRATEGIES.html.includes(extension) || pathname === '/') {
            return await networkFirst(request, DYNAMIC_CACHE);
        }
        
        // API запросы - Network First с fallback
        if (CACHE_STRATEGIES.api.some(apiPath => pathname.startsWith(apiPath))) {
            return await networkFirst(request, DYNAMIC_CACHE);
        }
        
        // Изображения - Cache First
        if (CACHE_STRATEGIES.images.includes(extension)) {
            return await cacheFirst(request, STATIC_CACHE);
        }
        
        // По умолчанию - Network First
        return await networkFirst(request, DYNAMIC_CACHE);
        
    } catch (error) {
        console.error('[SW] Error handling request:', error);
        
        // Fallback для HTML страниц
        if (pathname === '/' || CACHE_STRATEGIES.html.includes(extension)) {
            const fallbackResponse = await caches.match('/');
            if (fallbackResponse) {
                return fallbackResponse;
            }
        }
        
        // Возвращаем ошибку
        return new Response('Network error', {
            status: 503,
            statusText: 'Service Unavailable'
        });
    }
}

// Стратегия Cache First
async function cacheFirst(request, cacheName) {
    const cache = await caches.open(cacheName);
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
        return cachedResponse;
    }
    
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
        cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
}

// Стратегия Network First
async function networkFirst(request, cacheName) {
    const cache = await caches.open(cacheName);
    
    try {
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.log('[SW] Network failed, trying cache:', error);
        
        const cachedResponse = await cache.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        throw error;
    }
}

// Получение расширения файла
function getFileExtension(pathname) {
    const parts = pathname.split('.');
    return parts.length > 1 ? parts.pop().toLowerCase() : '';
}

// Обработка push уведомлений
self.addEventListener('push', event => {
    if (!event.data) {
        return;
    }
    
    const data = event.data.json();
    const options = {
        body: data.body,
        icon: '/static/images/examflow-logo.png',
        badge: '/static/images/examflow-badge.png',
        vibrate: [100, 50, 100],
        data: {
            dateOfArrival: Date.now(),
            primaryKey: data.primaryKey || 1
        },
        actions: [
            {
                action: 'explore',
                title: 'Открыть ExamFlow',
                icon: '/static/images/examflow-logo.png'
            },
            {
                action: 'close',
                title: 'Закрыть',
                icon: '/static/images/close.png'
            }
        ]
    };
    
    event.waitUntil(
        self.registration.showNotification(data.title || 'ExamFlow', options)
    );
});

// Обработка кликов по уведомлениям
self.addEventListener('notificationclick', event => {
    event.notification.close();
    
    if (event.action === 'explore') {
        event.waitUntil(
            clients.openWindow('/')
        );
    } else if (event.action === 'close') {
        // Просто закрываем уведомление
        return;
    } else {
        // По умолчанию открываем главную страницу
        event.waitUntil(
            clients.openWindow('/')
        );
    }
});

// Синхронизация в фоне
self.addEventListener('sync', event => {
    if (event.tag === 'background-sync') {
        event.waitUntil(doBackgroundSync());
    }
});

async function doBackgroundSync() {
    // Здесь можно добавить логику синхронизации данных
    console.log('[SW] Background sync triggered');
}

// Обработка сообщений от клиента
self.addEventListener('message', event => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});

// Очистка старых кэшей
async function cleanupOldCaches() {
    const cacheNames = await caches.keys();
    const currentCaches = [STATIC_CACHE, DYNAMIC_CACHE];
    
    return Promise.all(
        cacheNames.map(cacheName => {
            if (!currentCaches.includes(cacheName)) {
                console.log('[SW] Deleting old cache:', cacheName);
                return caches.delete(cacheName);
            }
        })
    );
}
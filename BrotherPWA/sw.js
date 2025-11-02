// Service Worker for Brother PT Label Generator PWA
// Enables offline functionality and caching

const CACHE_NAME = 'brother-pt-pwa-v1.0.0';
const API_CACHE_NAME = 'brother-pt-api-v1.0.0';

// Files to cache for offline functionality
const STATIC_ASSETS = [
    '/',
    '/index.html',
    '/styles.css',
    '/app.js',
    '/manifest.json',
    '/icon-192.png',
    '/icon-512.png'
];

// API endpoints to cache (for offline status)
const API_ENDPOINTS = [
    '/status'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
    console.log('⚙️ Service Worker: Installing...');
    
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('📦 Service Worker: Caching static assets');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => {
                console.log('✅ Service Worker: Installation complete');
                return self.skipWaiting();
            })
            .catch((error) => {
                console.error('❌ Service Worker: Installation failed', error);
            })
    );
});

// Activate event - cleanup old caches
self.addEventListener('activate', (event) => {
    console.log('🔄 Service Worker: Activating...');
    
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => {
                        if (cacheName !== CACHE_NAME && cacheName !== API_CACHE_NAME) {
                            console.log('🗑️ Service Worker: Deleting old cache', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('✅ Service Worker: Activation complete');
                return self.clients.claim();
            })
    );
});

// Fetch event - serve cached content when offline
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Handle different types of requests
    if (request.method === 'GET') {
        
        // Static assets - Cache First strategy
        if (STATIC_ASSETS.some(asset => url.pathname === asset || url.pathname.endsWith(asset))) {
            event.respondWith(
                caches.match(request)
                    .then((cachedResponse) => {
                        if (cachedResponse) {
                            console.log('📂 Serving from cache:', url.pathname);
                            return cachedResponse;
                        }
                        
                        return fetch(request)
                            .then((response) => {
                                // Cache successful responses
                                if (response.status === 200) {
                                    const responseClone = response.clone();
                                    caches.open(CACHE_NAME)
                                        .then((cache) => {
                                            cache.put(request, responseClone);
                                        });
                                }
                                return response;
                            });
                    })
                    .catch(() => {
                        // Offline fallback for HTML pages
                        if (request.headers.get('accept').includes('text/html')) {
                            return caches.match('/index.html');
                        }
                    })
            );
            return;
        }
        
        // API Status endpoint - Network First with cache fallback
        if (url.pathname === '/status') {
            event.respondWith(
                fetch(request)
                    .then((response) => {
                        if (response.status === 200) {
                            const responseClone = response.clone();
                            caches.open(API_CACHE_NAME)
                                .then((cache) => {
                                    cache.put(request, responseClone);
                                });
                        }
                        return response;
                    })
                    .catch(() => {
                        console.log('📡 API offline, serving cached status');
                        return caches.match(request)
                            .then((cachedResponse) => {
                                if (cachedResponse) {
                                    return cachedResponse;
                                }
                                // Return offline status if no cached data
                                return new Response(JSON.stringify({
                                    printer_ready: false,
                                    tape_width_mm: 0,
                                    print_height_px: 0,
                                    container_id: 'offline',
                                    timestamp: new Date().toISOString(),
                                    offline: true
                                }), {
                                    headers: { 'Content-Type': 'application/json' },
                                    status: 200
                                });
                            });
                    })
            );
            return;
        }
    }
    
    // POST requests (print jobs) - Network Only with offline detection
    if (request.method === 'POST' && url.pathname.startsWith('/print/')) {
        event.respondWith(
            fetch(request)
                .catch((error) => {
                    console.error('🚫 Print job failed - offline:', error);
                    
                    // Return user-friendly offline error
                    return new Response(JSON.stringify({
                        success: false,
                        message: 'Druckauftrag fehlgeschlagen - keine Verbindung zum Drucker. Bitte prüfen Sie Ihre Internetverbindung und den Drucker-Status.',
                        offline: true
                    }), {
                        headers: { 'Content-Type': 'application/json' },
                        status: 503
                    });
                })
        );
        return;
    }
    
    // Default: Network First for everything else
    event.respondWith(
        fetch(request)
            .catch(() => {
                return caches.match(request);
            })
    );
});

// Background Sync for failed print jobs (future feature)
self.addEventListener('sync', (event) => {
    console.log('🔄 Background Sync:', event.tag);
    
    if (event.tag === 'retry-print-jobs') {
        event.waitUntil(
            // Future: Retry failed print jobs when back online
            retryFailedPrintJobs()
        );
    }
});

// Handle failed print jobs (placeholder for future enhancement)
async function retryFailedPrintJobs() {
    console.log('🔁 Retrying failed print jobs...');
    
    // Future implementation:
    // - Get failed jobs from IndexedDB
    // - Retry each job
    // - Update UI with results
    
    return Promise.resolve();
}

// Push notifications (future feature)
self.addEventListener('push', (event) => {
    if (!event.data) return;
    
    const data = event.data.json();
    
    const options = {
        body: data.body || 'Drucker-Status Update',
        icon: '/icon-192.png',
        badge: '/icon-192.png',
        tag: 'printer-status',
        requireInteraction: false,
        data: data
    };
    
    event.waitUntil(
        self.registration.showNotification(data.title || 'Brother PT Drucker', options)
    );
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    
    event.waitUntil(
        clients.openWindow('/')
    );
});

console.log('✅ Service Worker loaded successfully');
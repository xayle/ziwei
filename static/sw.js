/**
 * Service Worker - 离线支持和缓存管理
 * 缓存策略：
 * - 静态资源（HTML/CSS/JS）：缓存优先
 * - API请求：网络优先，失败则从缓存恢复
 */

const CACHE_VERSION = 'bazi-v8.0';
const RUNTIME_CACHE = 'bazi-runtime-v8.0';

const STATIC_ASSETS = [
  '/static/sw.js'
]; // 不缓存 manifest/HTML，避免旧 CSP 头被复用

// 安装阶段：缓存基础资源
self.addEventListener('install', event => {
  console.log('[SW] Installing...');
  event.waitUntil(
    caches.open(CACHE_VERSION).then(cache => {
      console.log('[SW] Caching static assets');
      return cache.addAll(STATIC_ASSETS).catch(err => {
        console.warn('[SW] Some assets failed to cache:', err);
      });
    })
  );
  self.skipWaiting();
});

// 激活阶段：清理旧缓存
self.addEventListener('activate', event => {
  console.log('[SW] Activating...');
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_VERSION && cacheName !== RUNTIME_CACHE) {
            console.log('[SW] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// 网络请求处理策略
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // 仅处理同源HTTP/HTTPS请求
  if (!url.protocol.startsWith('http')) {
    return;
  }

  // 关键修复：跨域请求（如 CDN）不走 SW 缓存逻辑，避免返回无效 Response
  if (url.origin !== self.location.origin) {
    return;
  }

  // 根路径和 HTML 导航请求：始终走网络，避免复用旧 CSP 头
  const accept = request.headers.get('accept') || '';
  const isRootPath = url.pathname === '/' || url.pathname === '/dashboard' || url.pathname === '/verify';
  if (request.mode === 'navigate' || accept.includes('text/html') || isRootPath) {
    // 强制绕过 HTTP 缓存以获取最新 CSP/安全头
    event.respondWith(fetch(request, { cache: 'reload' }));
    return;
  }

  // API请求：网络优先，失败则尝试缓存
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request)
        .then(response => {
          if (!response || response.status !== 200) {
            return response;
          }
          // 克隆响应并缓存
          if (request.method === 'GET') {
            const responseClone = response.clone();
            caches.open(RUNTIME_CACHE).then(cache => {
              cache.put(request, responseClone);
            });
          }
          return response;
        })
        .catch(() => {
          // 网络失败，尝试从缓存恢复
          return caches.match(request).then(cached => {
            if (cached) {
              console.log('[SW] API from cache:', request.url);
              return cached;
            }
            // 缓存也无，返回离线提示
            return new Response(
              JSON.stringify({
                error: 'offline',
                message: '网络离线，请检查连接'
              }),
              {
                status: 503,
                headers: { 'Content-Type': 'application/json' }
              }
            );
          });
        })
    );
    return;
  }

  // 静态资源：缓存优先（但 manifest/HTML 强制走网络，避免旧 CSP）
  if (url.pathname.startsWith('/static/')) {
    const isHtml = url.pathname.endsWith('.html');
    const isManifest = url.pathname.endsWith('/manifest.json') || url.pathname === '/static/manifest.json';
    if (isHtml || isManifest) {
      // HTML / manifest 必须绕过缓存以避免复用旧 CSP 头
      event.respondWith(fetch(request, { cache: 'reload' }));
      return;
    }
    event.respondWith(
      caches.match(request).then(cached => {
        if (cached) {
          console.log('[SW] Static from cache:', request.url);
          return cached;
        }
        return fetch(request).then(response => {
          if (!response || response.status !== 200 || response.type === 'error') {
            return response;
          }
          const responseClone = response.clone();
          caches.open(CACHE_VERSION).then(cache => {
            cache.put(request, responseClone);
          });
          return response;
        });
      })
    );
    return;
  }

  // 其他请求：网络优先
  event.respondWith(
    fetch(request)
      .then(response => {
        if (!response || response.status !== 200) {
          return response;
        }
        const responseClone = response.clone();
        caches.open(RUNTIME_CACHE).then(cache => {
          cache.put(request, responseClone);
        });
        return response;
      })
      .catch(() => {
        return caches.match(request).then(cached => {
          if (cached) return cached;
          return new Response('offline', { status: 503, statusText: 'Offline' });
        });
      })
  );
});

// 消息处理：清理缓存命令
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  if (event.data && event.data.type === 'CLEAR_CACHE') {
    caches.delete(RUNTIME_CACHE).then(() => {
      console.log('[SW] Runtime cache cleared');
    });
  }
});

console.log('[SW] Service Worker loaded');

const CACHE_VERSION = 'happynest-tour-v2';
const TILE_CACHE = 'happynest-tour-v2-tiles';
const PRE_CACHE = [
  'vendor/pannellum.js',
  'vendor/pannellum.css',
  'logo.webp',
  'favicon.ico'
];
const MAX_TILE_CACHE_BYTES = 40 * 1024 * 1024;

self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_VERSION).then(function(cache) {
      return cache.addAll(PRE_CACHE);
    }).then(function() {
      return self.skipWaiting();
    })
  );
});

self.addEventListener('activate', function(event) {
  event.waitUntil(
    caches.keys().then(function(names) {
      return Promise.all(
        names.filter(function(n) {
          return n !== CACHE_VERSION && n !== TILE_CACHE;
        }).map(function(n) { return caches.delete(n); })
      );
    }).then(function() {
      return self.clients.claim();
    })
  );
});

function isHTMLOrJSON(url) {
  var p = url.pathname;
  if (p === '/' || p.endsWith('.html') || p.endsWith('.json') || p.endsWith('/sw.js') || p === '/sw.js') return true;
  var dest = url.search; // unused
  return false;
}

function isTileOrAsset(url) {
  var p = url.pathname;
  return p.startsWith('/assets/') || p.startsWith('/vendor/') ||
    p.endsWith('.webp') || p.endsWith('.jpg') || p.endsWith('.png') ||
    p.endsWith('.js') || p.endsWith('.css') || p.endsWith('.ico');
}

function trimTileCache() {
  return caches.open(TILE_CACHE).then(function(cache) {
    return cache.keys().then(function(keys) {
      return Promise.all(keys.map(function(req) {
        return cache.match(req).then(function(res) {
          if (!res) return {req: req, size: 0, date: 0};
          var len = parseInt(res.headers.get('content-length') || '0', 10);
          var date = Date.parse(res.headers.get('date') || '') || 0;
          return {req: req, size: len, date: date};
        });
      })).then(function(entries) {
        var total = entries.reduce(function(s, e) { return s + (e.size || 0); }, 0);
        if (total <= MAX_TILE_CACHE_BYTES) return;
        entries.sort(function(a, b) { return a.date - b.date; });
        var i = 0;
        var chain = Promise.resolve();
        while (total > MAX_TILE_CACHE_BYTES && i < entries.length) {
          total -= entries[i].size || 0;
          (function(req) {
            chain = chain.then(function() { return cache.delete(req); });
          })(entries[i].req);
          i++;
        }
        return chain;
      });
    });
  });
}

self.addEventListener('fetch', function(event) {
  if (event.request.method !== 'GET') return;
  var url;
  try { url = new URL(event.request.url); } catch (e) { return; }
  if (url.origin !== self.location.origin) return;

  if (isHTMLOrJSON(url)) {
    event.respondWith(
      fetch(event.request).then(function(response) {
        if (response && response.ok) {
          var clone = response.clone();
          caches.open(CACHE_VERSION).then(function(cache) { cache.put(event.request, clone); });
        }
        return response;
      }).catch(function() {
        return caches.match(event.request).then(function(cached) {
          return cached || caches.match('/') || caches.match('/index.html');
        });
      })
    );
    return;
  }

  if (isTileOrAsset(url)) {
    event.respondWith(
      caches.match(event.request).then(function(cached) {
        if (cached) return cached;
        return fetch(event.request).then(function(response) {
          if (response && response.status === 200 && (response.type === 'basic' || response.type === 'cors')) {
            var clone = response.clone();
            caches.open(TILE_CACHE).then(function(cache) {
              return cache.put(event.request, clone).then(trimTileCache);
            });
          }
          return response;
        });
      })
    );
  }
});

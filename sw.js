const CACHE_NAME = "yapaycin-mac-analiz-v42";

const FILES_TO_CACHE = ["./","./index.html","./manifest.json","./icon.png"];

self.addEventListener("install", event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(FILES_TO_CACHE)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", event => {
  if (event.request.method !== "GET") return;
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;

  if (url.pathname.endsWith("/data.json")) {
    const cachePromise = caches.open(CACHE_NAME);
    const baseRequest = new Request(url.origin + url.pathname);
    if (url.searchParams.has("v")) {
      event.respondWith((async () => {
        const cache = await cachePromise;
        try {
          const fresh = await fetch(event.request);
          if (fresh.ok) await cache.put(baseRequest, fresh.clone());
          return fresh;
        } catch (e) {
          return (await cache.match(baseRequest)) || Response.error();
        }
      })());
      return;
    }
    const refreshPromise = cachePromise.then(cache =>
      fetch(baseRequest).then(response => {
        if (response.ok) return cache.put(baseRequest, response.clone()).then(() => response);
        return response;
      }).catch(() => null)
    );
    event.waitUntil(refreshPromise);
    event.respondWith(cachePromise.then(cache => cache.match(baseRequest)).then(cached =>
      cached || refreshPromise.then(fresh => fresh || Response.error())
    ));
    return;
  }

  event.respondWith((async () => {
    const cache = await caches.open(CACHE_NAME);
    const cached = await cache.match(event.request);
    if (cached) return cached;
    try {
      const response = await fetch(event.request);
      if (response.ok && /\.(html|json|png|css|js)$/.test(url.pathname)) cache.put(event.request, response.clone());
      return response;
    } catch (e) { return Response.error(); }
  })());
});

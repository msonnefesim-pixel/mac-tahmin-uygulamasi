const CACHE_NAME = "yapaycin-mac-analiz-v177";

const FILES_TO_CACHE = ["./","./index.html","./manifest.json","./icon.svg","./icon-192-pal.png","./icon-512-pal.png"];

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

  if (event.request.mode === "navigate") {
    const cachePromise = caches.open(CACHE_NAME);
    const refreshPromise = cachePromise.then(cache =>
      fetch(event.request, { cache: "no-store" }).then(response => {
        if (response.ok) return cache.put(event.request, response.clone()).then(() => response);
        return response;
      }).catch(() => null)
    );
    // Ekrani once onbellekten ac; agdaki yeni surum arka planda guncellensin.
    event.waitUntil(refreshPromise.then(() => {}));
    event.respondWith(cachePromise.then(cache =>
      cache.match(event.request).then(cached =>
        cached || refreshPromise.then(fresh => fresh || cache.match("./").then(root => root || Response.error()))
      )
    ));
    return;
  }

  if (url.pathname.endsWith("/spor-toto.json")) {
    event.respondWith(fetch(event.request, { cache: "no-store" }).then(async response => {
      if (response.ok) {
        const cache = await caches.open(CACHE_NAME);
        await cache.put(new Request(url.origin + url.pathname), response.clone());
      }
      return response;
    }).catch(async () => {
      const cache = await caches.open(CACHE_NAME);
      return (await cache.match(new Request(url.origin + url.pathname))) || Response.error();
    }));
    return;
  }

  if (url.pathname.endsWith("/iddaa.json")) {
    event.respondWith(fetch(event.request, { cache: "no-store" }).then(async response => {
      if (response.ok) {
        const cache = await caches.open(CACHE_NAME);
        await cache.put(new Request(url.origin + url.pathname), response.clone());
      }
      return response;
    }).catch(async () => {
      const cache = await caches.open(CACHE_NAME);
      return (await cache.match(new Request(url.origin + url.pathname))) || Response.error();
    }));
    return;
  }

  if (url.pathname.endsWith("/live.json")) {
    event.respondWith(fetch(event.request, { cache: "no-store" }).catch(async () => {
      const cache = await caches.open(CACHE_NAME);
      return (await cache.match(event.request)) || (await cache.match(new Request(url.origin + url.pathname))) || Response.error();
    }));
    return;
  }

  if (url.pathname.endsWith("/data.json")) {
    const cachePromise = caches.open(CACHE_NAME);
    const baseRequest = new Request(url.origin + url.pathname);
    if (url.searchParams.has("v")) {
      event.respondWith((async () => {
        const cache = await cachePromise;
        try {
          const fresh = await fetch(event.request, { cache: "no-store" });
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
      if (response.ok && /\.(html|json|png|css|js|svg)$/.test(url.pathname)) cache.put(event.request, response.clone());
      return response;
    } catch (e) { return Response.error(); }
  })());
});

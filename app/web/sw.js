const SHELL_VERSION = "v7";
const CACHE_NAME = "blackhole-shell-" + SHELL_VERSION;
const SHELL_INDEX = "/index.html?v=" + SHELL_VERSION;
const SHELL_ASSETS = [
  "/",
  SHELL_INDEX,
  "/styles.css?v=" + SHELL_VERSION,
  "/app.js?v=" + SHELL_VERSION,
  "/manifest.webmanifest?v=" + SHELL_VERSION,
  "/icons/icon.svg?v=" + SHELL_VERSION,
  "/icons/icon-maskable.svg?v=" + SHELL_VERSION
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL_ASSETS)));
  self.skipWaiting();
});

self.addEventListener("message", (event) => {
  if (event.data && event.data.type === "SKIP_WAITING") self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))))
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== "GET" || url.origin !== self.location.origin || url.pathname.startsWith("/api/")) return;
  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request).then((response) => {
        const copy = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(SHELL_INDEX, copy)).catch(() => {});
        return response;
      }).catch(() => caches.match(SHELL_INDEX).then((cached) => cached || caches.match("/")))
    );
    return;
  }
  event.respondWith(caches.match(request).then((cached) => cached || fetch(request)));
});

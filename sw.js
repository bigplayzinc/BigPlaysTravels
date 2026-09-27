// Offline support: keeps the app itself available without signal.
// The plan's offline copy lives in localStorage (see index.html); GitHub and Google Maps requests are never cached here.
const CACHE = "njr-v1";
const SHELL = ["./", "./index.html", "./manifest.webmanifest", "./icons/icon-192.png", "./icons/icon-512.png", "./icons/apple-touch-icon.png"];
const STATIC_HOSTS = /^(fonts\.googleapis\.com|fonts\.gstatic\.com|cdn\.jsdelivr\.net)$/;

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});

const put = (req, res) => { if (res.ok) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(req, copy)); } return res; };

// App files: network first so a new version shows up straight away; the cached copy if the network fails or stalls.
function networkFirst(req) {
  const fallback = () => caches.match(req, { ignoreSearch: true }).then(m => m || (req.mode === "navigate" ? caches.match("./index.html") : undefined));
  return new Promise(resolve => {
    let done = false;
    const finish = r => { if (!done && r) { done = true; resolve(r); } };
    const timer = setTimeout(() => fallback().then(finish), 4000);
    fetch(req).then(res => { clearTimeout(timer); finish(put(req, res)); })
      .catch(() => { clearTimeout(timer); fallback().then(m => { finish(m); if (!done) { done = true; resolve(Response.error()); } }); });
  });
}

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin === location.origin) { e.respondWith(networkFirst(req)); return; }
  if (STATIC_HOSTS.test(url.hostname)) e.respondWith(caches.match(req).then(m => m || fetch(req).then(res => put(req, res))));
  // everything else (GitHub API, Google Maps) goes straight to the network
});
